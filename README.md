# 🏃 Garmin Connect to KWGT Sync

Automated serverless pipeline to sync advanced Garmin metrics—including **Acute Load**, **Training Load Tunnel (Min/Max)**, **Training Readiness**, **VO2 Max**, and **7-Day Running Distance**—to an interactive **KWGT Android Home Screen Widget** via GitHub Actions and GitHub Gists.

---

## 📌 Features

* **Serverless & Free:** Runs on GitHub Actions scheduled cron (no paid servers or background apps running on your phone).
* **Battery Friendly:** KWGT fetches data over standard HTTPS requests without polling Garmin APIs directly or wearing down your watch/phone battery.
* **Comprehensive Metrics:**
  * **Acute Training Load** + Min/Max Chronic Load Targets
  * **Training Status** (*Productive, Maintaining, Recovery, etc.*)
  * **Training Readiness** score + Qualitative Level & Short Feedback
  * **Recovery Time** (converted to rounded hours)
  * **Precise VO2 Max**
  * **7-Day Cumulative Running Distance** (in km)
* **Auto-Scaling KWGT Bar:** Included widget dynamic scaling logic adjusting to any screen width (`$si(rwidth)$`).

---

## 🏗️ Architecture


```

┌─────────────────┐       ┌──────────────────────┐       ┌──────────────────┐       ┌─────────────────┐
│  Garmin Connect │ ────> │  GitHub Actions      │ ────> │   GitHub Gist    │ ────> │   KWGT Widget   │
│   Cloud API     │       │ (Python Cron Script) │       │ (garmin_data.json│       │ (Android Phone) │
└─────────────────┘       └──────────────────────┘       └──────────────────┘       └─────────────────┘

```

---

## 📋 Prerequisites

1. **Garmin Connect Account**
2. **GitHub Account**
3. **Android Device** with [KWGT Kustom Widget Maker](https://play.google.com/store/apps/details?id=org.kustom.widget) & [KWGT Pro Key](https://play.google.com/store/apps/details?id=org.kustom.widget.pro)

---

## ⚙️ Setup Instructions

### Step 1: Generate Garmin Session Tokens (Locally)

Garmin Connect uses OAuth tokens. Generate your base64-encoded token string locally to store securely in GitHub Secrets.

1. Install `garminconnect` on your computer:
```bash
   pip install garminconnect
```

2. Run a quick python snippet to authenticate and save tokens:
```python
from garminconnect import Garmin

email = input("Garmin Email: ")
password = input("Garmin Password: ")

garmin = Garmin(email, password)
garmin.login()
garmin.garth.dump("~/.garminconnect")
print("Tokens saved to ~/.garminconnect/garmin_tokens.json")
```


3. Base64-encode your `garmin_tokens.json` file:
* **macOS / Linux:**
```bash
base64 -i ~/.garminconnect/garmin_tokens.json | tr -d '\n'
```


* **Windows (PowerShell):**
```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("$HOME\.garminconnect\garmin_tokens.json"))

```




4. Copy the resulting string—you will use it in Step 3.

---

### Step 2: Create GitHub Gist & Personal Access Token (PAT)

1. **Create Target Gist:**
* Go to [gist.github.com](https://gist.github.com/).
* Name the file `garmin_data.json`.
* Add dummy content `{}` and click **Create Secret Gist** (or Public Gist).
* Copy the **Gist ID** from the browser URL:
`https://gist.github.com/USERNAME/`**`a1b2c3d4e5f67890123456789abcdef0`**


2. **Generate PAT:**
* Go to **GitHub Settings** $\rightarrow$ **Developer Settings** $\rightarrow$ **Personal Access Tokens** $\rightarrow$ **Tokens (classic)**.
* Click **Generate new token (classic)**.
* Give it a name (e.g., `Garmin Gist Sync`) and check the **`gist`** scope box.
* Copy the generated token.



---

### Step 3: Configure Repository Secrets

1. Fork or clone this repository.
2. Go to your repository **Settings** $\rightarrow$ **Secrets and variables** $\rightarrow$ **Actions**.
3. Add three **New repository secrets**:

| Secret Name | Value Description |
| --- | --- |
| `GARMIN_TOKENS_BASE64` | The long base64 string copied from Step 1 |
| `GIST_ID` | Your Gist ID string from Step 2 |
| `GH_PAT` | Your Personal Access Token from Step 2 |

4. Go to the **Actions** tab in your repository and manually trigger **Run Garmin Sync** to verify setup.

---

### Step 4: Import and Set Up KWGT Widget

1. Download the exported `.kwgt` file from the `/widget` directory in this repo to your phone.
2. Open **KWGT**, select **Import**, and pick the `.kwgt` file.
3. In the widget editor, go to the **Globals** tab and update the following globals:

| Global Name | Type | Value |
| --- | --- | --- |
| `gisturl` | Text | `https://gist.githubusercontent.com/USERNAME/GIST_ID/raw/garmin_data.json` |
| `trackw` | Text / Formula | `$mu(round, si(rwidth) - 40)$` |

> ⚠️ **Important:** Make sure your Gist URL uses the permanent raw address format (without the commit hash segment between `/raw/` and `/garmin_data.json`).

---

## 📊 Data Payload Structure

The workflow updates `garmin_data.json` in your Gist with this schema:

```json
{
  "acuteLoad": 488,
  "minTrainingLoad": 396.0,
  "maxTrainingLoad": 742.5,
  "status": "Productive",
  "trainingReadiness": 75,
  "feedbackShort": "Rested and ready",
  "level": "High",
  "recoveryTime": 15,
  "recoveryTimeFactorPercent": 77,
  "vo2Max": 51.2,
  "weeklyRunningKm": 34.2,
  "lastUpdated": "2026-08-31"
}

```

---

## 🧮 KWGT Formula Reference

Here are useful formulas to pull data inside KWGT using your `gisturl` global:

* **Training Status:**
```text
$wg(gv(gisturl), json, .status)$

```


* **Training Readiness Score:**
```text
$wg(gv(gisturl), json, .trainingReadiness)$ / 100

```


* **Weekly Distance:**
```text
$wg(gv(gisturl), json, .weeklyRunningKm)$ km

```


* **Dynamic Target Range Width (Highlight Bar):**
```text
$gv(trackw) * (wg(gv(gisturl), json, .maxTrainingLoad) - wg(gv(gisturl), json, .minTrainingLoad)) / (wg(gv(gisturl), json, .maxTrainingLoad) + wg(gv(gisturl), json, .minTrainingLoad))$

```


* **Dynamic Pointer Position (Acute Load Triangle):**
```text
$(gv(trackw) * wg(gv(gisturl), json, .acuteLoad) / (wg(gv(gisturl), json, .maxTrainingLoad) + wg(gv(gisturl), json, .minTrainingLoad))) - 7$

```



---

## 🛡️ Privacy & Security

* **No Credentials in Code:** Passwords and session tokens are strictly maintained inside encrypted GitHub Action Secrets.
* **Public Repo Safe:** You can make your repository public without leaking access credentials. Note that anyone who finds your Raw Gist URL will be able to read your high-level training stats.

---

## 📜 License

MIT License. Feel free to modify and build upon this setup!

```

```
