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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ══════════════════════════════════════════════
   GLOBAL
══════════════════════════════════════════════ */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
[data-testid="stAppViewContainer"] {
    background: #F0F4F8;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { display: none; }

/* ══════════════════════════════════════════════
   SIDEBAR
══════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F1E36 0%, #1A2F4E 100%);
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] * { color: #C8D8EE !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.1) !important; }
[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 8px !important; color: #E8EDF5 !important;
}
[data-testid="stSidebar"] .stTextInput input::placeholder { color: rgba(200,216,238,0.45) !important; }
[data-testid="stSidebar"] .stTextInput input:focus {
    border-color: #4A9FD4 !important;
    box-shadow: 0 0 0 2px rgba(74,159,212,0.2) !important;
}
/* Sidebar refresh button */
[data-testid="stSidebar"] [data-testid="stButton"] button {
    background: rgba(46,134,193,0.2) !important;
    border: 1px solid rgba(46,134,193,0.4) !important;
    color: #7EB3E8 !important; border-radius: 8px !important;
    font-size: 0.82rem !important; font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    background: rgba(46,134,193,0.35) !important;
    border-color: rgba(46,134,193,0.6) !important;
    color: #A8D0F0 !important;
}

/* ══════════════════════════════════════════════
   LOGIN PAGE
══════════════════════════════════════════════ */
.login-page-bg {
    position: fixed; inset: 0; z-index: 0;
    background: linear-gradient(135deg, #0A1628 0%, #0F2044 40%, #0D3060 100%);
}
.login-card {
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 44px 40px 36px;
    box-shadow: 0 24px 64px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05);
}
.login-logo {
    font-size: 3rem; margin-bottom: 8px;
    filter: drop-shadow(0 4px 16px rgba(74,159,212,0.5));
}
.login-title {
    font-size: 1.9rem; font-weight: 700; margin: 0 0 4px;
    background: linear-gradient(135deg, #FFFFFF, #90C8E8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.login-subtitle {
    font-size: 0.88rem; color: rgba(200,216,238,0.6); margin: 0 0 32px;
}
/* Login input */
.login-card .stTextInput input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important; color: #E8EDF5 !important;
    font-size: 0.95rem !important; padding: 12px 16px !important;
    height: 48px !important; transition: all 0.2s ease !important;
}
.login-card .stTextInput input::placeholder { color: rgba(200,216,238,0.35) !important; }
.login-card .stTextInput input:focus {
    border-color: #4A9FD4 !important;
    box-shadow: 0 0 0 3px rgba(74,159,212,0.18) !important;
    background: rgba(255,255,255,0.09) !important;
}
.login-card label { color: rgba(200,216,238,0.7) !important; font-size: 0.82rem !important; font-weight: 500 !important; }
/* Login submit button — scoped to primaryFormSubmit only, never catches eye icon */
[data-testid="stForm"] button[kind="primaryFormSubmit"] {
    background: linear-gradient(135deg, #1565C0, #1E88E5) !important;
    color: #FFFFFF !important; border: none !important;
    border-radius: 10px !important; height: 48px !important;
    font-size: 0.96rem !important; font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 4px 16px rgba(21,101,192,0.45) !important;
    transition: all 0.18s ease !important;
    width: 100% !important;
}
[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover {
    background: linear-gradient(135deg, #1976D2, #42A5F5) !important;
    box-shadow: 0 6px 24px rgba(21,101,192,0.6) !important;
    transform: translateY(-1px) !important;
    color: #FFFFFF !important;
}
[data-testid="stForm"] button[kind="primaryFormSubmit"]:active {
    transform: translateY(0px) !important;
    box-shadow: 0 2px 8px rgba(21,101,192,0.4) !important;
}

/* ══════════════════════════════════════════════
   MAIN APP INPUTS
══════════════════════════════════════════════ */
.stTextArea textarea {
    border-radius: 10px !important;
    border: 1.5px solid #CBD5E1 !important;
    font-size: 0.93rem !important;
    background: #FFFFFF !important;
    color: #1E293B !important;
    transition: border-color 0.2s ease !important;
    line-height: 1.6 !important;
}
.stTextArea textarea:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
}
.stTextInput input {
    border-radius: 9px !important;
    border: 1.5px solid #CBD5E1 !important;
    font-size: 0.92rem !important; color: #1E293B !important;
    transition: border-color 0.2s ease !important;
}
.stTextInput input:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
}
.stSelectbox > div > div {
    border-radius: 9px !important; border: 1.5px solid #CBD5E1 !important;
}

/* ══════════════════════════════════════════════
   BUTTONS
══════════════════════════════════════════════ */
/* Primary — Generate CV */
[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #1565C0 0%, #1E88E5 100%) !important;
    color: #FFFFFF !important; border: none !important;
    border-radius: 12px !important;
    padding: 14px 36px !important; font-size: 1.05rem !important;
    font-weight: 600 !important; letter-spacing: 0.2px !important;
    box-shadow: 0 4px 18px rgba(21,101,192,0.4) !important;
    transition: all 0.18s ease !important;
}
[data-testid="stButton"] button[kind="primary"]:hover {
    background: linear-gradient(135deg, #1976D2 0%, #42A5F5 100%) !important;
    box-shadow: 0 8px 28px rgba(21,101,192,0.55) !important;
    transform: translateY(-2px) !important;
    color: #FFFFFF !important;
}
[data-testid="stButton"] button[kind="primary"]:active {
    transform: translateY(0px) !important;
}
/* Disabled state — clear visual feedback instead of confusing cursor */
[data-testid="stButton"] button[kind="primary"]:disabled {
    background: linear-gradient(135deg, #94A3B8 0%, #B0BEC5 100%) !important;
    box-shadow: none !important;
    cursor: not-allowed !important;
    opacity: 0.7 !important;
    transform: none !important;
}
/* Secondary */
[data-testid="stButton"] button[kind="secondary"] {
    background: #FFFFFF !important; color: #1E40AF !important;
    border: 1.5px solid #BFDBFE !important; border-radius: 9px !important;
    font-weight: 500 !important; transition: all 0.18s ease !important;
}
[data-testid="stButton"] button[kind="secondary"]:hover {
    background: #EFF6FF !important; border-color: #93C5FD !important;
}
/* Download button */
[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, #065F46, #059669) !important;
    color: white !important; border: none !important;
    border-radius: 12px !important; padding: 13px 28px !important;
    font-size: 1rem !important; font-weight: 600 !important;
    box-shadow: 0 4px 14px rgba(5,150,105,0.35) !important;
    transition: all 0.18s ease !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: linear-gradient(135deg, #047857, #10B981) !important;
    box-shadow: 0 6px 20px rgba(5,150,105,0.5) !important;
    transform: translateY(-1px) !important;
}

/* ══════════════════════════════════════════════
   TABS
══════════════════════════════════════════════ */
[data-testid="stTabs"] [role="tablist"] {
    gap: 4px; border-bottom: 2px solid #E2E8F0;
}
[data-testid="stTabs"] button[role="tab"] {
    font-size: 0.85rem !important; font-weight: 500 !important;
    color: #64748B !important; padding: 8px 16px !important;
    border-radius: 6px 6px 0 0 !important;
    transition: all 0.15s ease !important;
}
[data-testid="stTabs"] button[role="tab"]:hover { color: #1E40AF !important; background: #F1F5F9 !important; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #1E40AF !important; font-weight: 600 !important;
    border-bottom: 2px solid #1E40AF !important;
    background: transparent !important;
}

/* ══════════════════════════════════════════════
   CARDS & CONTAINERS
══════════════════════════════════════════════ */
.cv-card {
    background: #FFFFFF; border-radius: 14px;
    padding: 26px 30px; margin-bottom: 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.05);
    border: 1px solid #E8EFF5;
}
.cv-card h3 { color: #1E3A5F; margin-top: 0; font-size: 1.05rem; font-weight: 600; }

/* ══════════════════════════════════════════════
   SCORE BADGES
══════════════════════════════════════════════ */
.score-high { background:#DCFCE7; color:#15803D; padding:4px 14px;
              border-radius:20px; font-weight:700; font-size:0.88rem;
              border: 1px solid #BBF7D0; }
.score-mid  { background:#FEF9C3; color:#92400E; padding:4px 14px;
              border-radius:20px; font-weight:700; font-size:0.88rem;
              border: 1px solid #FDE68A; }
.score-low  { background:#FEE2E2; color:#B91C1C; padding:4px 14px;
              border-radius:20px; font-weight:700; font-size:0.88rem;
              border: 1px solid #FECACA; }

/* ══════════════════════════════════════════════
   TAGS
══════════════════════════════════════════════ */
.tag { background:#EFF6FF; color:#1D4ED8; padding:3px 11px;
       border-radius:20px; font-size:0.75rem; margin:2px 3px 2px 0;
       display:inline-block; font-weight:500; border: 1px solid #BFDBFE; }

/* ══════════════════════════════════════════════
   STEP LABELS & DIVIDERS
══════════════════════════════════════════════ */
.step-label {
    font-size: 0.72rem; font-weight: 700; color: #3B82F6;
    text-transform: uppercase; letter-spacing: 1.5px;
    margin-bottom: 10px; display: flex; align-items: center; gap: 6px;
}
hr { border: none; border-top: 1px solid #E2E8F0; margin: 20px 0; }

/* ══════════════════════════════════════════════
   ALERTS / INFO BOXES
══════════════════════════════════════════════ */
[data-testid="stAlert"] {
    border-radius: 10px !important; border-left-width: 4px !important;
    font-size: 0.88rem !important;
}

/* ══════════════════════════════════════════════
   PROGRESS BAR
══════════════════════════════════════════════ */
[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #1565C0, #42A5F5) !important;
    border-radius: 4px !important;
}

/* ══════════════════════════════════════════════
   SCROLLBAR
══════════════════════════════════════════════ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94A3B8; }
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
    st.markdown("""
    <style>
    /* Login-only overrides */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0A1628 0%, #0F2044 45%, #0D3060 100%) !important;
    }
    [data-testid="stSidebar"]        { display: none !important; }
    [data-testid="stHeader"]         { display: none !important; }
    [data-testid="block-container"]  { padding-top: 5vh !important; }

    /* ── Password eye-icon: reset to small icon only ── */
    [data-testid="stTextInput"] button,
    [data-testid="stTextInput"] button:hover,
    [data-testid="stTextInput"] button:focus {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        width: 36px !important;
        min-width: 36px !important;
        height: 36px !important;
        padding: 6px !important;
        color: rgba(200,216,238,0.5) !important;
        transform: none !important;
    }

    /* ── Login submit button only ── */
    [data-testid="stForm"] button[kind="primaryFormSubmit"] {
        background: linear-gradient(135deg, #1565C0, #1E88E5) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        height: 48px !important;
        width: 100% !important;
        font-size: 0.96rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 16px rgba(21,101,192,0.45) !important;
        transition: all 0.18s ease !important;
        letter-spacing: 0.3px !important;
    }
    [data-testid="stForm"] button[kind="primaryFormSubmit"]:hover {
        background: linear-gradient(135deg, #1976D2, #42A5F5) !important;
        box-shadow: 0 6px 24px rgba(21,101,192,0.65) !important;
        transform: translateY(-1px) !important;
        color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Center column: logo + form together (no gap)
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        # Logo + title
        st.markdown("""
        <div style="text-align:center; padding:32px 0 28px;">
            <div style="font-size:3rem; margin-bottom:14px;
                        filter:drop-shadow(0 4px 20px rgba(74,159,212,0.6));">🚀</div>
            <div style="font-size:1.95rem; font-weight:700; letter-spacing:-0.3px;
                        background:linear-gradient(135deg,#FFFFFF 30%,#90C8E8 100%);
                        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                        background-clip:text; margin-bottom:6px;">CV Pilot</div>
            <div style="font-size:0.85rem; color:rgba(200,216,238,0.5);
                        letter-spacing:0.3px;">Sashi Kiran's AI CV Engine</div>
        </div>
        """, unsafe_allow_html=True)

        # Form card
        with st.form("login_form"):
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter team password",
            )
            submitted = st.form_submit_button("🔐  Sign In", use_container_width=True)

        if submitted:
            if hashlib.sha256(password.encode()).hexdigest() == correct_hash:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")

        st.markdown("""
        <div style="text-align:center; margin-top:16px;">
            <span style="font-size:0.72rem; color:rgba(200,216,238,0.25);
                         letter-spacing:0.5px;">Secure · Private · AI-Powered</span>
        </div>
        """, unsafe_allow_html=True)
    return False


def score_colour(score: int) -> str:
    if score >= 75: return "score-high"
    if score >= 55: return "score-mid"
    return "score-low"


def render_sidebar(cv_library: list):
    """Render the left sidebar with library stats and saved CVs."""
    with st.sidebar:
        st.markdown("""
        <div style="padding:20px 4px 12px; text-align:center;">
            <div style="font-size:2rem; margin-bottom:6px;
                        filter:drop-shadow(0 2px 8px rgba(74,159,212,0.5));">🚀</div>
            <div style="font-size:1.05rem; font-weight:700; color:#E8F4FF;
                        letter-spacing:0.3px;">CV Pilot</div>
            <div style="font-size:0.72rem; color:rgba(200,216,238,0.45);
                        margin-top:2px; letter-spacing:0.2px;">
                Sashi Kiran's AI CV Engine
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Stats ──
        total = len(cv_library)
        roles = list(set(e.get("role_category","—") for e in cv_library))

        # Debug diagnostic messages
        debug_msg = ""
        if total == 0 and "_debug_base_cvs_count" in st.session_state:
            base_count = st.session_state.get("_debug_base_cvs_count", 0)
            if base_count == 0:
                debug_msg = "⚠️ No base CVs uploaded yet"
            else:
                debug_msg = f"Base CVs: {base_count} | Index: empty"
        elif total == 0 and "_debug_error" in st.session_state:
            error_text = st.session_state.get("_debug_error", "Unknown error")[:40]
            debug_msg = f"⚠️ Error: {error_text}..."

        debug_html = f'<div style="font-size:0.72rem; color:#E67E22; margin-top:6px;">{debug_msg}</div>' if debug_msg else ''

        st.markdown(f"""
        <div style="text-align:center; padding:8px 0 12px;">
            <div style="font-size:2rem; font-weight:700; color:#7EB3E8;">{total}</div>
            <div style="font-size:0.78rem; opacity:0.7;">CVs in library</div>
            {debug_html}
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔄  Refresh Library", key="refresh_lib"):
            st.cache_data.clear()
            # Clear debug session state
            for key in ["_debug_base_cvs_count", "_debug_error", "_template_active"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        st.markdown("---")

        # ── Template status ──
        template_active = st.session_state.get("_template_active", None)
        if template_active is True:
            st.markdown("""
            <div style="background:#1A3D2B; border-radius:8px; padding:10px 14px;
                        margin-bottom:8px; border-left:3px solid #27AE60;">
                <div style="font-size:0.75rem; font-weight:700; color:#2ECC71;">
                    🎨  Design Template Active
                </div>
                <div style="font-size:0.68rem; opacity:0.7; margin-top:2px;">
                    _template.docx found in CV Pilot/
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif template_active is False:
            st.markdown("""
            <div style="background:#2A2A1A; border-radius:8px; padding:10px 14px;
                        margin-bottom:8px; border-left:3px solid #E67E22;">
                <div style="font-size:0.75rem; font-weight:700; color:#E67E22;">
                    🎨  No Design Template
                </div>
                <div style="font-size:0.68rem; opacity:0.7; margin-top:2px;">
                    Upload _template.docx to CV Pilot/ to set one
                </div>
            </div>
            """, unsafe_allow_html=True)

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
                <div style="background:rgba(255,255,255,0.05); border-radius:10px;
                            padding:11px 14px; margin-bottom:7px;
                            border:1px solid rgba(255,255,255,0.08);
                            transition:background 0.15s ease;">
                    <div style="font-size:0.78rem; font-weight:600; margin-bottom:4px;
                                word-break:break-all; color:#D4E8FA;">{name[:36]}</div>
                    <div style="display:flex; justify-content:space-between;
                                align-items:center;">
                        <span style="font-size:0.69rem; color:rgba(200,216,238,0.55);">{role}</span>
                        <span class="{cls}" style="font-size:0.68rem;">{score}/100</span>
                    </div>
                    <div style="font-size:0.66rem; color:rgba(200,216,238,0.3); margin-top:3px;">{date}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:rgba(200,216,238,0.35); font-size:0.82rem; padding:8px 4px;'>No CVs found</div>",
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

    # ── 5. Check for design template ─────────────────────────────────────
    progress.progress(67, text="🎨  Checking for design template...")
    template_bytes = drive.get_template_cv()
    st.session_state["_template_active"] = template_bytes is not None
    # Use template for output design if available, otherwise use best CV
    base_for_output = template_bytes if template_bytes else cv_bytes

    # ── 6. Enhance (based on best CV content) ────────────────────────────
    enhancements = enhance_cv(client, best_text, jd)

    # ── 7. Apply to DOCX ──────────────────────────────────────────────────
    progress.progress(80, text="📝  Writing enhanced CV...")
    output_bytes = apply_enhancements(base_for_output, enhancements)

    # ── 7. Build filename & save to Drive ─────────────────────────────────
    progress.progress(90, text="☁️  Saving to Google Drive...")
    role   = jd["role_title"].replace(" ", "_").replace("/", "-")
    cloud  = jd["cloud_platform"].replace("-", "")
    co     = ("_" + company.replace(" ", "_")) if company else ""
    date   = datetime.now().strftime("%Y%m%d")
    fname  = f"{role}_{cloud}{co}_{date}.docx"

    drive_error = None
    try:
        drive.save_aligned_cv(fname, output_bytes)

        # ── 8. Update index (load existing → append → save) ──────────────────
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
        # Load existing index, append new entry, then save the full list
        existing_index = drive.load_index()
        if not isinstance(existing_index, list):
            existing_index = []
        existing_index.append(index_entry)
        drive.update_index(existing_index)
    except Exception as e:
        # Capture error but don't stop — user can still download
        drive_error = str(e)[:100]

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
        "drive_error": drive_error,
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
    drive_error = result.get("drive_error")

    # ── Download bar (top priority — recruiter wants file fast) ───────────
    st.markdown("---")
    dl_col, status_col = st.columns([3, 1])
    with dl_col:
        st.download_button(
            label=f"⬇️  Download  {fname}",
            data=out_bytes,
            file_name=fname,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
    with status_col:
        if drive_error:
            st.error("☁️ Drive save failed — use download", icon="⚠️")
        else:
            st.success("☁️ Saved to Drive", icon="✅")

    st.markdown("---")

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
                <div style="font-weight:600; color:#1E293B;">{jd['cloud_platform']}</div>
            </div>
            <div>
                <div style="font-size:0.72rem; color:#888; margin-bottom:2px;">SENIORITY</div>
                <div style="font-weight:600; color:#1E293B;">{jd['seniority']}</div>
            </div>
            <div>
                <div style="font-size:0.72rem; color:#888; margin-bottom:2px;">EXPERIENCE</div>
                <div style="font-weight:600; color:#1E293B;">{jd.get('years_experience','—')}</div>
            </div>
        </div>
        <div style="margin-top:14px;">
            {''.join(f'<span class="tag">{k}</span>' for k in jd['ats_keywords'][:12])}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── CV scores ─────────────────────────────────────────────────────────
    score_html = '<div class="cv-card"><h3>🎯  CV Match Scores</h3><div style="display:flex; gap:12px; flex-wrap:wrap;">'
    for i, row in enumerate(scored[:4]):
        sc  = row["score"]
        cls = score_colour(sc)
        stem = Path(row['filename']).stem[:28]
        matches = ', '.join(row.get('key_matches',[])[:3])
        bg  = '#EBF5FB' if i == 0 else '#F7F9FC'
        bdr = '2px solid #2E86C1' if i == 0 else '1px solid #E8EDF5'
        lbl = '⭐ BEST MATCH' if i == 0 else f'#{i+1}'
        score_html += f"""
        <div style="background:{bg}; border-radius:10px; padding:14px; text-align:center;
                    border:{bdr}; flex:1; min-width:140px;">
            <div style="font-size:0.72rem; color:#888; margin-bottom:4px;">{lbl}</div>
            <div style="font-weight:700; font-size:0.82rem; color:#1B4F72;
                        word-break:break-all; margin-bottom:8px;">{stem}</div>
            <span class="{cls}">{sc}/100</span>
            <div style="font-size:0.7rem; color:#666; margin-top:8px;">{matches}</div>
        </div>"""
    score_html += '</div></div>'
    st.markdown(score_html, unsafe_allow_html=True)

    # ── Enhancement summary ─────────────────────────────────────────────────
    # Use native Streamlit components (not raw HTML) to avoid rendering bugs
    import html as html_mod   # for escaping dynamic content

    role_title = enh.get('role_title', '—')
    summary    = enh.get('summary', '')
    bullets    = enh.get('professional_skills_bullets', [])
    job_b      = enh.get('job_bullets', {})
    total_b    = sum(len(v) for v in job_b.values())

    st.markdown("#### ✨  What Was Enhanced")
    st.caption("Here's exactly what the AI changed in your CV for this role.")

    # ── Row 1: Role title + Summary ──────────────────────────────────────
    r1c1, r1c2 = st.columns([1, 2])
    with r1c1:
        st.markdown("**🏷️ Updated Role Title**")
        st.info(role_title)
    with r1c2:
        st.markdown("**📝 New Professional Summary**")
        st.text_area("summary_preview", value=summary, height=100,
                      disabled=True, label_visibility="collapsed",
                      key="enh_summary_preview")

    # ── Row 2: Skills + Experience ────────────────────────────────────────
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown(f"**🛠️ Skills Section** *({len(bullets)} lines rewritten)*")
        for b in bullets[:6]:
            st.markdown(f"- {b}")

    with r2c2:
        st.markdown(f"**💼 Experience Bullets** *({total_b} points across {len(job_b)} roles)*")
        for comp_name, comp_bullets in list(job_b.items())[:3]:
            st.markdown(f"**{html_mod.escape(comp_name)}**")
            for jb in comp_bullets[:3]:
                st.markdown(f"- {jb}")

    st.markdown("---")


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
    <div style="padding:16px 0 24px; border-bottom:1px solid #E2E8F0; margin-bottom:24px;">
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:6px;">
            <span style="font-size:1.8rem;">🚀</span>
            <h1 style="color:#0F2044; margin:0; font-size:1.75rem; font-weight:700;
                       letter-spacing:-0.3px;">CV Pilot</h1>
        </div>
        <p style="color:#64748B; margin:0; font-size:0.92rem; max-width:620px; line-height:1.55;">
            Paste the job description below and hit <strong>Generate</strong>.
            The AI will find the best-matching CV from your library, tailor it to the role,
            and give you an ATS-ready file to download — all in under a minute.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── How it works (helpful for non-technical recruiters) ───────────────
    with st.expander("ℹ️  How does this work?", expanded=False):
        st.markdown("""
        **3 simple steps:**

        1. **Paste the job description** — copy it from the job posting or client email
        2. **Click Generate** — the AI reads the JD, scores all your CVs against it, picks the best one, and rewrites it to match the role
        3. **Download the result** — you get a `.docx` file ready to submit to the client

        The tool checks for ATS keywords, rewrites bullet points to sound natural (not robotic),
        and keeps all dates, companies, and job titles accurate. Nothing is fabricated.
        """)

    # ── Input card ────────────────────────────────────────────────────────
    with st.container():
        st.markdown('<div class="step-label">📋 Step 1 — Paste the Job Description</div>',
                    unsafe_allow_html=True)

        jd_text = ""
        jd_tab, file_tab = st.tabs(["📋  Paste JD", "📁  Upload JD File"])

        with jd_tab:
            st.text_area(
                "Job Description",
                height=260,
                placeholder="Paste the full job description here…\n\nInclude the role title, requirements, responsibilities, and any skills mentioned.",
                label_visibility="collapsed",
                key="jd_input_area",
            )
            # Read from session state (reliable across Streamlit reruns & tabs)
            jd_text = st.session_state.get("jd_input_area", "")

        with file_tab:
            uploaded = st.file_uploader("Upload a .txt or .pdf JD file",
                                        type=["txt", "pdf"],
                                        label_visibility="collapsed")
            if uploaded:
                if uploaded.type == "text/plain":
                    jd_text_from_file = uploaded.read().decode("utf-8", errors="ignore")
                    st.session_state["jd_input_area"] = jd_text_from_file
                    jd_text = jd_text_from_file
                    st.success(f"Loaded {len(jd_text_from_file)} characters from {uploaded.name}")
                elif uploaded.type == "application/pdf":
                    try:
                        import pdfplumber
                        with pdfplumber.open(io.BytesIO(uploaded.read())) as pdf:
                            jd_text_from_file = "\n".join(
                                p.extract_text() or "" for p in pdf.pages
                            )
                        st.session_state["jd_input_area"] = jd_text_from_file
                        jd_text = jd_text_from_file
                        st.success(f"Extracted text from {uploaded.name}")
                    except ImportError:
                        st.warning("PDF reading needs pdfplumber. Paste the JD as text instead.")

        st.markdown("---")
        st.markdown('<div class="step-label">⚙️ Step 2 — Optional (helps with filing)</div>',
                    unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            company = st.text_input("Client / company name",
                                    placeholder="e.g.  Amazon, Microsoft, Google…",
                                    help="Added to the filename so you can find it later. Leave blank if unknown.")
        with col2:
            role_hint = st.selectbox(
                "Role category (auto-detected if blank)",
                options=["— Auto-detect —", "AWS Cloud Engineer", "Cloud Solutions Architect",
                         "DevOps Engineer", "SRE", "AIOps Engineer",
                         "Azure DevOps Engineer", "Cloud Network Engineer", "Platform Engineer"],
                help="The AI detects this from the JD — only override if it gets it wrong.",
            )

        st.markdown("---")

        # ── Generate button ───────────────────────────────────────────────────
        ready = bool(jd_text and len(jd_text.strip()) > 100)
        if not ready:
            st.info("👆  Paste a job description above (at least 100 characters) to get started.")

        generate = st.button("⚡  Generate Tailored CV",
                             type="primary",
                             disabled=not ready,
                             use_container_width=True)

    # ── Run pipeline ──────────────────────────────────────────────────────
    if generate and ready:
        st.markdown("---")
        st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:16px;">
            <span style="font-size:1.4rem;">📄</span>
            <h3 style="color:#0F2044; margin:0; font-weight:700;">Your Tailored CV</h3>
        </div>
        """, unsafe_allow_html=True)
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
        st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:16px;">
            <span style="font-size:1.4rem;">📄</span>
            <h3 style="color:#0F2044; margin:0; font-weight:700;">Last Generated CV</h3>
        </div>
        """, unsafe_allow_html=True)
        show_results(st.session_state["last_result"])

    if "last_result" in st.session_state and generate:
        show_results(st.session_state["last_result"])


if __name__ == "__main__":
    main()
