# 🎓 AcademiQ — Academic Result Analysis System

A full-stack web application built with **Streamlit** that lets users upload academic result PDFs,
automatically extracts tabular data, and provides a rich dashboard to browse, search, and download results.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 **Authentication** | User registration & login with bcrypt password hashing |
| 📤 **PDF Upload** | Upload PDFs containing student result tables |
| 🧠 **Auto Extraction** | Tables extracted automatically with `pdfplumber` |
| 🗂️ **Dashboard** | Lists all uploaded documents with metadata |
| 🔍 **Search & Filter** | Real-time row filtering across any column |
| 📄 **PDF Preview** | Inline PDF viewer alongside the extracted data |
| ⬇️ **Export** | Download individual tables as CSV or original PDFs |
| 🔒 **Data Isolation** | Each user sees only their own documents |

---

## 🏗️ Project Structure

```
academic_system/
├── app.py              ← Main Streamlit application (router + pages + UI)
├── database.py         ← SQLite operations (users, uploads, extracted tables)
├── auth.py             ← bcrypt password hashing & verification
├── pdf_processor.py    ← PDF table extraction using pdfplumber
├── requirements.txt    ← Python dependencies
├── README.md           ← This file
└── academic_results.db ← Auto-created SQLite database on first run
```

---

## 🛠️ Database Schema

```sql
users (id, username, email, password_hash, created_at)
   │
   └─ uploads (id, user_id, filename, file_size, page_count, table_count, pdf_data, upload_date)
                   │
                   └─ extracted_tables (id, upload_id, table_index, page_number,
                                        headers, table_data, row_count, col_count)
```

- **`pdf_data`** — original PDF stored as BLOB in SQLite
- **`headers`** / **`table_data`** — stored as JSON strings; headers are a `list[str]`, data is `list[list[str]]`

---

## 🚀 Setup & Run

### 1. Prerequisites
- Python 3.9+

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
streamlit run app.py
```

The app will open at **http://localhost:8501**

---

## 📋 Requirements

```
streamlit>=1.32.0
pdfplumber>=0.10.0
pandas>=2.0.0
bcrypt>=4.0.0
Pillow>=10.0.0
```

---

## 🔒 Security Notes

- Passwords are hashed with **bcrypt** (cost factor 12) — never stored in plaintext.
- All database queries use **parameterised statements** — no SQL injection.
- Upload access is **always validated** against the logged-in user's `user_id` — users cannot access other users' files.
- Sessions are managed via **Streamlit session state** (server-side).

---

## 💡 PDF Table Extraction Notes

- Extraction uses `pdfplumber` with line-based strategy first, then falls back to text-based strategy.
- PDFs that use **scanned images** (not selectable text) will not have tables extracted.
- Each page is scanned independently — tables spanning across pages are treated as separate tables.
- Different table structures across PDFs are handled automatically.

---

## 🎨 UI Theme

Dark-mode interface with:
- **DM Serif Display** (headings) + **DM Sans** (body) + **DM Mono** (code/numbers)
- Accent color: `#C8F135` (lime-yellow)
- Background: `#0D0F14` (near-black)
- Cards: `#13161E` / `#1B1F2A`
