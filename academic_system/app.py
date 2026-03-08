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
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── Design tokens ───────────────────────────────────────────── */
:root {
    --bg:        #0D0F14;
    --surface:   #13161E;
    --surface2:  #1B1F2A;
    --border:    #252935;
    --accent:    #C8F135;
    --accent2:   #5DFFCB;
    --text:      #E8EAF0;
    --text-muted:#7A8098;
    --danger:    #FF5C5C;
    --success:   #5DFFCB;
    --radius:    12px;
    --radius-lg: 20px;
}

/* ── Reset Streamlit chrome ───────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden !important; }
.stDeployButton { display: none !important; }
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}
section[data-testid="stSidebar"] { display: none !important; }

/* ── Base ────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
}

/* ── Scrollbar ───────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* ── Streamlit element overrides ─────────────────────────────── */
.stTextInput > label,
.stSelectbox > label,
.stFileUploader > label { color: var(--text-muted) !important; font-size: 0.8rem !important; font-weight: 500 !important; letter-spacing: 0.05em; text-transform: uppercase; }

.stTextInput > div > div > input,
.stTextInput > div > div > input:focus {
    background: var(--surface2) !important;
    border: 1.5px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
    padding: 0.6rem 0.9rem !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus { border-color: var(--accent) !important; }

.stButton > button {
    background: var(--accent) !important;
    color: #0D0F14 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 0.55rem 1.4rem !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.02em;
}
.stButton > button:hover {
    background: #deff4a !important;
    transform: translateY(-1px);
    box-shadow: 0 6px 24px rgba(200, 241, 53, 0.25) !important;
}
.stButton > button[kind="secondary"] {
    background: var(--surface2) !important;
    color: var(--text) !important;
    border: 1.5px solid var(--border) !important;
}
.stButton > button[kind="secondary"]:hover {
    background: var(--border) !important;
    box-shadow: none !important;
}

/* File uploader */
.stFileUploader > div {
    background: var(--surface2) !important;
    border: 2px dashed var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text-muted) !important;
}
.stFileUploader > div:hover { border-color: var(--accent) !important; }

/* Dataframe */
.stDataFrame { border: 1.5px solid var(--border) !important; border-radius: var(--radius) !important; }
.stDataFrame table { background: var(--surface) !important; }
.stDataFrame th { background: var(--surface2) !important; color: var(--accent) !important; font-weight: 600 !important; border-bottom: 1.5px solid var(--border) !important; font-family: 'DM Mono', monospace !important; font-size: 0.75rem !important; }
.stDataFrame td { color: var(--text) !important; border-color: var(--border) !important; font-size: 0.85rem !important; }

/* Alert / info boxes */
.stSuccess { background: rgba(93,255,203,0.08) !important; border-left: 3px solid var(--success) !important; border-radius: 0 8px 8px 0 !important; color: var(--success) !important; }
.stError { background: rgba(255,92,92,0.08) !important; border-left: 3px solid var(--danger) !important; border-radius: 0 8px 8px 0 !important; color: var(--danger) !important; }
.stWarning { background: rgba(255,180,0,0.08) !important; border-left: 3px solid #FFB400 !important; border-radius: 0 8px 8px 0 !important; }
.stInfo { background: rgba(200,241,53,0.05) !important; border-left: 3px solid var(--accent) !important; border-radius: 0 8px 8px 0 !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: var(--surface) !important; border-radius: var(--radius) !important; padding: 4px !important; gap: 2px !important; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: var(--text-muted) !important; border-radius: 8px !important; font-weight: 500 !important; }
.stTabs [aria-selected="true"] { background: var(--surface2) !important; color: var(--accent) !important; }
.stTabs [data-baseweb="tab-panel"] { background: transparent !important; padding: 0 !important; }

/* Spinner */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* Divider */
hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

/* Selectbox */
.stSelectbox > div > div {
    background: var(--surface2) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
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
    background: {'{'}var(--surface){'}'};
    border-bottom: 1.5px solid var(--border);
    padding: 0 2.5rem;
    height: 62px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 999;
    backdrop-filter: blur(12px);
">
    <div style="display:flex;align-items:center;gap:10px;">
        <div style="
            width:32px;height:32px;
            background:var(--accent);
            border-radius:8px;
            display:flex;align-items:center;justify-content:center;
            font-size:16px;font-weight:900;color:#0D0F14;
        ">A</div>
        <span style="font-family:'DM Serif Display',serif;font-size:1.25rem;color:var(--text);letter-spacing:-0.02em;">
            {title}
        </span>
    </div>
    <div style="display:flex;align-items:center;gap:1rem;">
        {'<span style="font-size:0.82rem;color:var(--text-muted);">Signed in as&nbsp;<strong style=color:var(--text)>' + (st.session_state.username or "") + '</strong></span>' if show_logout and st.session_state.username else ''}
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def card(content_html: str, padding: str = "1.4rem 1.6rem", extra_style: str = ""):
    st.markdown(
        f"""
<div style="
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: var(--radius-lg);
    padding: {padding};
    {extra_style}
">
    {content_html}
</div>
        """,
        unsafe_allow_html=True,
    )


def badge(text: str, color: str = "var(--accent)", bg: str = "rgba(200,241,53,0.12)"):
    return f"""<span style="
        background:{bg};color:{color};
        border-radius:20px;padding:2px 10px;
        font-size:0.72rem;font-weight:600;letter-spacing:0.04em;
        font-family:'DM Mono',monospace;
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

    # Hero section
    st.markdown(
        """
<div style="
    min-height:100vh;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    padding: 3rem 1rem;
    background: radial-gradient(ellipse 80% 60% at 50% -10%, rgba(200,241,53,0.10) 0%, transparent 70%),
                var(--bg);
">
    <div style="text-align:center;max-width:480px;width:100%;">
        <div style="
            width:56px;height:56px;
            background:var(--accent);
            border-radius:14px;
            display:inline-flex;align-items:center;justify-content:center;
            font-size:26px;font-weight:900;color:#0D0F14;
            margin-bottom:1.4rem;
            box-shadow:0 0 40px rgba(200,241,53,0.35);
        ">A</div>
        <h1 style="
            font-family:'DM Serif Display',serif;
            font-size:2.6rem;
            color:var(--text);
            margin:0 0 0.5rem;
            line-height:1.15;
            letter-spacing:-0.03em;
        ">AcademiQ</h1>
        <p style="color:var(--text-muted);font-size:1rem;margin-bottom:2.5rem;">
            Academic Result Analysis System
        </p>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
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

    st.markdown("<div style='padding:2rem 2.5rem 0;'>", unsafe_allow_html=True)

    # ── Header row
    col_title, col_logout = st.columns([8, 1])
    with col_title:
        st.markdown(
            """
<div style="margin-bottom:0.3rem;">
    <h2 style="font-family:'DM Serif Display',serif;font-size:1.9rem;margin:0;
               color:var(--text);letter-spacing:-0.02em;">My Documents</h2>
    <p style="color:var(--text-muted);margin:0.2rem 0 0;font-size:0.9rem;">
        Upload academic result PDFs and explore extracted data.
    </p>
</div>
            """,
            unsafe_allow_html=True,
        )
    with col_logout:
        st.markdown("<div style='padding-top:0.5rem;'>", unsafe_allow_html=True)
        if st.button("Sign Out", key="logout_btn", use_container_width=True):
            for k in ["authenticated", "user_id", "username", "page", "current_upload_id"]:
                st.session_state[k] = (False if k == "authenticated" else None if k != "page" else "auth")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # ── Upload section
    st.markdown(
        """
<div style="background:var(--surface);border:1.5px solid var(--border);
     border-radius:var(--radius-lg);padding:1.6rem 1.8rem;margin-bottom:2rem;">
    <p style="margin:0 0 0.8rem;font-weight:600;font-size:1rem;color:var(--text);">
        📤  Upload a New PDF
    </p>
    <p style="margin:0;font-size:0.82rem;color:var(--text-muted);">
        Upload a PDF file containing academic result tables.
        Tables are extracted automatically and stored in the database.
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
     border-radius:var(--radius-lg);background:var(--surface);">
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
            f"""<p style="color:var(--text-muted);font-size:0.82rem;margin-bottom:1rem;">
            Showing {len(uploads)} document{'s' if len(uploads) != 1 else ''}
            </p>""",
            unsafe_allow_html=True,
        )

        # Column header row
        st.markdown(
            """
<div style="display:grid;grid-template-columns:3fr 1fr 1fr 1fr 1fr;
     gap:0.8rem;padding:0.5rem 1.2rem;margin-bottom:0.4rem;">
    <span style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;
           color:var(--text-muted);font-weight:600;">File Name</span>
    <span style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;
           color:var(--text-muted);font-weight:600;">Pages</span>
    <span style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;
           color:var(--text-muted);font-weight:600;">Tables</span>
    <span style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;
           color:var(--text-muted);font-weight:600;">Size</span>
    <span style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;
           color:var(--text-muted);font-weight:600;">Uploaded</span>
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
<div style="display:flex;align-items:center;gap:10px;
     padding:0.75rem 1rem;background:var(--surface);
     border:1.5px solid var(--border);border-radius:10px;height:100%;">
    <span style="font-size:1.2rem;">📄</span>
    <span style="font-size:0.88rem;font-weight:500;color:var(--text);
           white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:280px;"
          title="{upload['filename']}">{upload['filename']}</span>
</div>
            """,
            unsafe_allow_html=True,
        )

    with col_pages:
        st.markdown(
            f"""<div style="padding:0.75rem 1rem;background:var(--surface);
            border:1.5px solid var(--border);border-radius:10px;text-align:center;height:100%;
            display:flex;align-items:center;justify-content:center;">
            <span style="font-family:'DM Mono',monospace;font-size:0.9rem;color:var(--text);">
            {upload.get('page_count', '—')}</span></div>""",
            unsafe_allow_html=True,
        )

    with col_tables:
        count = upload.get("table_count", 0)
        color = "var(--accent)" if count > 0 else "var(--text-muted)"
        st.markdown(
            f"""<div style="padding:0.75rem 1rem;background:var(--surface);
            border:1.5px solid var(--border);border-radius:10px;text-align:center;height:100%;
            display:flex;align-items:center;justify-content:center;">
            <span style="font-family:'DM Mono',monospace;font-size:0.9rem;color:{color};">
            {count}</span></div>""",
            unsafe_allow_html=True,
        )

    with col_size:
        st.markdown(
            f"""<div style="padding:0.75rem 1rem;background:var(--surface);
            border:1.5px solid var(--border);border-radius:10px;text-align:center;height:100%;
            display:flex;align-items:center;justify-content:center;">
            <span style="font-family:'DM Mono',monospace;font-size:0.85rem;color:var(--text-muted);">
            {fmt_size(upload['file_size'])}</span></div>""",
            unsafe_allow_html=True,
        )

    with col_date:
        st.markdown(
            f"""<div style="padding:0.75rem 1rem;background:var(--surface);
            border:1.5px solid var(--border);border-radius:10px;height:100%;
            display:flex;align-items:center;justify-content:center;">
            <span style="font-size:0.78rem;color:var(--text-muted);">
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
            if st.button("🗑", key=f"del_{uid}", use_container_width=True):
                delete_upload(uid, st.session_state.user_id)
                st.rerun()


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

    st.markdown("<div style='padding:1.5rem 2.5rem 0;'>", unsafe_allow_html=True)

    # Back button + title
    col_back, col_info = st.columns([1, 7])
    with col_back:
        if st.button("← Dashboard", key="back_btn"):
            st.session_state.page = "dashboard"
            st.session_state.current_upload_id = None
            st.rerun()

    with col_info:
        st.markdown(
            f"""
<div>
    <h2 style="font-family:'DM Serif Display',serif;font-size:1.7rem;margin:0;
               color:var(--text);letter-spacing:-0.02em;">{metadata['filename']}</h2>
    <p style="color:var(--text-muted);font-size:0.82rem;margin:0.3rem 0 0;">
        {metadata.get('page_count','—')} pages &nbsp;·&nbsp;
        {metadata.get('table_count','—')} tables &nbsp;·&nbsp;
        {fmt_size(metadata['file_size'])} &nbsp;·&nbsp;
        Uploaded {fmt_date(metadata['upload_date'])}
    </p>
</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

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
<div style="background:var(--surface);border:1.5px solid var(--border);
     border-radius:var(--radius-lg);padding:1.4rem 1.6rem;margin-bottom:1rem;">
    <p style="font-family:'DM Serif Display',serif;font-size:1.2rem;margin:0 0 0.3rem;color:var(--text);">
        📊  Extracted Tables
    </p>
    <p style="color:var(--text-muted);font-size:0.82rem;margin:0;">
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
     border-radius:var(--radius-lg);background:var(--surface);">
    <div style="font-size:2.5rem;margin-bottom:0.8rem;">🔍</div>
    <p style="color:var(--text-muted);font-size:0.9rem;margin:0;">
        No tables detected in this PDF.<br>
        The file may use image-based or scanned content.
    </p>
</div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Table selector if more than one table
    if len(tables) > 1:
        table_options = [
            f"Table {t['table_index'] + 1}  —  Page {t['page_number']}  ({t['row_count']} rows × {t['col_count']} cols)"
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
    <span style="font-size:0.78rem;color:var(--text-muted);">
        Page <strong style="color:var(--text)">{active_table['page_number']}</strong>
    </span>
    <span style="color:var(--border);">|</span>
    <span style="font-size:0.78rem;color:var(--text-muted);">
        <strong style="color:var(--text)">{active_table['row_count']}</strong> rows
    </span>
    <span style="color:var(--border);">|</span>
    <span style="font-size:0.78rem;color:var(--text-muted);">
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
            f"<p style='font-size:0.78rem;color:var(--text-muted);margin:0.4rem 0;'>"
            f"Showing {len(filtered_df)} of {len(df)} rows</p>",
            unsafe_allow_html=True,
        )
    else:
        filtered_df = df

    st.dataframe(filtered_df, use_container_width=True, height=420)

    # Download CSV button
    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇  Download as CSV",
        data=csv_data,
        file_name=f"table_{active_table['table_index'] + 1}.csv",
        mime="text/csv",
        key=f"dl_{active_table['table_index']}",
    )


def _render_pdf_preview(upload_id: int, user_id: int, filename: str):
    """Embed the original PDF in an iframe."""
    st.markdown(
        """
<div style="background:var(--surface);border:1.5px solid var(--border);
     border-radius:var(--radius-lg);padding:1.4rem 1.6rem;margin-bottom:1rem;">
    <p style="font-family:'DM Serif Display',serif;font-size:1.2rem;margin:0 0 0.3rem;color:var(--text);">
        📄  PDF Preview
    </p>
    <p style="color:var(--text-muted);font-size:0.82rem;margin:0;">
        Original document — scroll to browse pages.
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
<div style="border:1.5px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;background:#fff;">
    <iframe
        src="data:application/pdf;base64,{b64}"
        width="100%"
        height="620px"
        style="border:none;display:block;"
        title="{filename}">
        <p style="padding:1rem;font-size:0.85rem;">
            Your browser doesn't support inline PDF viewing.
            Please download the file instead.
        </p>
    </iframe>
</div>
        """,
        unsafe_allow_html=True,
    )

    # Download original PDF
    st.download_button(
        label="⬇  Download Original PDF",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
        key=f"dl_pdf_{upload_id}",
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

