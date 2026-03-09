"""
database.py
SQLite database operations for Academic Result Analysis System.
Handles users, PDF uploads, and extracted table storage.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "academic_results.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS uploads (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            filename    TEXT    NOT NULL,
            file_size   INTEGER NOT NULL,
            page_count  INTEGER DEFAULT 0,
            table_count INTEGER DEFAULT 0,
            pdf_data    BLOB    NOT NULL,
            upload_date TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS extracted_tables (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_id   INTEGER NOT NULL,
            table_index INTEGER NOT NULL,
            page_number INTEGER NOT NULL DEFAULT 1,
            headers     TEXT    NOT NULL,
            table_data  TEXT    NOT NULL,
            row_count   INTEGER NOT NULL DEFAULT 0,
            col_count   INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (upload_id) REFERENCES uploads(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


# ─── USER OPERATIONS ────────────────────────────────────────────────────────

def create_user(username: str, email: str, password_hash: str) -> Optional[int]:
    """Insert a new user. Returns new user ID or None on conflict."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username.strip(), email.strip().lower(), password_hash),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_username(username: str) -> Optional[Dict]:
    """Fetch a user dict by username."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username.strip(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict]:
    """Fetch a user dict by email."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ─── UPLOAD OPERATIONS ──────────────────────────────────────────────────────

def save_upload(
    user_id: int,
    filename: str,
    file_size: int,
    pdf_bytes: bytes,
    page_count: int,
    tables: List[Dict[str, Any]],
) -> int:
    """
    Store the PDF blob and all its extracted tables.
    If a document with the same filename exists for this user, it replaces the old one.
    Returns the upload ID (existing or new).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Check for existing upload
        existing = cursor.execute(
            "SELECT id FROM uploads WHERE user_id = ? AND filename = ?",
            (user_id, filename)
        ).fetchone()

        if existing:
            upload_id = existing["id"]
            # Update existing upload record
            cursor.execute(
                """UPDATE uploads
                   SET file_size = ?, page_count = ?, table_count = ?, pdf_data = ?, upload_date = datetime('now')
                   WHERE id = ?""",
                (file_size, page_count, len(tables), pdf_bytes, upload_id),
            )
            # Delete old extracted tables to replace them
            cursor.execute("DELETE FROM extracted_tables WHERE upload_id = ?", (upload_id,))
        else:
            # Insert new upload record
            cursor.execute(
                """INSERT INTO uploads
                   (user_id, filename, file_size, page_count, table_count, pdf_data)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, filename, file_size, page_count, len(tables), pdf_bytes),
            )
            upload_id = cursor.lastrowid

        # Insert each extracted table (new or replaced)
        for table in tables:
            cursor.execute(
                """INSERT INTO extracted_tables
                   (upload_id, table_index, page_number, headers, table_data, row_count, col_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    upload_id,
                    table["index"],
                    table["page"],
                    json.dumps(table["headers"]),
                    json.dumps(table["data"]),
                    table["row_count"],
                    table["col_count"],
                ),
            )

        conn.commit()
        return upload_id
    finally:
        conn.close()


def get_user_uploads(user_id: int) -> List[Dict]:
    """Return all uploads for a user (no PDF blob — metadata only)."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, filename, file_size, page_count, table_count, upload_date
           FROM uploads
           WHERE user_id = ?
           ORDER BY upload_date DESC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_upload_metadata(upload_id: int, user_id: int) -> Optional[Dict]:
    """Fetch upload metadata (no blob) and verify it belongs to user_id."""
    conn = get_connection()
    row = conn.execute(
        """SELECT id, filename, file_size, page_count, table_count, upload_date
           FROM uploads WHERE id = ? AND user_id = ?""",
        (upload_id, user_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_upload_pdf(upload_id: int, user_id: int) -> Optional[bytes]:
    """Return the raw PDF bytes for an upload that belongs to user_id."""
    conn = get_connection()
    row = conn.execute(
        "SELECT pdf_data FROM uploads WHERE id = ? AND user_id = ?",
        (upload_id, user_id),
    ).fetchone()
    conn.close()
    return bytes(row["pdf_data"]) if row else None


def get_tables_for_upload(upload_id: int, user_id: int) -> List[Dict]:
    """
    Return all extracted tables for an upload.
    Security: verifies upload belongs to user_id first.
    """
    # Verify ownership
    conn = get_connection()
    owns = conn.execute(
        "SELECT 1 FROM uploads WHERE id = ? AND user_id = ?", (upload_id, user_id)
    ).fetchone()
    if not owns:
        conn.close()
        return []

    rows = conn.execute(
        """SELECT id, table_index, page_number, headers, table_data, row_count, col_count
           FROM extracted_tables
           WHERE upload_id = ?
           ORDER BY table_index""",
        (upload_id,),
    ).fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append(
            {
                "id": r["id"],
                "table_index": r["table_index"],
                "page_number": r["page_number"],
                "headers": json.loads(r["headers"]),
                "data": json.loads(r["table_data"]),
                "row_count": r["row_count"],
                "col_count": r["col_count"],
            }
        )
    return result


def delete_upload(upload_id: int, user_id: int) -> bool:
    """Delete an upload and its tables. Returns True on success."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM uploads WHERE id = ? AND user_id = ?", (upload_id, user_id)
    )
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
