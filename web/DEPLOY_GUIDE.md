# CV Pilot Web UI — Deploy Guide
**From zero to live in ~15 minutes.**

---

## What you'll have after this

A password-protected web app at a URL like:
```
https://your-app.streamlit.app
```
Your sales team pastes a JD → clicks Generate → downloads the aligned CV.
All CVs are stored in your Google Drive. Zero ongoing cost.

---

## Step 1 — Google Cloud Setup (~8 min)

### 1a. Create a Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Click **Select a project** → **New Project**
3. Name it: `cv-pilot` → Click **Create**

### 1b. Enable Google Drive API

1. In the left menu: **APIs & Services** → **Library**
2. Search: `Google Drive API`
3. Click it → Click **Enable**

### 1c. Create a Service Account

1. Left menu: **IAM & Admin** → **Service Accounts**
2. Click **Create Service Account**
3. Name: `cv-pilot-service` → Click **Create and Continue**
4. Role: skip (click **Continue**) → Click **Done**

### 1d. Download the JSON Key

1. Click on your new service account (`cv-pilot-service@...`)
2. Tab: **Keys** → **Add Key** → **Create new key**
3. Select **JSON** → Click **Create**
4. A `.json` file downloads — **keep this safe, you'll need it shortly**

### 1e. Share your Google Drive folder with the service account

1. Open **Google Drive** in your browser
2. Create a folder named exactly: **`CV Pilot`**
3. Right-click the folder → **Share**
4. Paste the service account email (looks like: `cv-pilot-service@cv-pilot-123.iam.gserviceaccount.com`)
5. Give it **Editor** access → Click **Send**

### 1f. Upload your base CVs

1. Open the `CV Pilot` folder in Drive
2. Create a subfolder named: **`base_cvs`**
3. Upload all your 8+ DOCX CVs into `base_cvs/`

---

## Step 2 — GitHub Setup (~3 min)

1. Go to https://github.com and create a **new public repository**
   - Name: `cv-pilot-ui`
2. Upload all files from this `cv_ui/` folder to the repository
   - Drag and drop files in the GitHub web interface, or use git
   - **Important: do NOT upload `.streamlit/secrets_template.toml` as `secrets.toml`**
   - The `.streamlit/config.toml` is fine to upload

---

## Step 3 — Streamlit Cloud Deployment (~4 min)

1. Go to https://share.streamlit.io
2. Sign in with your GitHub account
3. Click **New app**
4. Fill in:
   - **Repository**: `your-username/cv-pilot-ui`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. Click **Advanced settings** → **Secrets**
6. Paste the contents of `.streamlit/secrets_template.toml`, filling in your real values:

```toml
ANTHROPIC_API_KEY = "sk-ant-api03-..."
APP_PASSWORD = "your-team-password"
DRIVE_FOLDER_NAME = "CV Pilot"
GOOGLE_CREDENTIALS_JSON = """
{ ... paste your full service account JSON here ... }
"""
```

7. Click **Save** → Click **Deploy**

Your app will be live in about 2-3 minutes.

---

## Step 4 — Share with Your Team

Send your team:
1. The app URL (e.g. `https://cv-pilot-sashi.streamlit.app`)
2. The password you set in `APP_PASSWORD`

That's it — they paste a JD, click Generate, download the CV.

---

## Cost Summary

| Service | Cost |
|---|---|
| Streamlit Community Cloud | Free |
| Google Drive API | Free (well within limits) |
| Google Cloud (service account) | Free |
| Anthropic API | ~$0.02–$0.05 per CV generated |

**Typical monthly cost: < $5** for a small team generating 50–100 CVs.

---

## Troubleshooting

**"ANTHROPIC_API_KEY not found"**
→ Check Streamlit Secrets — make sure the key name matches exactly

**"Google Drive authentication failed"**
→ Make sure the JSON is valid — paste it into https://jsonlint.com/ to check
→ Make sure the Drive folder is shared with the service account email

**"No base CVs found"**
→ Check the `base_cvs/` subfolder in your `CV Pilot` Drive folder
→ Make sure files are `.docx` format

**App crashes on startup**
→ Check the Streamlit Cloud logs (three dots next to app → Logs)

---

## File Structure

```
cv_ui/
├── app.py                      ← Main Streamlit app (UI + pipeline)
├── cv_engine.py                ← Claude API logic (parse, score, enhance)
├── drive_client.py             ← Google Drive integration
├── requirements.txt            ← Python dependencies
├── .gitignore                  ← Protects secrets from git
└── .streamlit/
    ├── config.toml             ← App theme + settings
    └── secrets_template.toml  ← Template for Streamlit secrets (do not rename to secrets.toml)
```
