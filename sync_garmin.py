import base64
import json
import os
from datetime import date
import requests
from garminconnect import Garmin


def main():
    # 1. Fetch and decode token string from GitHub Secret
    token_b64 = os.environ["GARMIN_TOKENS_BASE64"]
    token_json = base64.b64decode(token_b64).decode("utf-8")

    # 2. Reconstruct ~/.garminconnect/garmin_tokens.json
    token_dir = os.path.expanduser("~/.garminconnect")
    os.makedirs(token_dir, exist_ok=True)
    token_file = os.path.join(token_dir, "garmin_tokens.json")

    with open(token_file, "w", encoding="utf-8") as f:
        f.write(token_json)

    # 3. Authenticate using the token store path
    garmin = Garmin()
    garmin.login(token_dir)

    # 4. Pull training status & load metrics for today
    today_str = date.today().isoformat()
    status_data = garmin.get_training_status(today_str)

    # 5. Extract status values and VO2 Max from nested JSON
    device_data = {}
    vo2_max_precise = None

    if isinstance(status_data, dict):
        most_recent_status = status_data.get("mostRecentTrainingStatus", {})
        if isinstance(most_recent_status, dict):
            train_dict = most_recent_status.get("latestTrainingStatusData", {})
            if isinstance(train_dict, dict) and train_dict:
                device_data = list(train_dict.values())[0]

        most_recent_vo2 = status_data.get("mostRecentVO2Max", {})
        if isinstance(most_recent_vo2, dict):
            generic_vo2 = most_recent_vo2.get("generic", {})
            if isinstance(generic_vo2, dict):
                vo2_max_precise = generic_vo2.get("vo2MaxPreciseValue")

    acute_dto = (
        device_data.get("acuteTrainingLoadDTO", {})
        if isinstance(device_data, dict)
        else {}
    )

    raw_phrase = device_data.get("trainingStatusFeedbackPhrase", "UNKNOWN")
    clean_phrase = (
        raw_phrase.split("_")[0] if isinstance(raw_phrase, str) else "UNKNOWN"
    )
    formatted_status = clean_phrase.capitalize()

    # 6. Pull Training Readiness and recovery metrics
    readiness_score = None
    feedback_short = None
    level = None
    recovery_time_hours = None
    recovery_time_factor_percent = None

    try:
        readiness_data = garmin.get_training_readiness(today_str)

        if isinstance(readiness_data, list) and len(readiness_data) > 0:
            sorted_data = sorted(
                readiness_data,
                key=lambda x: str(
                    x.get("timestampGMT")
                    or x.get("timestamp")
                    or x.get("calendarDate")
                    or ""
                ),
            )
            readiness_obj = sorted_data[-1]
        elif isinstance(readiness_data, dict):
            readiness_obj = readiness_data
        else:
            readiness_obj = {}

        readiness_score = readiness_obj.get("score")
        level = readiness_obj.get("level")
        recovery_time_factor_percent = readiness_obj.get("recoveryTimeFactorPercent")

        # Format feedbackShort ("RESTED_AND_READY" -> "Rested and ready")
        raw_feedback = readiness_obj.get("feedbackShort")
        if raw_feedback and isinstance(raw_feedback, str):
            feedback_short = raw_feedback.replace("_", " ").lower().capitalize()

        # Convert recoveryTime from minutes to rounded hours
        raw_rec_time = readiness_obj.get("recoveryTime")
        if raw_rec_time is not None:
            recovery_time_hours = round(raw_rec_time / 60)

    except Exception as e:
        print(f"Warning: Could not fetch training readiness: {e}")

    # Build clean payload
    payload = {
        "acuteLoad": acute_dto.get("dailyTrainingLoadAcute", 0),
        "minTrainingLoad": acute_dto.get("minTrainingLoadChronic", 0),
        "maxTrainingLoad": acute_dto.get("maxTrainingLoadChronic", 0),
        "status": formatted_status,
        "trainingReadiness": readiness_score,
        "feedbackShort": feedback_short,
        "level": level,
        "recoveryTime": recovery_time_hours,
        "recoveryTimeFactorPercent": recovery_time_factor_percent,
        "vo2Max": vo2_max_precise,
        "lastUpdated": device_data.get("calendarDate", today_str),
    }

    print(f"Extracted payload: {payload}")

    # 7. Update the GitHub Gist
    gist_id = os.environ["GIST_ID"]
    gh_pat = os.environ["GH_PAT"]

    headers = {
        "Authorization": f"token {gh_pat}",
        "Accept": "application/vnd.github.v3+json",
    }

    body = {
        "files": {
            "garmin_data.json": {"content": json.dumps(payload, indent=2)}
        }
    }

    res = requests.patch(
        f"https://api.github.com/gists/{gist_id}", headers=headers, json=body
    )
    if res.status_code == 200:
        print("Successfully updated Gist with Garmin training load data!")
    else:
        print(f"Failed to update Gist: {res.status_code} - {res.text}")


if __name__ == "__main__":
    main()
