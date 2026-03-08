"""
pdf_processor.py
Extract tabular data from PDF bytes using pdfplumber.
Handles varied table structures across different PDF layouts.
"""

import io
import re
from typing import List, Dict, Any, Tuple

import pdfplumber
import pandas as pd


def _sanitize_header(value: Any, col_index: int) -> str:
    """Convert a raw cell value to a clean column header string."""
    if value is None or str(value).strip() == "":
        return f"Column_{col_index + 1}"
    cleaned = re.sub(r"\s+", " ", str(value).strip())
    return cleaned or f"Column_{col_index + 1}"


def _deduplicate_headers(headers: List[str]) -> List[str]:
    """Ensure no two headers are identical by appending a suffix."""
    seen: Dict[str, int] = {}
    result = []
    for h in headers:
        if h in seen:
            seen[h] += 1
            result.append(f"{h}_{seen[h]}")
        else:
            seen[h] = 0
            result.append(h)
    return result


def _clean_row(row: List[Any], expected_len: int) -> List[str]:
    """Normalise a single row to the expected number of string cells."""
    cleaned = [re.sub(r"\s+", " ", str(c).strip()) if c is not None else "" for c in row]
    # Pad short rows
    while len(cleaned) < expected_len:
        cleaned.append("")
    # Truncate long rows
    return cleaned[:expected_len]


def _is_empty_row(row: List[str]) -> bool:
    return all(cell == "" for cell in row)


def _process_raw_table(raw: List[List[Any]], page_num: int, table_idx: int) -> Dict[str, Any]:
    """
    Convert a raw pdfplumber table (list of lists) into a structured dict.
    Attempts to detect if the first row is a header row.
    """
    if not raw or len(raw) == 0:
        return None

    # Determine max column count across all rows
    max_cols = max(len(row) for row in raw)

    # Use the first non-empty row as headers
    first_row = _clean_row(raw[0], max_cols)
    headers = _deduplicate_headers([_sanitize_header(v, i) for i, v in enumerate(first_row)])

    # Remaining rows as data
    data_rows = []
    for row in raw[1:]:
        cleaned = _clean_row(row, max_cols)
        if not _is_empty_row(cleaned):
            data_rows.append(cleaned)

    if len(data_rows) == 0:
        return None  # Skip tables with no data rows

    return {
        "index": table_idx,
        "page": page_num,
        "headers": headers,
        "data": data_rows,
        "row_count": len(data_rows),
        "col_count": len(headers),
    }


def extract_tables_from_pdf(file_bytes: bytes) -> Tuple[List[Dict[str, Any]], int]:
    """
    Extract all tables from a PDF given as raw bytes.

    Returns:
        (tables, page_count)
        tables — list of dicts, each with keys:
            index, page, headers, data, row_count, col_count
        page_count — total pages in the PDF
    """
    tables: List[Dict[str, Any]] = []
    page_count = 0
    table_idx = 0

    settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "intersection_tolerance": 10,
    }
    fallback_settings = {
        "vertical_strategy": "text",
        "horizontal_strategy": "text",
        "snap_tolerance": 5,
    }

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        page_count = len(pdf.pages)

        for page_num, page in enumerate(pdf.pages, start=1):
            # Try line-based extraction first
            raw_tables = page.extract_tables(settings)

            # If nothing found, try text-based extraction
            if not raw_tables:
                raw_tables = page.extract_tables(fallback_settings)

            for raw in raw_tables:
                if not raw or len(raw) < 2:
                    continue
                processed = _process_raw_table(raw, page_num, table_idx)
                if processed:
                    tables.append(processed)
                    table_idx += 1

    return tables, page_count


def tables_to_dataframes(tables: List[Dict[str, Any]]) -> List[pd.DataFrame]:
    """Convert extracted table dicts into pandas DataFrames."""
    dfs = []
    for t in tables:
        df = pd.DataFrame(t["data"], columns=t["headers"])
        dfs.append(df)
    return dfs
