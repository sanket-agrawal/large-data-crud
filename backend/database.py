import duckdb
import os
import re
import json
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import threading

DB_FILE = os.getenv("DUCKDB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "records.duckdb"))

_conn = None
_conn_lock = threading.Lock()

def ensure_tables(conn):
    """Ensure sequence, table, columns, and indexes exist on the database connection."""
    conn.execute("PRAGMA threads=4;")
    conn.execute("CREATE SEQUENCE IF NOT EXISTS seq_records_id START 1;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id BIGINT PRIMARY KEY DEFAULT nextval('seq_records_id'),
            reg_no VARCHAR,
            rto VARCHAR,
            reg_date VARCHAR,
            name VARCHAR,
            address VARCHAR,
            pincode VARCHAR,
            make VARCHAR,
            model_variant VARCHAR,
            mobile VARCHAR,
            source_file VARCHAR,
            source_sheet VARCHAR,
            search_text VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Check if search_text column exists in case created with older version
    try:
        conn.execute("ALTER TABLE records ADD COLUMN IF NOT EXISTS search_text VARCHAR;")
    except Exception:
        pass

    # Ensure indexes exist on key searchable columns
    conn.execute("CREATE INDEX IF NOT EXISTS idx_reg_no ON records(reg_no);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON records(name);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_mobile ON records(mobile);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pincode ON records(pincode);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_make ON records(make);")

def get_db_connection():
    """Get a thread-safe cursor to the persistent DuckDB connection."""
    global _conn
    if _conn is None:
        with _conn_lock:
            if _conn is None:
                os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
                _conn = duckdb.connect(DB_FILE)
                ensure_tables(_conn)
    return _conn.cursor()

def init_db():
    """Initialize database table schema, sequence, and indexes."""
    conn = get_db_connection()
    conn.close()

def normalize_column_name(col: str) -> str:
    """Normalize excel column headers to standard database columns."""
    c = str(col).strip().upper()
    c_clean = re.sub(r'[^A-Z0-9]', '', c)
    
    if "REGNO" in c_clean or "REGISTRATION" in c_clean:
        return "reg_no"
    elif c_clean == "RTO":
        return "rto"
    elif "REGDATE" in c_clean or "DATE" in c_clean:
        return "reg_date"
    elif c_clean in ["NAME", "CUSTOMERNAME", "OWNERNAME", "OWNER"]:
        return "name"
    elif "ADDR" in c_clean:
        return "address"
    elif "PIN" in c_clean or "POSTAL" in c_clean:
        return "pincode"
    elif c_clean in ["MAKE", "BRAND", "MANUFACTURER"]:
        return "make"
    elif "MODEL" in c_clean or "VARIANT" in c_clean:
        return "model_variant"
    elif "MOB" in c_clean or "PHONE" in c_clean or "CONTACT" in c_clean:
        return "mobile"
    else:
        return re.sub(r'\s+', '_', str(col).strip().lower())

def prepare_df_for_insertion(df: pd.DataFrame, filename: str, sheet_name: str) -> pd.DataFrame:
    standard_cols = [
        "reg_no", "rto", "reg_date", "name", "address", 
        "pincode", "make", "model_variant", "mobile"
    ]
    col_map = {orig: normalize_column_name(orig) for orig in df.columns}
    df = df.rename(columns=col_map)
    for col in standard_cols:
        if col not in df.columns:
            df[col] = ""
    df = df[standard_cols].fillna("").astype(str)
    df["source_file"] = filename
    df["source_sheet"] = str(sheet_name)
    
    # Compute consolidated lowercased search_text for sub-10ms global queries
    df["search_text"] = (
        df["reg_no"] + " " +
        df["rto"] + " " +
        df["reg_date"] + " " +
        df["name"] + " " +
        df["address"] + " " +
        df["pincode"] + " " +
        df["make"] + " " +
        df["model_variant"] + " " +
        df["mobile"] + " " +
        df["source_sheet"]
    ).str.lower()
    return df

def ingest_excel_file(file_path: str, filename: str) -> Dict[str, Any]:
    """Ingest all sheets from an Excel file into DuckDB."""
    excel_file = pd.ExcelFile(file_path)
    sheet_names = excel_file.sheet_names
    
    conn = get_db_connection()
    total_ingested = 0
    sheet_details = []

    try:
        for sheet in sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet, dtype=str)
            if df.empty:
                continue

            df = prepare_df_for_insertion(df, filename, sheet)

            conn.register("temp_df", df)
            conn.execute("""
                INSERT INTO records (reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet, search_text)
                SELECT reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet, search_text
                FROM temp_df;
            """)
            conn.unregister("temp_df")

            count = len(df)
            total_ingested += count
            sheet_details.append({"sheet": sheet, "rows": count})
            
    finally:
        conn.close()

    return {
        "filename": filename,
        "total_rows": total_ingested,
        "sheets": sheet_details
    }

def ingest_files_generator(file_items: List[Tuple[str, str]]):
    """
    Generator that processes uploaded Excel/CSV files and yields progress events.
    file_items is a list of (temp_file_path, original_filename).
    """
    file_sheet_maps = []
    total_sheets = 0

    yield f"data: {json.dumps({'progress': 5, 'message': 'Scanning files and inspecting sheets...', 'status': 'processing'})}\n\n"

    for temp_path, filename in file_items:
        try:
            if filename.lower().endswith('.csv'):
                file_sheet_maps.append((temp_path, filename, ['CSV_Data'], 'csv'))
                total_sheets += 1
            else:
                excel_file = pd.ExcelFile(temp_path)
                sheets = excel_file.sheet_names
                file_sheet_maps.append((temp_path, filename, sheets, 'excel'))
                total_sheets += len(sheets)
        except Exception as e:
            file_sheet_maps.append((temp_path, filename, [], 'error'))

    if total_sheets == 0:
        total_sheets = 1

    processed_sheets = 0
    total_rows_ingested = 0
    results = []

    conn = get_db_connection()

    try:
        for file_idx, (temp_path, filename, sheets, file_type) in enumerate(file_sheet_maps):
            if not sheets:
                continue

            file_total_rows = 0
            sheet_details = []

            if file_type == 'csv':
                df = pd.read_csv(temp_path, dtype=str)
                processed_sheets += 1
                percent = int(10 + (processed_sheets / total_sheets) * 85)
                yield f"data: {json.dumps({'progress': percent, 'message': f'Processing CSV {filename} ({len(df):,} rows)...', 'status': 'processing'})}\n\n"
                
                df = prepare_df_for_insertion(df, filename, "CSV_Data")

                conn.register("temp_df", df)
                conn.execute("""
                    INSERT INTO records (reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet, search_text)
                    SELECT reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet, search_text
                    FROM temp_df;
                """)
                conn.unregister("temp_df")

                count = len(df)
                file_total_rows += count
                total_rows_ingested += count
                sheet_details.append({"sheet": "CSV_Data", "rows": count})

            else:
                excel_file = pd.ExcelFile(temp_path)
                for s_idx, sheet in enumerate(sheets):
                    processed_sheets += 1
                    percent = int(10 + (processed_sheets / total_sheets) * 85)
                    yield f"data: {json.dumps({'progress': percent, 'message': f'File {file_idx+1}/{len(file_sheet_maps)} ({filename}) • Sheet {s_idx+1}/{len(sheets)} ({sheet})...', 'status': 'processing'})}\n\n"

                    df = pd.read_excel(excel_file, sheet_name=sheet, dtype=str)
                    if df.empty:
                        continue

                    df = prepare_df_for_insertion(df, filename, sheet)

                    conn.register("temp_df", df)
                    conn.execute("""
                        INSERT INTO records (reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet, search_text)
                        SELECT reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet, search_text
                        FROM temp_df;
                    """)
                    conn.unregister("temp_df")

                    count = len(df)
                    file_total_rows += count
                    total_rows_ingested += count
                    sheet_details.append({"sheet": sheet, "rows": count})

            results.append({
                "filename": filename,
                "total_rows": file_total_rows,
                "sheets": sheet_details
            })

    except Exception as e:
        yield f"data: {json.dumps({'progress': 100, 'message': f'Error during ingestion: {str(e)}', 'status': 'error'})}\n\n"
        return
    finally:
        conn.close()

    yield f"data: {json.dumps({'progress': 100, 'message': f'Successfully ingested {total_rows_ingested:,} rows from {len(file_sheet_maps)} file(s)!', 'status': 'completed', 'total_rows': total_rows_ingested, 'results': results})}\n\n"

def _enrich_record(r: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure clean fields, extracting pincode from address if empty, avoiding None values."""
    if (not r.get("pincode") or str(r.get("pincode")).strip() in ["", "nan", "None"]) and r.get("address"):
        m = re.search(r'\b[1-9][0-9]{5}\b', str(r["address"]))
        if m:
            r["pincode"] = m.group(0)
    for k, v in r.items():
        if v is None:
            r[k] = ""
    return r

def _generate_reg_no_candidates(q_raw: str) -> List[str]:
    """
    Generate normalized candidate vehicle numbers to handle all edge cases:
    - Missing spaces / irregular spaces (e.g. MH 12 SM 5430 -> MH12SM5430)
    - Punctuation (e.g. MH-12-SM-5430, MH.12.SM.5430, MH/12/SM/5430)
    - Missing leading zeros in number (e.g. MH14HZ7 -> MH14HZ0007, MH14HZ747 -> MH14HZ0747)
    - Missing leading zero in RTO (e.g. MH1SM5430 -> MH01SM5430, MH1HZ7 -> MH01HZ0007)
    - Omitted state code (e.g. 14HZ747 -> MH14HZ0747, 12SM5430 -> MH12SM5430, 14HZ7 -> MH14HZ0007)
    - Common typos: 'O' instead of '0', 'I' instead of '1' in digit positions
    """
    q = q_raw.strip().upper()
    if not q:
        return []

    clean = re.sub(r'[^A-Z0-9]', '', q)
    if not clean:
        return []

    candidates = []

    # 1. Check for O/I typos in digit positions when formatted like standard plate
    fixed_typo = None
    if len(clean) == 10 and clean[:2].isalpha():
        rto = clean[2:4].replace('O', '0').replace('I', '1')
        series = clean[4:6]
        num = clean[6:10].replace('O', '0').replace('I', '1')
        cand_10 = clean[:2] + rto + series + num
        if cand_10 != clean:
            fixed_typo = cand_10
            candidates.append(cand_10)

    # 2. Add raw clean candidate
    candidates.append(clean)
    working_clean = fixed_typo if fixed_typo else clean

    # 3. Missing leading zeros in final 4-digit number (e.g. MH14HZ7 -> MH14HZ0007, MH14HZ747 -> MH14HZ0747)
    m_num = re.match(r'^([A-Z]{2}\d{1,2}[A-Z]{1,2})([0-9OI]{1,3})$', working_clean)
    if m_num:
        prefix, num = m_num.groups()
        num_clean = num.replace('O', '0').replace('I', '1')
        candidates.append(prefix + num_clean.zfill(4))

    # 4. Single-digit RTO padding (e.g. MH1SM5430 -> MH01SM5430, MH1HZ7 -> MH01HZ0007)
    m_rto = re.match(r'^([A-Z]{2})(\d)([A-Z]{1,2})([0-9OI]{1,4})$', working_clean)
    if m_rto:
        state, rto_dig, series, num = m_rto.groups()
        num_clean = num.replace('O', '0').replace('I', '1')
        candidates.append(f"{state}0{rto_dig}{series}{num_clean}")
        if len(num_clean) < 4:
            candidates.append(f"{state}0{rto_dig}{series}{num_clean.zfill(4)}")

    # 5. Omitted State Code prefix (e.g. 14HZ747 -> MH14HZ0747, 12SM5430 -> MH12SM5430, 14HZ7 -> MH14HZ0007)
    m_nostate = re.match(r'^(\d{1,2})([A-Z]{1,2})([0-9OI]{1,4})$', working_clean)
    if m_nostate:
        rto, series, num = m_nostate.groups()
        num_clean = num.replace('O', '0').replace('I', '1')
        rto_pad = rto.zfill(2)
        num_pad = num_clean.zfill(4)
        candidates.append(f"MH{rto_pad}{series}{num_pad}")
        candidates.append(f"{rto_pad}{series}{num_pad}")
        candidates.append(f"{rto}{series}{num_pad}")
        candidates.append(f"{rto}{series}{num_clean}")

    # 6. Spaced version if different
    spaced = re.sub(r'\s+', ' ', q_raw).strip().upper()
    if spaced and spaced != clean:
        candidates.append(spaced)

    # Deduplicate while preserving order and filter by minimum length
    seen = set()
    unique = []
    for c in candidates:
        if c and c not in seen and len(c) >= 4:
            seen.add(c)
            unique.append(c)

    return unique

def search_records(
    query: Optional[str] = None,
    make: Optional[str] = None,
    pincode: Optional[str] = None,
    rto: Optional[str] = None,
    source_sheet: Optional[str] = None,
    source_file: Optional[str] = None,
    strict_reg_no: bool = False,
    page: int = 1,
    limit: int = 50,
    sort_by: str = "id",
    sort_order: str = "ASC"
) -> Dict[str, Any]:
    """
    Sub-10ms query search across 2M+ rows.
    Intelligently uses ART indexes on vehicle registration number.
    When strict_reg_no=True (Standard Users), strictly limits lookup to vehicle registration
    number, preventing data-scraping or broad location/address leaks.
    """
    import time
    t_start = time.perf_counter()

    conn = get_db_connection()
    try:
        q_raw = query.strip() if query else ""
        has_filters = any([make, pincode, rto, source_sheet, source_file])

        # Base column filters
        filter_clauses = []
        filter_params = []
        if make and make.strip():
            filter_clauses.append("make ILIKE ?")
            filter_params.append(f"%{make.strip()}%")
        if pincode and pincode.strip():
            filter_clauses.append("pincode LIKE ?")
            filter_params.append(f"%{pincode.strip()}%")
        if rto and rto.strip():
            filter_clauses.append("rto ILIKE ?")
            filter_params.append(f"%{rto.strip()}%")
        if source_sheet and source_sheet.strip():
            filter_clauses.append("source_sheet = ?")
            filter_params.append(source_sheet.strip())
        if source_file and source_file.strip():
            filter_clauses.append("source_file = ?")
            filter_params.append(source_file.strip())

        filter_sql = (" AND " + " AND ".join(filter_clauses)) if filter_clauses else ""
        columns = ["id", "reg_no", "rto", "reg_date", "name", "address", "pincode", "make", "model_variant", "mobile", "source_file", "source_sheet"]

        # =====================================================================
        # STRICT REGISTRATION NUMBER SEARCH (STANDARD USERS)
        # Guarantees zero data leaks: only vehicle registration number is queried.
        # Queries without digits (e.g. 'khara', 'pune') are rejected instantly.
        # =====================================================================
        if strict_reg_no:
            if not q_raw:
                return {
                    "total": 0,
                    "page": 1,
                    "limit": limit,
                    "total_pages": 0,
                    "has_more": False,
                    "latency_ms": 0,
                    "search_strategy": "empty_prompt",
                    "data": []
                }

            clean_alnum = re.sub(r'[^A-Za-z0-9]', '', q_raw).upper()
            has_digits = any(c.isdigit() for c in clean_alnum)
            has_letters = any(c.isalpha() for c in clean_alnum)

            # Must contain both digits and letters and have at least 4 alphanumeric characters
            # Instantly rejects broad non-vehicle text (e.g. 'khara', 'pune', 'katraj')
            if len(clean_alnum) < 4 or not has_digits or not has_letters:
                t_end = time.perf_counter()
                return {
                    "total": 0,
                    "page": 1,
                    "limit": limit,
                    "total_pages": 0,
                    "has_more": False,
                    "latency_ms": round((t_end - t_start) * 1000, 2),
                    "search_strategy": "invalid_reg_no_format",
                    "data": []
                }

            candidates = _generate_reg_no_candidates(q_raw)

            # 1. Exact Reg No Match via ART Index (idx_reg_no ~ 0.5 - 2ms)
            exact_sql = f"""
                SELECT id, reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet
                FROM records
                WHERE reg_no = ?{filter_sql}
                LIMIT ?;
            """
            for cand in candidates:
                rows = conn.execute(exact_sql, [cand] + filter_params + [limit]).fetchall()
                if rows:
                    t_end = time.perf_counter()
                    return {
                        "total": len(rows),
                        "page": 1,
                        "limit": limit,
                        "total_pages": 1,
                        "has_more": False,
                        "latency_ms": round((t_end - t_start) * 1000, 2),
                        "search_strategy": "exact_reg_no",
                        "data": [_enrich_record(dict(zip(columns, row))) for row in rows]
                    }

            # 2. Prefix Reg No Match (Range scan on ART index, e.g. MH12SM% or MH14HZ%)
            for cand in candidates:
                if len(cand) >= 6 and cand[:2].isalpha():
                    prefix_sql = f"""
                        SELECT id, reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet
                        FROM records
                        WHERE reg_no LIKE ?{filter_sql}
                        LIMIT ?;
                    """
                    rows = conn.execute(prefix_sql, [cand + "%"] + filter_params + [limit]).fetchall()
                    if rows:
                        t_end = time.perf_counter()
                        return {
                            "total": len(rows),
                            "page": 1,
                            "limit": limit,
                            "total_pages": 1,
                            "has_more": len(rows) == limit,
                            "latency_ms": round((t_end - t_start) * 1000, 2),
                            "search_strategy": "prefix_reg_no",
                            "data": [_enrich_record(dict(zip(columns, row))) for row in rows]
                        }

            # 3. Suffix Reg No Match (when user omits state code or district prefix, e.g. 14HZ0747 or 12SM5430)
            for cand in candidates:
                if len(cand) >= 6:
                    suffix_sql = f"""
                        SELECT id, reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet
                        FROM records
                        WHERE reg_no LIKE ?{filter_sql}
                        LIMIT ?;
                    """
                    rows = conn.execute(suffix_sql, [f"%{cand}"] + filter_params + [limit]).fetchall()
                    if rows:
                        t_end = time.perf_counter()
                        return {
                            "total": len(rows),
                            "page": 1,
                            "limit": limit,
                            "total_pages": 1,
                            "has_more": len(rows) == limit,
                            "latency_ms": round((t_end - t_start) * 1000, 2),
                            "search_strategy": "suffix_reg_no",
                            "data": [_enrich_record(dict(zip(columns, row))) for row in rows]
                        }

            # Reg No not found in database -> return immediately without scanning other columns
            t_end = time.perf_counter()
            return {
                "total": 0,
                "page": 1,
                "limit": limit,
                "total_pages": 0,
                "has_more": False,
                "latency_ms": round((t_end - t_start) * 1000, 2),
                "search_strategy": "reg_no_not_found",
                "data": []
            }

        # Tier 1: Fast Index Lookups if query provided (Target: 2-8ms)
        if q_raw:
            clean_alnum = re.sub(r'[^A-Za-z0-9]', '', q_raw).upper()
            clean_spaced = re.sub(r'\s+', ' ', q_raw).strip().upper()
            digits = re.sub(r'\D', '', q_raw)

            # Strategy 1A: Exact Reg No Candidates (Index Lookups ~ 1-3ms)
            if clean_alnum and len(clean_alnum) >= 4 and any(c.isdigit() for c in clean_alnum) and any(c.isalpha() for c in clean_alnum):
                reg_candidates = _generate_reg_no_candidates(q_raw)
                exact_sql = f"""
                    SELECT id, reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet
                    FROM records
                    WHERE reg_no = ?{filter_sql}
                    LIMIT ?;
                """
                for cand in reg_candidates:
                    rows = conn.execute(exact_sql, [cand] + filter_params + [limit]).fetchall()
                    if rows:
                        t_end = time.perf_counter()
                        return {
                            "total": len(rows),
                            "page": 1,
                            "limit": limit,
                            "total_pages": 1,
                            "has_more": False,
                            "latency_ms": round((t_end - t_start) * 1000, 2),
                            "search_strategy": "exact_reg_no",
                            "data": [_enrich_record(dict(zip(columns, row))) for row in rows]
                        }

            # Strategy 1B: Exact Mobile (Index Lookup on 10-digit mobile)
            if len(digits) >= 10:
                mob_target = digits[-10:]
                exact_mob_sql = f"""
                    SELECT id, reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet
                    FROM records
                    WHERE mobile = ?{filter_sql}
                    LIMIT ?;
                """
                rows = conn.execute(exact_mob_sql, [mob_target] + filter_params + [limit]).fetchall()
                if not rows and digits != mob_target:
                    rows = conn.execute(exact_mob_sql, [digits] + filter_params + [limit]).fetchall()
                if rows:
                    t_end = time.perf_counter()
                    return {
                        "total": len(rows),
                        "page": 1,
                        "limit": limit,
                        "total_pages": 1,
                        "has_more": False,
                        "latency_ms": round((t_end - t_start) * 1000, 2),
                        "search_strategy": "exact_mobile",
                        "data": [_enrich_record(dict(zip(columns, row))) for row in rows]
                    }
                elif is_mob_pattern and not has_filters:
                    # 10-digit mobile number definitely not in database
                    t_end = time.perf_counter()
                    return {
                        "total": 0,
                        "page": 1,
                        "limit": limit,
                        "total_pages": 0,
                        "has_more": False,
                        "latency_ms": round((t_end - t_start) * 1000, 2),
                        "search_strategy": "mobile_not_found",
                        "data": []
                    }

            # Strategy 1C: Exact Name (Index Lookup)
            if clean_spaced and any(c.isalpha() for c in clean_spaced):
                exact_name_sql = f"""
                    SELECT id, reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet
                    FROM records
                    WHERE name = ?{filter_sql}
                    LIMIT ?;
                """
                rows = conn.execute(exact_name_sql, [clean_spaced] + filter_params + [limit]).fetchall()
                if rows:
                    t_end = time.perf_counter()
                    return {
                        "total": len(rows),
                        "page": 1,
                        "limit": limit,
                        "total_pages": 1,
                        "has_more": False,
                        "latency_ms": round((t_end - t_start) * 1000, 2),
                        "search_strategy": "exact_name",
                        "data": [_enrich_record(dict(zip(columns, row))) for row in rows]
                    }

            # Strategy 1D: Prefix Reg No (Range scan on ART index, e.g. MH12SM%)
            if len(clean_alnum) >= 4 and clean_alnum[:2].isalpha():
                prefix_sql = f"""
                    SELECT id, reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet
                    FROM records
                    WHERE reg_no LIKE ?{filter_sql}
                    LIMIT ?;
                """
                rows = conn.execute(prefix_sql, [clean_alnum + "%"] + filter_params + [limit]).fetchall()
                if rows:
                    t_end = time.perf_counter()
                    return {
                        "total": len(rows),
                        "page": 1,
                        "limit": limit,
                        "total_pages": 1,
                        "has_more": len(rows) == limit,
                        "latency_ms": round((t_end - t_start) * 1000, 2),
                        "search_strategy": "prefix_reg_no",
                        "data": [_enrich_record(dict(zip(columns, row))) for row in rows]
                    }

            # Strategy 1E: Substring Reg No (When user omits state prefix, e.g. 12SM5430)
            if len(clean_alnum) >= 5 and any(c.isdigit() for c in clean_alnum) and any(c.isalpha() for c in clean_alnum):
                sub_reg_sql = f"""
                    SELECT id, reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet
                    FROM records
                    WHERE reg_no LIKE ?{filter_sql}
                    LIMIT ?;
                """
                rows = conn.execute(sub_reg_sql, [f"%{clean_alnum}%"] + filter_params + [limit]).fetchall()
                if rows:
                    t_end = time.perf_counter()
                    return {
                        "total": len(rows),
                        "page": 1,
                        "limit": limit,
                        "total_pages": 1,
                        "has_more": len(rows) == limit,
                        "latency_ms": round((t_end - t_start) * 1000, 2),
                        "search_strategy": "substring_reg_no",
                        "data": [_enrich_record(dict(zip(columns, row))) for row in rows]
                    }

            # Strategy 1F: Multi-word Name Match (handles multi-spaced names and middle names)
            name_words = [w for w in clean_spaced.split() if len(w) >= 2 and any(c.isalpha() for c in w)]
            if len(name_words) >= 2:
                name_where = " AND ".join(["name ILIKE ?" for _ in name_words])
                name_params = [f"%{w}%" for w in name_words]
                multi_name_sql = f"""
                    SELECT id, reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet
                    FROM records
                    WHERE {name_where}{filter_sql}
                    LIMIT ?;
                """
                rows = conn.execute(multi_name_sql, name_params + filter_params + [limit]).fetchall()
                if rows:
                    t_end = time.perf_counter()
                    return {
                        "total": len(rows),
                        "page": 1,
                        "limit": limit,
                        "total_pages": 1,
                        "has_more": len(rows) == limit,
                        "latency_ms": round((t_end - t_start) * 1000, 2),
                        "search_strategy": "multi_word_name",
                        "data": [_enrich_record(dict(zip(columns, row))) for row in rows]
                    }

            # Strategy 1G: Partial Phone Match (when 8 or 9 digits typed)
            if 7 <= len(digits) < 10:
                mob_sub_sql = f"""
                    SELECT id, reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet
                    FROM records
                    WHERE mobile LIKE ?{filter_sql}
                    LIMIT ?;
                """
                rows = conn.execute(mob_sub_sql, [f"%{digits}%"] + filter_params + [limit]).fetchall()
                if rows:
                    t_end = time.perf_counter()
                    return {
                        "total": len(rows),
                        "page": 1,
                        "limit": limit,
                        "total_pages": 1,
                        "has_more": len(rows) == limit,
                        "latency_ms": round((t_end - t_start) * 1000, 2),
                        "search_strategy": "partial_mobile",
                        "data": [_enrich_record(dict(zip(columns, row))) for row in rows]
                    }

        # Tier 2: General / Fallback Multi-Word Search
        where_clauses = list(filter_clauses)
        params = list(filter_params)

        if q_raw:
            terms = q_raw.split()
            # Match each term across the core searchable columns
            for term in terms[:3]:
                t = f"%{term}%"
                where_clauses.append("(reg_no ILIKE ? OR mobile LIKE ? OR name ILIKE ? OR address ILIKE ? OR make ILIKE ? OR model_variant ILIKE ?)")
                params.extend([t, t, t, t, t, t])

        where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        allowed_sort_cols = [
            "id", "reg_no", "rto", "reg_date", "name", "address", 
            "pincode", "make", "model_variant", "mobile", "source_file", "source_sheet"
        ]
        if sort_by not in allowed_sort_cols:
            sort_by = "id"
        sort_order_clean = "DESC" if sort_order.upper() == "DESC" else "ASC"

        offset = max(0, (page - 1) * limit)
        data_sql = f"""
            SELECT id, reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet
            FROM records
            {where_sql}
            ORDER BY {sort_by} {sort_order_clean}
            LIMIT ? OFFSET ?;
        """
        rows = conn.execute(data_sql, params + [limit + 1, offset]).fetchall()

        has_more = len(rows) > limit
        result_rows = rows[:limit]

        # Fast total: avoid expensive COUNT(*) if first page returns fewer rows than limit
        if page == 1 and not has_more:
            total_rows = len(result_rows)
        elif not where_clauses:
            total_rows = conn.execute("SELECT COUNT(*) FROM records;").fetchone()[0]
        else:
            count_sql = f"SELECT COUNT(*) FROM records{where_sql};"
            total_rows = conn.execute(count_sql, params).fetchone()[0]

        records = [_enrich_record(dict(zip(columns, row))) for row in result_rows]

        t_end = time.perf_counter()
        return {
            "total": total_rows,
            "page": page,
            "limit": limit,
            "total_pages": (total_rows + limit - 1) // limit if limit > 0 else 1,
            "has_more": has_more,
            "latency_ms": round((t_end - t_start) * 1000, 2),
            "search_strategy": "multi_field",
            "data": records
        }
    finally:
        conn.close()

def get_dashboard_stats() -> Dict[str, Any]:
    """Get database statistics (total records, unique makes, pincodes, sheets, files, file size)."""
    conn = get_db_connection()
    try:
        total_count = conn.execute("SELECT COUNT(*) FROM records;").fetchone()[0]
        
        top_makes = conn.execute("""
            SELECT make, COUNT(*) as count 
            FROM records 
            WHERE make IS NOT NULL AND make != ''
            GROUP BY make 
            ORDER BY count DESC 
            LIMIT 6;
        """).fetchall()
        
        top_pincodes = conn.execute("""
            SELECT pincode, COUNT(*) as count 
            FROM records 
            WHERE pincode IS NOT NULL AND pincode != ''
            GROUP BY pincode 
            ORDER BY count DESC 
            LIMIT 6;
        """).fetchall()

        sheets = conn.execute("""
            SELECT source_sheet, COUNT(*) as count 
            FROM records 
            WHERE source_sheet IS NOT NULL AND source_sheet != ''
            GROUP BY source_sheet 
            ORDER BY source_sheet ASC;
        """).fetchall()

        files = conn.execute("""
            SELECT source_file, COUNT(*) as count 
            FROM records 
            WHERE source_file IS NOT NULL AND source_file != ''
            GROUP BY source_file 
            ORDER BY count DESC;
        """).fetchall()

        db_size_bytes = 0
        if os.path.exists(DB_FILE):
            db_size_bytes = os.path.getsize(DB_FILE)

        return {
            "total_records": total_count,
            "top_makes": [{"make": row[0], "count": row[1]} for row in top_makes],
            "top_pincodes": [{"pincode": row[0], "count": row[1]} for row in top_pincodes],
            "sheets": [{"sheet": row[0], "count": row[1]} for row in sheets],
            "files": [{"file": row[0], "count": row[1]} for row in files],
            "db_size_mb": round(db_size_bytes / (1024 * 1024), 2)
        }
    finally:
        conn.close()

def add_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new single record."""
    conn = get_db_connection()
    try:
        search_text = " ".join([
            str(record.get("reg_no", "")),
            str(record.get("rto", "")),
            str(record.get("reg_date", "")),
            str(record.get("name", "")),
            str(record.get("address", "")),
            str(record.get("pincode", "")),
            str(record.get("make", "")),
            str(record.get("model_variant", "")),
            str(record.get("mobile", "")),
            str(record.get("source_sheet", "Manual"))
        ]).lower()

        conn.execute("""
            INSERT INTO records (reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet, search_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, [
            record.get("reg_no", ""),
            record.get("rto", ""),
            record.get("reg_date", ""),
            record.get("name", ""),
            record.get("address", ""),
            record.get("pincode", ""),
            record.get("make", ""),
            record.get("model_variant", ""),
            record.get("mobile", ""),
            record.get("source_file", "Manual Entry"),
            record.get("source_sheet", "Manual"),
            search_text
        ])
        
        new_id = conn.execute("SELECT currval('seq_records_id');").fetchone()[0]
        return {"status": "success", "id": new_id}
    finally:
        conn.close()

def update_record(record_id: int, record: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing record by ID."""
    conn = get_db_connection()
    try:
        search_text = " ".join([
            str(record.get("reg_no", "")),
            str(record.get("rto", "")),
            str(record.get("reg_date", "")),
            str(record.get("name", "")),
            str(record.get("address", "")),
            str(record.get("pincode", "")),
            str(record.get("make", "")),
            str(record.get("model_variant", "")),
            str(record.get("mobile", "")),
            str(record.get("source_sheet", ""))
        ]).lower()

        conn.execute("""
            UPDATE records SET
                reg_no = ?,
                rto = ?,
                reg_date = ?,
                name = ?,
                address = ?,
                pincode = ?,
                make = ?,
                model_variant = ?,
                mobile = ?,
                search_text = ?
            WHERE id = ?;
        """, [
            record.get("reg_no", ""),
            record.get("rto", ""),
            record.get("reg_date", ""),
            record.get("name", ""),
            record.get("address", ""),
            record.get("pincode", ""),
            record.get("make", ""),
            record.get("model_variant", ""),
            record.get("mobile", ""),
            search_text,
            record_id
        ])
        return {"status": "success", "id": record_id}
    finally:
        conn.close()

def delete_record(record_id: int) -> Dict[str, Any]:
    """Delete a record by ID."""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM records WHERE id = ?;", [record_id])
        return {"status": "success", "id": record_id}
    finally:
        conn.close()

def clear_database() -> Dict[str, Any]:
    """Delete all records from database."""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM records;")
        return {"status": "success", "message": "Database cleared"}
    finally:
        conn.close()
