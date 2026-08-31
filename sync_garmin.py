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

    # Pretty-print the raw status_data dictionary to inspect its structure
    print("=== RAW STATUS DATA START ===")
    print(json.dumps(status_data, indent=2, default=str))
    print("=== RAW STATUS DATA END ===")

    latest = {}
    if isinstance(status_data, dict):
        most_recent = status_data.get("mostRecentTrainingStatus", {})
        if isinstance(most_recent, dict):
            train_dict = most_recent.get("latestTrainingStatusData", {})
            if isinstance(train_dict, dict) and train_dict:
                latest = list(train_dict.values())[0]

        if not latest and "latestTrainingStatusData" in status_data:
            train_dict = status_data.get("latestTrainingStatusData", {})
            if isinstance(train_dict, dict) and train_dict:
                latest = list(train_dict.values())[0]

    payload = {
        "acuteLoad": latest.get("acuteLoad", 0),
        "minTrainingLoad": latest.get("minTrainingLoad", 0),
        "maxTrainingLoad": latest.get("maxTrainingLoad", 0),
        "status": latest.get("trainingStatus", "UNKNOWN"),
        "lastUpdated": latest.get("calendarDate")
        or (
            status_data.get("lastUpdated")
            if isinstance(status_data, dict)
            else None
        ),
    }

    print(f"Parsed payload: {payload}")

    # 5. Update the GitHub Gist
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
