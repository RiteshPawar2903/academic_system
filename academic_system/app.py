"""
app.py
Academic Result Analysis System — Main Streamlit application.

Run with:  streamlit run app.py
"""

import base64
import json
import io
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st

from database import (
    init_db,
    create_user,
    get_user_by_username,
    get_user_by_email,
    save_upload,
    get_user_uploads,
    get_upload_metadata,
    get_upload_pdf,
    get_tables_for_upload,
    delete_upload,
)
from auth import hash_password, verify_password
from pdf_processor import extract_tables_from_pdf

# ─────────────────────────────────────────────────────────────────────────────
# INITIALISATION
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AcademiQ — Result Analysis System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_db()

# Session state defaults
for key, default in {
    "authenticated": False,
    "user_id": None,
    "username": None,
    "page": "auth",          # auth | dashboard | file_view
    "current_upload_id": None,
    "auth_tab": "login",     # login | register
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────

def inject_css():
    st.markdown(
        """
<style>
/* ── Fonts ───────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* ── Design Tokens (Modern Light Slate & Indigo) ────────────────── */
:root {
    /* Backgrounds */
    --bg-color:      #FFFFFF;
    --surface:       #F8FAFC;
    --surface2:      #F1F5F9;
    --surface-hover: #F8FAFC;
    
    /* Borders & Dividers */
    --border:        #E2E8F0;
    --border-focus:  #CBD5E1;
    
    /* Colors */
    --primary:       #4F46E5;
    --primary-light: #818CF8;
    --primary-glow:  rgba(79, 70, 229, 0.15);
    
    --text-main:     #334155;
    --text-muted:    #64748B;
    
    /* Status Colors */
    --success:       #10B981;
    --danger:        #EF4444;
    --warning:       #F59E0B;
    
    /* Spacing & Radius */
    --radius:        12px;
    --radius-lg:     16px;
    --radius-pill:   50px;
}

/* ── Reset Streamlit Chrome ───────────────────────────────────── */
/* Only hide specific elements, keep header for logo */
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
.stDeployButton { display: none !important; }
.block-container {
    padding: 2rem 2rem 2rem 2rem !important;
    max-width: 100% !important;
    background-color: var(--bg-color) !important;
}
section[data-testid="stSidebar"] { display: none !important; }

/* ── Base ────────────────────────────────────────────────────── */
html, body, [data-testid="stApp"], [data-testid="stHeader"] {
    font-family: 'Outfit', sans-serif !important;
    background-color: var(--bg-color) !important;
    color: var(--text-main) !important;
}

[data-testid="stApp"] {
    background-image: none !important;
}

/* ── Header & Logo ────────────────────────────────────────────── */
[data-testid="stHeader"] {
    background: linear-gradient(135deg, var(--surface) 0%, #FFFFFF 100%) !important;
    border-bottom: 1px solid var(--border) !important;
    padding: 1rem 2rem !important;
}

[data-testid="stHeader"] img {
    max-height: 40px !important;
    object-fit: contain !important;
}

/* ── Popover dropdowns (Selectbox options) ────────────────────── */
div[data-baseweb="popover"] > div {
    background-color: #FFFFFF !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05) !important;
    padding: 8px !important;
}
div[data-baseweb="popover"] li[role="option"] {
    background-color: transparent !important;
    color: var(--text-main) !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
    padding: 10px 12px !important;
    border-radius: 6px !important;
}
div[data-baseweb="popover"] li[role="option"]:hover {
    background-color: var(--surface) !important;
}
div[data-baseweb="popover"] li[aria-selected="true"] {
    background-color: var(--primary-glow) !important;
    color: var(--primary) !important;
}

/* ── Scrollbar ───────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ── Streamlit element overrides ─────────────────────────────── */
.stTextInput > label,
.stSelectbox > label,
.stFileUploader > label { 
    color: var(--text-main) !important; 
    font-size: 0.85rem !important; 
    font-weight: 600 !important; 
    letter-spacing: 0.03em; 
    text-transform: uppercase;
    font-family: 'Space Grotesk', sans-serif !important;
    margin-bottom: 0.5rem !important;
    opacity: 0.8;
}

/* Inputs */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: #FFFFFF !important;
    border: 1px solid var(--border) !important;
    color: var(--text-main) !important;
    border-radius: var(--radius) !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
    min-height: 48px !important;
    padding: 0 1rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02) !important;
}

/* Fix for invisible text in Selectbox */
.stSelectbox [data-baseweb="select"] * {
    color: var(--text-main) !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div:focus-within { 
    border-color: var(--primary) !important; 
    box-shadow: 0 0 0 4px var(--primary-glow) !important;
    outline: none !important;
}

/* Buttons */
.stButton > button {
    background: var(--primary) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-weight: 600 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s ease !important;
    text-transform: none;
    letter-spacing: 0.02em;
    box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2) !important;
}
.stButton > button:hover {
    background: #4338CA !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.3) !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
    box-shadow: none !important;
}

.stButton > button[kind="secondary"] {
    background: #FFFFFF !important;
    color: var(--text-main) !important;
    border: 1px solid var(--border) !important;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
}
.stButton > button[kind="secondary"]:hover {
    background: var(--surface) !important;
    border-color: var(--text-muted) !important;
}

/* File uploader */
.stFileUploader > div {
    background: var(--surface) !important;
    border: 2px dashed var(--border) !important;
    border-radius: var(--radius-lg) !important;
    color: var(--text-muted) !important;
    transition: all 0.2s ease !important;
}
.stFileUploader > div:hover { 
    border-color: var(--primary) !important; 
    background: rgba(79, 70, 229, 0.03) !important;
    color: var(--primary) !important;
}

/* Dataframe */
.stDataFrame { 
    border: 1px solid var(--border) !important; 
    border-radius: var(--radius) !important; 
    background: #FFFFFF !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02) !important;
}
.stDataFrame th { 
    background: var(--surface2) !important; 
    color: var(--text-main) !important; 
    font-weight: 700 !important; 
    font-family: 'Space Grotesk', sans-serif !important; 
    font-size: 0.8rem !important; 
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.stDataFrame td { color: var(--text-main) !important; border-color: var(--border) !important; }

/* Alert / info boxes */
[data-testid="stAlert"] {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    background-color: #FFFFFF !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02) !important;
}
.stSuccess { border-left: 4px solid var(--success) !important; color: var(--text-main) !important; background: rgba(16, 185, 129, 0.05) !important; }
.stError { border-left: 4px solid var(--danger) !important; color: var(--text-main) !important; background: rgba(239, 68, 68, 0.05) !important; }
.stWarning { border-left: 4px solid var(--warning) !important; background: rgba(245, 158, 11, 0.05) !important; }
.stInfo { border-left: 4px solid var(--primary) !important; background: rgba(79, 70, 229, 0.05) !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { 
    background: var(--surface) !important; 
    border-radius: var(--radius) !important; 
    padding: 4px !important; 
    gap: 4px !important;
    border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] { 
    background: transparent !important; 
    color: var(--text-muted) !important; 
    border-radius: 8px !important; 
    font-weight: 600 !important; 
    font-family: 'Space Grotesk', sans-serif !important; 
    transition: all 0.2s ease !important; 
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-main) !important;
    background: rgba(0,0,0,0.03) !important;
}
.stTabs [aria-selected="true"] { 
    background: #FFFFFF !important;
    color: var(--primary) !important; 
    box-shadow: 0 2px 4px 0 rgba(0, 0, 0, 0.05) !important; 
}
.stTabs [data-baseweb="tab-panel"] { background: transparent !important; padding: 1.5rem 0 0 0 !important; }

/* Spinner */
.stSpinner > div { border-top-color: var(--primary) !important; }

/* Divider */
hr { border-color: var(--border) !important; margin: 2rem 0 !important; opacity: 1; }

/* Magical Text Gradient */
.text-gradient {
    background: linear-gradient(135deg, var(--primary) 0%, #818CF8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    color: transparent;
    font-weight: 800;
}

/* ── Emoji & Icon Fixes ───────────────────────────────────────── */
/* Ensure emojis display correctly */
[data-testid="stMarkdown"] *,
[data-testid="stText"] *,
[data-testid="stMetric"] * {
    font-family: 'Outfit', sans-serif !important;
}

/* Icon elements */
[data-testid="stIcon"] {
    color: var(--primary) !important;
}

/* Ensure all text elements are visible */
[data-testid="stMarkdown"] {
    color: var(--text-main) !important;
}

/* Fix for any hidden elements */
* {
    visibility: visible !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# SHARED COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────

def top_nav(title: str = "AcademiQ", show_logout: bool = True):
    st.markdown(
        f"""
<div style="
    background: #FFFFFF;
    border-bottom: 1px solid var(--border);
    padding: 0 2.5rem;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 999;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
">
    <div style="display:flex;align-items:center;gap:12px;">
        <div style="
            width:32px;height:32px;
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%);
            border-radius: 8px;
            display:flex;align-items:center;justify-content:center;
            font-size:16px;font-weight:900;color:#FFF;
        ">A</div>
        <span style="font-family:'Space Grotesk',sans-serif;font-size:1.25rem;font-weight:700;letter-spacing:-0.02em;" class="text-gradient">
            {title}
        </span>
    </div>
    <div style="display:flex;align-items:center;gap:1.5rem;">
        {'<span style="font-size:0.85rem;font-weight:500;color:var(--text-muted);background:var(--surface);padding:0.4rem 0.8rem;border-radius:20px;border:1px solid var(--border);">🚀 &nbsp;&nbsp;' + (st.session_state.username or "") + '</span>' if show_logout and st.session_state.username else ''}
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def card(content_html: str, padding: str = "1.25rem 1.5rem", extra_style: str = ""):
    st.markdown(
        f"""
<div style="
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: {padding};
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    {extra_style}
">
    {content_html}
</div>
        """,
        unsafe_allow_html=True,
    )


def badge(text: str, color: str = "var(--accent)", bg: str = "rgba(59, 130, 246, 0.1)"):
    return f"""<span style="
        background:{bg};color:{color};
        border-radius:20px;padding:2px 10px;
        font-size:0.75rem;font-weight:600;
        font-family:'Outfit',sans-serif;
    ">{text}</span>"""


def fmt_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / 1024 ** 2:.2f} MB"


def fmt_date(dt_str: str) -> str:
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%b %d, %Y • %H:%M")
    except Exception:
        return dt_str or "—"


# ─────────────────────────────────────────────────────────────────────────────
# AUTH PAGE
# ─────────────────────────────────────────────────────────────────────────────

def page_auth():
    inject_css()

    st.markdown(
        """
<div style="
    min-height:100vh;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    padding: 2rem 1rem;
    background-color: #F9FAFB;
">
    <div style="
        text-align:center;max-width:440px;width:100%;
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 2.5rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
    ">
        <div style="
            width:56px;height:56px;
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-light) 100%);
            border-radius:14px;
            display:inline-flex;align-items:center;justify-content:center;
            font-size:28px;font-weight:900;color:#FFF;
            margin-bottom:1.5rem;
        ">A</div>
        <h1 style="
            font-family:'Space Grotesk',sans-serif;
            font-weight: 800;
            font-size:2.5rem;
            margin:0 0 0.5rem;
            line-height:1.1;
            letter-spacing:-0.03em;
        " class="text-gradient">AcademiQ</h1>
        <p style="
            color:var(--text-muted);
            font-size:1rem;
            font-weight: 500;
            margin-bottom:2rem;
        ">
            Result Analysis System
        </p>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([0.1, 2, 0.1])
    with col2:
        tab_login, tab_register = st.tabs(["🔑  Sign In", "✨  Create Account"])

        with tab_login:
            _login_form()

        with tab_register:
            _register_form()

    st.markdown("</div></div>", unsafe_allow_html=True)


def _login_form():
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    username = st.text_input("Username", key="login_username", placeholder="your_username")
    password = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")

    if st.button("Sign In", key="btn_login", use_container_width=True):
        if not username or not password:
            st.error("Please fill in all fields.")
            return
        user = get_user_by_username(username)
        if not user or not verify_password(password, user["password_hash"]):
            st.error("Invalid username or password.")
            return
        st.session_state.authenticated = True
        st.session_state.user_id = user["id"]
        st.session_state.username = user["username"]
        st.session_state.page = "dashboard"
        st.rerun()


def _register_form():
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    username = st.text_input("Username", key="reg_username", placeholder="choose_username")
    email = st.text_input("Email", key="reg_email", placeholder="you@example.com")
    password = st.text_input("Password", type="password", key="reg_password", placeholder="min. 8 chars")
    confirm = st.text_input("Confirm Password", type="password", key="reg_confirm", placeholder="repeat password")

    if st.button("Create Account", key="btn_register", use_container_width=True):
        errs = []
        if not username or len(username) < 3:
            errs.append("Username must be at least 3 characters.")
        if not email or "@" not in email:
            errs.append("Please enter a valid email address.")
        if not password or len(password) < 8:
            errs.append("Password must be at least 8 characters.")
        if password != confirm:
            errs.append("Passwords do not match.")
        if get_user_by_username(username):
            errs.append("Username is already taken.")
        if errs:
            for e in errs:
                st.error(e)
            return
        uid = create_user(username, email, hash_password(password))
        if uid is None:
            st.error("Registration failed. Email may already be in use.")
            return
        st.success("Account created! You can now sign in.")


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD PAGE
# ─────────────────────────────────────────────────────────────────────────────

def page_dashboard():
    inject_css()
    top_nav()

    st.markdown("<div style='padding:2.5rem 3rem 0;'>", unsafe_allow_html=True)

    # ── Header row
    col_title, col_logout = st.columns([8, 1.5])
    with col_title:
        st.markdown(
            """
<div style="margin-bottom:1.5rem;">
    <h2 style="font-family:'Space Grotesk',sans-serif;font-size:2rem;font-weight:800;margin:0 0 0.5rem;
               letter-spacing:-0.02em;" class="text-gradient">My Documents</h2>
    <p style="color:var(--text-muted);margin:0;font-size:1.1rem;font-weight:500;">
        Upload PDFs. Extract tables automatically.
    </p>
</div>
            """,
            unsafe_allow_html=True,
        )
    with col_logout:
        st.markdown("<div style='padding-top:0.8rem;'>", unsafe_allow_html=True)
        if st.button("Sign Out", key="logout_btn", use_container_width=True, type="secondary"):
            for k in ["authenticated", "user_id", "username", "page", "current_upload_id"]:
                st.session_state[k] = (False if k == "authenticated" else None if k != "page" else "auth")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

    # ── Upload section
    st.markdown(
        """
<div style="background:#FFFFFF; border:1px solid #E5E7EB;
     border-radius:var(--radius-lg);padding:1.8rem 2.2rem;margin-bottom:2.5rem;
     box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
    <p style="margin:0 0 0.6rem;font-weight:700;font-family:'Space Grotesk',sans-serif;font-size:1.2rem;color:var(--accent);">
        ⚡  Initialize Upload
    </p>
    <p style="margin:0;font-size:1rem;color:var(--text-muted);">
        Drop your academic result PDF here to start intelligent extraction.
    </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        key="pdf_uploader",
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        _handle_upload(uploaded_file)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Documents list
    uploads = get_user_uploads(st.session_state.user_id)

    if not uploads:
        st.markdown(
            """
<div style="text-align:center;padding:4rem 2rem;border:1.5px dashed var(--border);
     border-radius:var(--radius-lg);background:#F9FAFB;">
    <div style="font-size:3rem;margin-bottom:1rem;">📂</div>
    <p style="color:var(--text-muted);font-size:0.95rem;margin:0;">
        No documents yet. Upload your first PDF above!
    </p>
</div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:1rem;font-weight:500;">
            Showing {len(uploads)} document{'s' if len(uploads) != 1 else ''}
            </p>""",
            unsafe_allow_html=True,
        )

        # Column header row
        st.markdown(
            """
<div style="display:grid;grid-template-columns:3fr 1fr 1fr 1fr 1.5fr;
     gap:0.8rem;padding:0.5rem 1.2rem;margin-bottom:0.4rem;border-bottom:1px solid var(--border);">
    <span style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;
           color:var(--text-muted);font-weight:700;">File Name</span>
    <span style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;
           color:var(--text-muted);font-weight:700;text-align:center;">Pages</span>
    <span style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;
           color:var(--text-muted);font-weight:700;text-align:center;">Tables</span>
    <span style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;
           color:var(--text-muted);font-weight:700;text-align:center;">Size</span>
    <span style="font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em;
           color:var(--text-muted);font-weight:700;">Uploaded</span>
</div>
            """,
            unsafe_allow_html=True,
        )

        for upload in uploads:
            _upload_row(upload)

    st.markdown("</div>", unsafe_allow_html=True)


def _handle_upload(uploaded_file):
    """Parse and store the uploaded PDF."""
    with st.spinner("⚙️  Extracting tables from PDF…"):
        try:
            file_bytes = uploaded_file.read()
            tables, page_count = extract_tables_from_pdf(file_bytes)

            upload_id = save_upload(
                user_id=st.session_state.user_id,
                filename=uploaded_file.name,
                file_size=len(file_bytes),
                pdf_bytes=file_bytes,
                page_count=page_count,
                tables=tables,
            )

            if tables:
                st.success(
                    f"✅ **{uploaded_file.name}** uploaded successfully! "
                    f"Found **{len(tables)}** table(s) across {page_count} page(s)."
                )
            else:
                st.warning(
                    f"⚠️ **{uploaded_file.name}** uploaded, but no tables were detected. "
                    "The PDF may use images instead of selectable text."
                )

            st.rerun()

        except Exception as exc:
            st.error(f"❌ Failed to process PDF: {exc}")


def _upload_row(upload: dict):
    """Render a single file row on the dashboard."""
    uid = upload["id"]
    col_name, col_pages, col_tables, col_size, col_date, col_actions = st.columns(
        [3, 1, 1, 1, 1.5, 1.5]
    )

    with col_name:
        st.markdown(
            f"""
<div style="display:flex;align-items:center;gap:12px;
     padding:0.6rem 0.5rem;height:100%;transition: all 0.2s ease;">
    <span style="font-size:1.1rem;">📄</span>
    <span style="font-size:0.95rem;font-weight:600;color:var(--text);font-family:'Outfit',sans-serif;
           white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:280px;"
          title="{upload['filename']}">{upload['filename']}</span>
</div>
            """,
            unsafe_allow_html=True,
        )

    with col_pages:
        st.markdown(
            f"""<div style="padding:0.6rem 0.5rem;text-align:center;height:100%;
            display:flex;align-items:center;justify-content:center;">
            <span style="font-family:'Outfit',sans-serif;font-weight:600;font-size:0.95rem;color:var(--text);">
            {upload.get('page_count', '—')}</span></div>""",
            unsafe_allow_html=True,
        )

    with col_tables:
        count = upload.get("table_count", 0)
        color = "var(--accent)" if count > 0 else "var(--text-muted)"
        st.markdown(
            f"""<div style="padding:0.6rem 0.5rem;text-align:center;height:100%;
            display:flex;align-items:center;justify-content:center;">
            <span style="font-family:'Outfit',sans-serif;font-weight:700;font-size:0.95rem;color:{color};">
            {count}</span></div>""",
            unsafe_allow_html=True,
        )

    with col_size:
        st.markdown(
            f"""<div style="padding:0.6rem 0.5rem;text-align:center;height:100%;
            display:flex;align-items:center;justify-content:center;">
            <span style="font-family:'Outfit',sans-serif;font-weight:500;font-size:0.85rem;color:var(--text-muted);">
            {fmt_size(upload['file_size'])}</span></div>""",
            unsafe_allow_html=True,
        )

    with col_date:
        st.markdown(
            f"""<div style="padding:0.6rem 0.5rem;height:100%;
            display:flex;align-items:center;justify-content:center;">
            <span style="font-size:0.8rem;font-weight:500;color:var(--text-muted);">
            {fmt_date(upload['upload_date'])}</span></div>""",
            unsafe_allow_html=True,
        )

    with col_actions:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Open", key=f"open_{uid}", use_container_width=True):
                st.session_state.current_upload_id = uid
                st.session_state.page = "file_view"
                st.rerun()
        with c2:
            if st.button("🗑", key=f"del_{uid}", use_container_width=True, type="secondary"):
                delete_upload(uid, st.session_state.user_id)
                st.rerun()

    st.markdown("<hr style='margin:0 !important;'>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# FILE VIEW PAGE
# ─────────────────────────────────────────────────────────────────────────────

def page_file_view():
    inject_css()
    top_nav()

    upload_id = st.session_state.current_upload_id
    user_id = st.session_state.user_id

    # Security & existence check
    metadata = get_upload_metadata(upload_id, user_id)
    if not metadata:
        st.error("Document not found or access denied.")
        if st.button("← Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        return

    st.markdown("<div style='padding:2.5rem 3rem 0;'>", unsafe_allow_html=True)

    # Back button + title
    col_back, col_info = st.columns([1, 7])
    with col_back:
        st.markdown("<div style='padding-top:0.5rem;'>", unsafe_allow_html=True)
        if st.button("← Back", key="back_btn", type="secondary"):
            st.session_state.page = "dashboard"
            st.session_state.current_upload_id = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_info:
        st.markdown(
            f"""
<div style="margin-bottom: 2rem;">
    <h2 style="font-family:'Space Grotesk',sans-serif;font-size:2rem;font-weight:800;margin:0 0 0.4rem;
               letter-spacing:-0.02em;" class="text-gradient">{metadata['filename']}</h2>
    <p style="color:var(--text-muted);font-size:1rem;font-weight:500;margin:0.5rem 0 0;">
        {metadata.get('page_count','—')} pages &nbsp;·&nbsp;
        {metadata.get('table_count','—')} tables &nbsp;·&nbsp;
        {fmt_size(metadata['file_size'])} &nbsp;·&nbsp;
        Uploaded {fmt_date(metadata['upload_date'])}
    </p>
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # ── Two-column layout: left = tables, right = PDF preview
    left_col, right_col = st.columns([5, 4], gap="large")

    with left_col:
        _render_tables_section(upload_id, user_id)

    with right_col:
        _render_pdf_preview(upload_id, user_id, metadata["filename"])

    st.markdown("</div>", unsafe_allow_html=True)


def _render_tables_section(upload_id: int, user_id: int):
    """Render extracted tables with search/filter."""
    tables = get_tables_for_upload(upload_id, user_id)

    st.markdown(
        """
<div style="background:#FFFFFF; border:1px solid #E5E7EB;
     border-radius:var(--radius);padding:1.8rem 2.2rem;margin-bottom:2rem;
     box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
    <p style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.4rem;margin:0 0 0.6rem;color:var(--accent);">
        📊  Extracted Tables
    </p>
    <p style="color:var(--text-muted);font-size:1rem;font-weight:500;margin:0;">
        Search and filter the extracted academic data below.
    </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    if not tables:
        st.markdown(
            """
<div style="text-align:center;padding:3rem;border:1.5px dashed var(--border);
     border-radius:var(--radius);background:#F9FAFB;">
    <div style="font-size:2.5rem;margin-bottom:0.8rem;">🔍</div>
    <p style="color:var(--text-muted);font-size:0.9rem;margin:0;">
        No tables detected in this PDF.
    </p>
</div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Table selector if more than one table
    if len(tables) > 1:
        table_options = [
            f"Table {t['table_index'] + 1}  —  Page {t['page_number']}  ({t['row_count']} rows)"
            for t in tables
        ]
        selected_label = st.selectbox(
            "Select table", table_options, key="table_selector", label_visibility="visible"
        )
        selected_idx = table_options.index(selected_label)
        active_table = tables[selected_idx]
    else:
        active_table = tables[0]

    # Build DataFrame
    df = pd.DataFrame(active_table["data"], columns=active_table["headers"])

    # Stats strip
    st.markdown(
        f"""
<div style="display:flex;gap:1rem;margin-bottom:0.9rem;flex-wrap:wrap;">
    <span style="font-size:0.75rem;color:var(--text-muted);font-weight:500;">
        Page <strong style="color:var(--text)">{active_table['page_number']}</strong>
    </span>
    <span style="color:var(--border);">|</span>
    <span style="font-size:0.75rem;color:var(--text-muted);font-weight:500;">
        <strong style="color:var(--text)">{active_table['row_count']}</strong> rows
    </span>
    <span style="color:var(--border);">|</span>
    <span style="font-size:0.75rem;color:var(--text-muted);font-weight:500;">
        <strong style="color:var(--text)">{active_table['col_count']}</strong> columns
    </span>
</div>
        """,
        unsafe_allow_html=True,
    )

    # Search
    search_query = st.text_input(
        "Search rows",
        key=f"search_{active_table['table_index']}",
        placeholder="🔎  Filter any column…",
        label_visibility="collapsed",
    )

    if search_query:
        mask = df.apply(
            lambda col: col.astype(str).str.contains(search_query, case=False, na=False)
        ).any(axis=1)
        filtered_df = df[mask]
        st.markdown(
            f"<p style='font-size:0.75rem;color:var(--text-muted);margin:0.4rem 0;'>"
            f"Showing {len(filtered_df)} of {len(df)} rows</p>",
            unsafe_allow_html=True,
        )
    else:
        filtered_df = df

    st.dataframe(filtered_df, use_container_width=True, height=400)

    # Download CSV button
    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇  Download CSV",
        data=csv_data,
        file_name=f"table_{active_table['table_index'] + 1}.csv",
        mime="text/csv",
        key=f"dl_{active_table['table_index']}",
        use_container_width=True,
        type="secondary"
    )


def _render_pdf_preview(upload_id: int, user_id: int, filename: str):
    """Embed the original PDF in an iframe."""
    st.markdown(
        """
<div style="background:#FFFFFF; border:1px solid #E5E7EB;
     border-radius:var(--radius);padding:1.8rem 2.2rem;margin-bottom:2rem;
     box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
    <p style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:1.4rem;margin:0 0 0.6rem;color:var(--accent-light);">
        📄  PDF Preview
    </p>
    <p style="color:var(--text-muted);font-size:1rem;font-weight:500;margin:0;">
        Browse the original document.
    </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    with st.spinner("Loading PDF…"):
        pdf_bytes = get_upload_pdf(upload_id, user_id)

    if not pdf_bytes:
        st.error("Could not retrieve the PDF file.")
        return

    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    st.markdown(
        f"""
<div style="border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;background:#FFF;box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
    <iframe
        src="data:application/pdf;base64,{b64}"
        width="100%"
        height="600px"
        style="border:none;display:block;"
        title="{filename}">
    </iframe>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # Download original PDF
    st.download_button(
        label="⬇  Download Original PDF",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
        key=f"dl_pdf_{upload_id}",
        use_container_width=True,
        type="secondary"
    )


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if not st.session_state.authenticated:
        page_auth()
        return

    page = st.session_state.page
    if page == "dashboard":
        page_dashboard()
    elif page == "file_view" and st.session_state.current_upload_id is not None:
        page_file_view()
    else:
        st.session_state.page = "dashboard"
        st.rerun()


if __name__ == "__main__":
    main()

