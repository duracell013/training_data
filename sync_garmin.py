import json
import os
import requests
from garminconnect import Garmin


def main():
    # 1. Fetch token string from GitHub Secret
    token_b64 = os.environ["GARMIN_TOKENS_BASE64"]

    # 2. Authenticate directly using the Base64 string
    garmin = Garmin()
    garmin.login(token_b64)

    # 3. Pull training status & load metrics
    status_data = garmin.get_training_status()
    latest = status_data.get("latestTrainingStatusData", {})

    payload = {
        "acuteLoad": latest.get("acuteLoad", 0),
        "minTrainingLoad": latest.get("minTrainingLoad", 0),
        "maxTrainingLoad": latest.get("maxTrainingLoad", 0),
        "status": latest.get("trainingStatus", "UNKNOWN"),
        "lastUpdated": status_data.get("lastUpdated"),
    }

    # 4. Update the GitHub Gist
    gist_id = os.environ["GIST_ID"]
    gh_pat = os.environ["GH_PAT"]

    headers = {
        "Authorization": f"token {gh_pat}",
        "Accept": "application/vnd.github.v3+json",
    }

    body = {
        "files": {
            "garmin_data.json": {
                "content": json.dumps(payload, indent=2)
            }
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
