"""
CV Pilot — Web UI
Streamlit app for Sashi Kiran's CV generation engine.
Staff paste a JD → Claude picks best CV → enhances it → download DOCX → saves to Drive.
"""

import os, io, json, hashlib, time
import streamlit as st
from datetime import datetime
from pathlib import Path

# ── Page config (must be first Streamlit call) ─────────────────────────────
st.set_page_config(
    page_title="CV Pilot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ── */
[data-testid="stAppViewContainer"] { background: #F7F9FC; }
[data-testid="stSidebar"] { background: #1B2A4A; }
[data-testid="stSidebar"] * { color: #E8EDF5 !important; }
[data-testid="stSidebar"] .stButton button {
    background: #2E5090; border: none; color: white;
    border-radius: 8px; width: 100%;
}

/* ── Cards ── */
.cv-card {
    background: white; border-radius: 14px;
    padding: 24px 28px; margin-bottom: 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    border-left: 4px solid #2E86C1;
}
.cv-card h3 { color: #1B4F72; margin-top: 0; font-size: 1.1rem; }

/* ── Score badge ── */
.score-high { background:#D5F5E3; color:#1E8449; padding:4px 12px;
              border-radius:20px; font-weight:700; font-size:0.95rem; }
.score-mid  { background:#FDEBD0; color:#B7770D; padding:4px 12px;
              border-radius:20px; font-weight:700; font-size:0.95rem; }
.score-low  { background:#FADBD8; color:#922B21; padding:4px 12px;
              border-radius:20px; font-weight:700; font-size:0.95rem; }

/* ── Tags ── */
.tag { background:#EBF5FB; color:#2E86C1; padding:3px 10px;
       border-radius:12px; font-size:0.78rem; margin:2px;
       display:inline-block; }

/* ── Generate button ── */
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #1B4F72, #2E86C1);
    color: white; border: none; border-radius: 10px;
    padding: 14px 36px; font-size: 1.05rem; font-weight: 600;
    width: 100%; box-shadow: 0 4px 14px rgba(46,134,193,0.35);
    transition: all 0.2s ease;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(46,134,193,0.5); transform: translateY(-1px);
}

/* ── Download button ── */
div[data-testid="stDownloadButton"] button {
    background: #1E8449; color: white; border: none;
    border-radius: 10px; padding: 12px 28px;
    font-size: 1rem; font-weight: 600; width: 100%;
}

/* ── Misc ── */
.stTextArea textarea { border-radius: 10px; border: 1.5px solid #AED6F1;
                       font-size: 0.92rem; }
.stTextInput input { border-radius: 8px; }
.step-label { font-size: 0.78rem; font-weight: 700; color: #2E86C1;
              text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
.divider { height:1px; background:#E8EDF5; margin: 24px 0; }
hr { border-color: #E8EDF5; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════

def get_secret(key: str, fallback: str = "") -> str:
    """Read from Streamlit secrets or environment variable."""
    try:
        return st.secrets.get(key, os.environ.get(key, fallback))
    except Exception:
        return os.environ.get(key, fallback)


def check_password() -> bool:
    """Returns True if the user has entered the correct password."""
    correct_hash = hashlib.sha256(
        get_secret("APP_PASSWORD", "cvpilot2024").encode()
    ).hexdigest()

    if st.session_state.get("authenticated"):
        return True

    # ── Login screen ──────────────────────────────────────────────────────
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center; margin-bottom:32px;">
            <div style="font-size:3rem">🚀</div>
            <h1 style="color:#1B4F72; margin:8px 0 4px;">CV Pilot</h1>
            <p style="color:#666; margin:0">Sashi Kiran's AI CV Engine</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            password = st.text_input("Password", type="password",
                                     placeholder="Enter team password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            if hashlib.sha256(password.encode()).hexdigest() == correct_hash:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")
    return False


def score_colour(score: int) -> str:
    if score >= 75: return "score-high"
    if score >= 55: return "score-mid"
    return "score-low"


def render_sidebar(cv_library: list):
    """Render the left sidebar with library stats and saved CVs."""
    with st.sidebar:
        st.markdown("""
        <div style="padding:16px 0 8px; text-align:center;">
            <span style="font-size:1.6rem">🚀</span>
            <div style="font-size:1.1rem; font-weight:700; margin-top:4px;">CV Pilot</div>
            <div style="font-size:0.75rem; opacity:0.6; margin-top:2px;">
                Sashi Kiran's CV Engine
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Stats ──
        total = len(cv_library)
        roles = list(set(e.get("role_category","—") for e in cv_library))
        st.markdown(f"""
        <div style="text-align:center; padding:8px 0 12px;">
            <div style="font-size:2rem; font-weight:700; color:#7EB3E8;">{total}</div>
            <div style="font-size:0.78rem; opacity:0.7;">CVs in library</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔄  Refresh Library", key="refresh_lib"):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")

        # ── Search ──
        search = st.text_input("🔍  Search library", placeholder="e.g. AWS, DevOps…",
                               label_visibility="collapsed")

        filtered = cv_library
        if search:
            kw = search.lower()
            filtered = [e for e in cv_library
                        if kw in e.get("role_type","").lower()
                        or kw in " ".join(e.get("reuse_tags",[])).lower()
                        or kw in e.get("company","").lower()]

        if filtered:
            for entry in sorted(filtered,
                                key=lambda x: x.get("created_date",""), reverse=True)[:20]:
                score = entry.get("ats_score", 0)
                cls   = score_colour(score)
                name  = Path(entry.get("filename","?")).stem
                role  = entry.get("role_type","")[:28]
                date  = entry.get("created_date","")[:10]
                st.markdown(f"""
                <div style="background:#243555; border-radius:8px; padding:10px 12px;
                            margin-bottom:8px; cursor:pointer;">
                    <div style="font-size:0.78rem; font-weight:600; margin-bottom:3px;
                                word-break:break-all;">{name[:36]}</div>
                    <div style="display:flex; justify-content:space-between;
                                align-items:center; margin-top:4px;">
                        <span style="font-size:0.7rem; opacity:0.7;">{role}</span>
                        <span class="{cls}" style="font-size:0.7rem;">{score}/100</span>
                    </div>
                    <div style="font-size:0.68rem; opacity:0.5; margin-top:2px;">{date}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='opacity:0.5; font-size:0.82rem;'>No CVs found</div>",
                        unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
#  Core pipeline (calls cv_engine + drive_client)
# ══════════════════════════════════════════════════════════════════════════

def run_pipeline(jd_text: str, company: str) -> dict:
    """
    Full pipeline: JD → best CV → enhance → DOCX bytes → save to Drive.
    Returns result dict for display.
    """
    from cv_engine import parse_jd, score_cvs, enhance_cv, apply_enhancements
    from drive_client import DriveClient

    api_key = get_secret("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("ANTHROPIC_API_KEY not set in Streamlit secrets.")
        st.stop()

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    drive = DriveClient(
        credentials_json=get_secret("GOOGLE_CREDENTIALS_JSON"),
        folder_name=get_secret("DRIVE_FOLDER_NAME", "CV Pilot"),
    )

    # ── 1. Parse JD ─────────────────────────────────────────────────────
    progress = st.progress(0, text="🔍  Analysing job description...")
    jd = parse_jd(client, jd_text)
    progress.progress(20, text="📂  Loading CVs from Google Drive...")

    # ── 2. Load base CVs from Drive ──────────────────────────────────────
    cv_files = drive.list_base_cvs()
    if not cv_files:
        st.error("No CVs found in your Google Drive `CV Pilot/base_cvs/` folder.")
        st.stop()

    cv_data_list = []
    for i, f in enumerate(cv_files):
        progress.progress(20 + int(30 * i / len(cv_files)),
                          text=f"📄  Reading {f['name']}...")
        text = drive.read_cv_text(f["id"])
        cv_data_list.append({"filename": f["name"], "id": f["id"], "text": text})

    # ── 3. Score CVs ─────────────────────────────────────────────────────
    progress.progress(55, text="🎯  Scoring CVs against the JD...")
    scored = score_cvs(client, cv_data_list, jd)

    # ── 4. Load best CV bytes ─────────────────────────────────────────────
    best      = scored[0]
    best_id   = next(c["id"] for c in cv_data_list if c["filename"] == best["filename"])
    progress.progress(65, text=f"⚡  Enhancing {best['filename']}...")
    cv_bytes  = drive.download_cv(best_id)
    best_text = next(c["text"] for c in cv_data_list if c["filename"] == best["filename"])

    # ── 5. Enhance ────────────────────────────────────────────────────────
    enhancements = enhance_cv(client, best_text, jd)

    # ── 6. Apply to DOCX ──────────────────────────────────────────────────
    progress.progress(80, text="📝  Writing enhanced CV...")
    output_bytes = apply_enhancements(cv_bytes, enhancements)

    # ── 7. Build filename & save to Drive ─────────────────────────────────
    progress.progress(90, text="☁️  Saving to Google Drive...")
    role   = jd["role_title"].replace(" ", "_").replace("/", "-")
    cloud  = jd["cloud_platform"].replace("-", "")
    co     = ("_" + company.replace(" ", "_")) if company else ""
    date   = datetime.now().strftime("%Y%m%d")
    fname  = f"{role}_{cloud}{co}_{date}.docx"

    drive.save_aligned_cv(fname, output_bytes)

    # ── 8. Update index ───────────────────────────────────────────────────
    import uuid
    index_entry = {
        "id": str(uuid.uuid4()),
        "filename": fname,
        "base_cv": best["filename"],
        "role_type": jd["role_title"],
        "role_category": jd["role_category"],
        "cloud_platform": jd["cloud_platform"],
        "company": company,
        "created_date": datetime.now().isoformat(),
        "jd_keywords": jd["ats_keywords"],
        "required_skills": jd["required_skills"],
        "ats_score": best["score"],
        "reuse_tags": list(set(
            [jd["cloud_platform"].lower()]
            + [s.lower() for s in jd["required_skills"][:8]]
            + [jd["role_category"].lower().replace(" ", "_")]
        )),
    }
    drive.update_index(index_entry)

    progress.progress(100, text="✅  Done!")
    time.sleep(0.4)
    progress.empty()

    return {
        "jd": jd,
        "scored": scored,
        "best": best,
        "enhancements": enhancements,
        "output_bytes": output_bytes,
        "filename": fname,
    }


# ══════════════════════════════════════════════════════════════════════════
#  Result display
# ══════════════════════════════════════════════════════════════════════════

def show_results(result: dict):
    jd          = result["jd"]
    scored      = result["scored"]
    best        = result["best"]
    enh         = result["enhancements"]
    out_bytes   = result["output_bytes"]
    fname       = result["filename"]

    # ── JD summary card ───────────────────────────────────────────────────
    st.markdown(f"""
    <div class="cv-card">
        <h3>📋  Job Analysis</h3>
        <div style="display:flex; gap:24px; flex-wrap:wrap;">
            <div>
                <div style="font-size:0.72rem; color:#888; margin-bottom:2px;">ROLE</div>
                <div style="font-weight:700; color:#1B4F72; font-size:1.05rem;">
                    {jd['role_title']}
                </div>
            </div>
            <div>
                <div style="font-size:0.72rem; color:#888; margin-bottom:2px;">PLATFORM</div>
                <div style="font-weight:600;">{jd['cloud_platform']}</div>
            </div>
            <div>
                <div style="font-size:0.72rem; color:#888; margin-bottom:2px;">SENIORITY</div>
                <div style="font-weight:600;">{jd['seniority']}</div>
            </div>
            <div>
                <div style="font-size:0.72rem; color:#888; margin-bottom:2px;">EXPERIENCE</div>
                <div style="font-weight:600;">{jd.get('years_experience','—')}</div>
            </div>
        </div>
        <div style="margin-top:14px;">
            {''.join(f'<span class="tag">{k}</span>' for k in jd['ats_keywords'][:12])}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── CV scores ─────────────────────────────────────────────────────────
    st.markdown('<div class="cv-card"><h3>🎯  CV Match Scores</h3>', unsafe_allow_html=True)
    cols = st.columns(min(len(scored), 4))
    for i, row in enumerate(scored[:4]):
        sc  = row["score"]
        cls = score_colour(sc)
        with cols[i]:
            star = "⭐ " if i == 0 else ""
            st.markdown(f"""
            <div style="background:{'#EBF5FB' if i==0 else '#F7F9FC'};
                        border-radius:10px; padding:14px; text-align:center;
                        border:{'2px solid #2E86C1' if i==0 else '1px solid #E8EDF5'};">
                <div style="font-size:0.72rem; color:#888; margin-bottom:4px;">
                    {star}{'BEST MATCH' if i==0 else f'#{i+1}'}
                </div>
                <div style="font-weight:700; font-size:0.82rem; color:#1B4F72;
                            word-break:break-all; margin-bottom:8px;">
                    {Path(row['filename']).stem[:28]}
                </div>
                <span class="{cls}">{sc}/100</span>
                <div style="font-size:0.7rem; color:#666; margin-top:8px;">
                    {', '.join(row.get('key_matches',[])[:3])}
                </div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Enhancement summary ───────────────────────────────────────────────
    st.markdown('<div class="cv-card"><h3>✨  What Was Enhanced</h3>',
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Role Title**")
        st.markdown(f"> {enh.get('role_title','—')}")
        st.markdown("**Summary** *(first 180 chars)*")
        summary = enh.get("summary","")
        st.markdown(f"> {summary[:180]}{'…' if len(summary)>180 else ''}")
    with c2:
        bullets = enh.get("professional_skills_bullets", [])
        st.markdown(f"**Skills** *({len(bullets)} bullets updated)*")
        for b in bullets[:5]:
            st.markdown(f"- {b[:90]}")
        job_b = enh.get("job_bullets", {})
        total_b = sum(len(v) for v in job_b.values())
        st.markdown(f"**Job bullets:** {total_b} points across {len(job_b)} roles")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Download + Drive status ────────────────────────────────────────────
    c1, c2 = st.columns([2, 1])
    with c1:
        st.download_button(
            label=f"⬇️  Download  {fname}",
            data=out_bytes,
            file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
    with c2:
        st.markdown(f"""
        <div style="background:#D5F5E3; border-radius:10px; padding:14px;
                    text-align:center; height:100%; display:flex;
                    flex-direction:column; justify-content:center;">
            <div style="font-size:1.2rem;">☁️</div>
            <div style="font-size:0.78rem; font-weight:700; color:#1E8449;">
                Saved to Drive
            </div>
            <div style="font-size:0.7rem; color:#555; margin-top:2px;">
                CV Pilot / aligned_cvs
            </div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
#  Load library (cached)
# ══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def load_library() -> list:
    """Load the CV index from Drive with diagnostic logging."""
    try:
        from drive_client import DriveClient
        drive = DriveClient(
            credentials_json=get_secret("GOOGLE_CREDENTIALS_JSON"),
            folder_name=get_secret("DRIVE_FOLDER_NAME", "CV Pilot"),
        )
        index = drive.load_index()

        # DEBUG: Check base CVs folder for diagnostics
        try:
            base_cvs = drive.list_base_cvs()
            st.session_state["_debug_base_cvs_count"] = len(base_cvs)
        except Exception as e:
            st.session_state["_debug_error"] = f"Base CV check error: {str(e)[:60]}"

        return index
    except Exception as e:
        st.session_state["_debug_error"] = f"Library load error: {str(e)[:60]}"
        return []


# ══════════════════════════════════════════════════════════════════════════
#  Main app
# ══════════════════════════════════════════════════════════════════════════

def main():
    if not check_password():
        return

    # Load library for sidebar
    library = load_library()
    render_sidebar(library)

    # ── Page header ───────────────────────────────────────────────────────
    st.markdown("""
    <div style="padding: 8px 0 24px;">
        <h1 style="color:#1B4F72; margin:0; font-size:1.8rem;">
            🚀  CV Pilot
        </h1>
        <p style="color:#666; margin:4px 0 0; font-size:0.95rem;">
            Paste a job description below — Claude will pick the best matching CV,
            enhance it for this role, and save it to Google Drive automatically.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Input card ────────────────────────────────────────────────────────
    st.markdown('<div class="cv-card">', unsafe_allow_html=True)
    st.markdown('<div class="step-label">Step 1 — Job Description</div>',
                unsafe_allow_html=True)

    jd_tab, file_tab = st.tabs(["📋  Paste JD", "📁  Upload JD File"])

    with jd_tab:
        jd_text = st.text_area(
            "Job Description",
            height=260,
            placeholder="Paste the full job description here…\n\nInclude the role title, requirements, responsibilities, and any skills mentioned.",
            label_visibility="collapsed",
        )

    with file_tab:
        uploaded = st.file_uploader("Upload a .txt or .pdf JD file",
                                    type=["txt", "pdf"],
                                    label_visibility="collapsed")
        jd_text_from_file = ""
        if uploaded:
            if uploaded.type == "text/plain":
                jd_text_from_file = uploaded.read().decode("utf-8", errors="ignore")
                st.success(f"Loaded {len(jd_text_from_file)} characters from {uploaded.name}")
            elif uploaded.type == "application/pdf":
                try:
                    import pdfplumber
                    with pdfplumber.open(io.BytesIO(uploaded.read())) as pdf:
                        jd_text_from_file = "\n".join(
                            p.extract_text() or "" for p in pdf.pages
                        )
                    st.success(f"Extracted text from {uploaded.name}")
                except ImportError:
                    st.warning("PDF reading needs pdfplumber. Paste the JD as text instead.")

        if jd_text_from_file:
            jd_text = jd_text_from_file

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="step-label">Step 2 — Optional Details</div>',
                unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("Target company name",
                                placeholder="e.g.  Amazon, Microsoft, Google…",
                                help="Used in the output filename. Leave blank if not known.")
    with col2:
        role_hint = st.selectbox(
            "Role category hint (optional)",
            options=["— Auto-detect —", "AWS Cloud Engineer", "Cloud Solutions Architect",
                     "DevOps Engineer", "SRE", "AIOps Engineer",
                     "Azure DevOps Engineer", "Cloud Network Engineer", "Platform Engineer"],
            help="Leave on auto-detect — Claude will identify the role from the JD.",
        )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Generate button ───────────────────────────────────────────────────
    ready = bool(jd_text and len(jd_text.strip()) > 100)
    if not ready:
        st.info("👆  Paste a job description above (at least 100 characters) to enable generation.")

    generate = st.button("⚡  Generate CV",
                         type="primary",
                         disabled=not ready,
                         use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Run pipeline ──────────────────────────────────────────────────────
    if generate and ready:
        st.markdown("---")
        st.markdown("### Results")
        try:
            result = run_pipeline(
                jd_text=jd_text.strip(),
                company=company.strip(),
            )
            st.session_state["last_result"] = result
            # Refresh library after saving
            st.cache_data.clear()
        except Exception as e:
            st.error(f"Something went wrong: {e}")
            st.exception(e)
            st.stop()

    # ── Show last result (persists across reruns) ─────────────────────────
    if "last_result" in st.session_state and not generate:
        st.markdown("---")
        st.markdown("### Last Generated CV")
        show_results(st.session_state["last_result"])

    if "last_result" in st.session_state and generate:
        show_results(st.session_state["last_result"])


if __name__ == "__main__":
    main()
