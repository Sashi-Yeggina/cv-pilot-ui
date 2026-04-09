# CV Pilot 🚀

**AI-powered CV alignment engine** — built for Sashi Kiran Yeggina and sales team.

Drop a job description → AI picks your best matching base CV → rewrites title, summary, skills, and all bullet points to match the JD → saves with smart tags → syncs to GitHub so the whole team has it.

---

## What it does

| Feature | Detail |
|---|---|
| **Auto-pick best CV** | Scores all your 8+ CVs against the JD, picks the highest match |
| **Rewrite title + summary** | Updates role title and professional summary to mirror the JD |
| **Enhance all bullet points** | Rewrites job bullets to highlight JD-relevant experience — natural tone, never fabricated |
| **ATS optimised** | Mirrors JD keywords naturally throughout the CV |
| **Smart save + tagging** | Saves with structured filename; tags by role, cloud platform, skills |
| **Reuse library** | Before rebuilding, checks if a similar aligned CV already exists (≥75% match = reuse it) |
| **GitHub cloud sync** | Every saved CV auto-pushes to your private GitHub repo so the sales team can pull it |

---

## Quick Start (First Time)

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your API key

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

Get your API key at: https://console.anthropic.com/

### 3. Add your base CVs

```bash
mkdir my_cvs
# Copy all your 8+ DOCX CVs into my_cvs/
```

### 4. Run it

```bash
# Interactive mode — paste JD when prompted
python cv_pilot.py

# From a JD file
python cv_pilot.py --jd amazon_jd.txt

# With company name for better filename
python cv_pilot.py --jd amazon_jd.txt --company Amazon
```

Your aligned CV will appear in `aligned_cvs/` with a name like:
```
AWS_Cloud_Engineer_AWS_Amazon_20260406.docx
```

---

## GitHub Setup (for team sharing)

### One-time setup (you — the admin)

1. Create a GitHub Personal Access Token:
   - Go to: GitHub → Settings → Developer Settings → Personal Access Tokens → Classic
   - Scopes needed: `repo` (full control)

2. Add to `.env`:
   ```
   GITHUB_TOKEN=ghp_your_token_here
   GITHUB_REPO=your-username/cv-library
   ```

3. Create the repo:
   ```bash
   python cv_sync.py setup --name cv-library
   ```

4. Upload your 8+ base CVs to the repo:
   ```bash
   python upload_base_cvs.py
   ```

After this, **every CV you align auto-pushes to GitHub** — no extra steps.

### For your sales team (each recruiter, once)

1. Get a copy of this `cv_pilot` folder (share via zip, USB, or clone from GitHub)
2. Add their own `.env` with the shared `GITHUB_TOKEN` and `GITHUB_REPO`
3. Run:
   ```bash
   pip install -r requirements.txt
   python team_pull.py
   ```
   This pulls all base CVs + aligned CVs + the index in one shot.

4. They're ready to use `cv_pilot.py` normally.

---

## All Commands

```bash
# ── Align a new CV ─────────────────────────────────────────────
python cv_pilot.py                         # interactive — paste JD
python cv_pilot.py --jd job.txt            # JD from file
python cv_pilot.py --jd job.txt --company Amazon  # with company name
python cv_pilot.py --jd job.txt --auto     # no prompts (batch mode)

# ── Browse your library ────────────────────────────────────────
python cv_pilot.py --list                  # show all saved CVs
python cv_pilot.py --reuse "AWS Cloud"     # find CVs matching a role

# ── GitHub sync ────────────────────────────────────────────────
python cv_sync.py status                   # check GitHub connection
python cv_sync.py list                     # list CVs in GitHub repo
python cv_sync.py pull                     # pull all CVs from GitHub
python cv_sync.py push-index               # manually push index
python cv_sync.py push-base my_cvs/cv.docx # push a base CV

# ── Team setup ─────────────────────────────────────────────────
python team_pull.py                        # pull everything from GitHub (team members)
python upload_base_cvs.py                  # upload base CVs to GitHub (admin only)
```

---

## Role types supported

The tool recognises these role categories automatically from the JD:
- AWS Cloud Engineer
- Cloud Solutions Architect
- DevOps Engineer
- SRE (Site Reliability Engineer)
- AIOps Engineer
- Azure DevOps Engineer
- Cloud Network Engineer
- Platform Engineer

---

## Folder structure

```
cv_pilot/
├── cv_pilot.py            ← Main CLI script
├── cv_sync.py             ← GitHub sync module
├── team_pull.py           ← One-command team setup
├── upload_base_cvs.py     ← Upload base CVs to GitHub
├── requirements.txt       ← Python dependencies
├── .env.example           ← Config template (copy to .env)
├── .env                   ← Your actual config (never commit this!)
├── .gitignore             ← Protects .env and local folders
│
├── my_cvs/                ← Your 8+ base DOCX CVs (source of truth)
├── aligned_cvs/           ← Aligned CVs saved here
└── cv_index.json          ← Smart tagging library (auto-created)
```

---

## CV Naming Convention

Saved CVs use this pattern:
```
{Role_Title}_{Cloud}_{Company}_{YYYYMMDD}.docx

Examples:
  AWS_Cloud_Engineer_AWS_Amazon_20260406.docx
  DevOps_Engineer_Azure_Microsoft_20260407.docx
  SRE_MultiCloud_Google_20260408.docx
```

---

## Privacy & Security

- Your CV files never leave your machine (except to your private GitHub repo)
- JD text and CV text are sent to the Claude API (Anthropic) for processing — [Anthropic's data policy](https://www.anthropic.com/legal/privacy)
- Your `.env` file is in `.gitignore` and will never be committed
- The GitHub repo is private — only people you invite can access it

---

## Troubleshooting

**"ANTHROPIC_API_KEY not found"**
→ Make sure `.env` exists with your key, or run: `export ANTHROPIC_API_KEY=sk-ant-...`

**"No DOCX files found in my_cvs/"**
→ Create the folder and copy your CVs in: `mkdir my_cvs`

**GitHub push fails**
→ Check your token has `repo` scope and `GITHUB_REPO` matches exactly

**CV looks wrong after enhancement**
→ The DOCX structure varies between CV templates. Open the output and manually verify key sections. The more consistently structured your base CVs are, the better the output.

---

Built with Claude AI (Anthropic) | For Sashi Kiran Yeggina | 2026
