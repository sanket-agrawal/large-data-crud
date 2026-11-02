import duckdb
import os
import re
import json
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import threading

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "records.duckdb")

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

    # Populate search_text for any rows where it is NULL
    conn.execute("""
        UPDATE records 
        SET search_text = lower(concat_ws(' ', 
            coalesce(reg_no, ''), coalesce(rto, ''), coalesce(reg_date, ''), 
            coalesce(name, ''), coalesce(address, ''), coalesce(pincode, ''), 
            coalesce(make, ''), coalesce(model_variant, ''), coalesce(mobile, ''), 
            coalesce(source_sheet, '')
        ))
        WHERE search_text IS NULL;
    """)

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

def search_records(
    query: Optional[str] = None,
    make: Optional[str] = None,
    pincode: Optional[str] = None,
    rto: Optional[str] = None,
    source_sheet: Optional[str] = None,
    source_file: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    sort_by: str = "id",
    sort_order: str = "ASC"
) -> Dict[str, Any]:
    """
    Fast query search across 700k+ rows with global multi-word match and filters.
    Optimized to sub-10ms using consolidated pre-lowercased search_text.
    """
    conn = get_db_connection()
    try:
        where_clauses = []
        params = []

        # Global multi-word search against pre-lowercased search_text
        if query and query.strip():
            terms = query.strip().lower().split()
            for term in terms:
                where_clauses.append("search_text LIKE ?")
                params.append(f"%{term}%")

        # Column-specific filters
        if make and make.strip():
            where_clauses.append("make ILIKE ?")
            params.append(f"%{make.strip()}%")

        if pincode and pincode.strip():
            where_clauses.append("pincode LIKE ?")
            params.append(f"%{pincode.strip()}%")

        if rto and rto.strip():
            where_clauses.append("rto ILIKE ?")
            params.append(f"%{rto.strip()}%")

        if source_sheet and source_sheet.strip():
            where_clauses.append("source_sheet = ?")
            params.append(source_sheet.strip())

        if source_file and source_file.strip():
            where_clauses.append("source_file = ?")
            params.append(source_file.strip())

        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        allowed_sort_cols = [
            "id", "reg_no", "rto", "reg_date", "name", "address", 
            "pincode", "make", "model_variant", "mobile", "source_file", "source_sheet"
        ]
        if sort_by not in allowed_sort_cols:
            sort_by = "id"
        sort_order_clean = "DESC" if sort_order.upper() == "DESC" else "ASC"

        # Count total matching rows
        if not where_clauses:
            total_rows = conn.execute("SELECT COUNT(*) FROM records;").fetchone()[0]
        else:
            count_sql = f"SELECT COUNT(*) FROM records{where_sql};"
            total_rows = conn.execute(count_sql, params).fetchone()[0]

        # Query paginated rows with limit + 1 to detect has_more
        offset = max(0, (page - 1) * limit)
        data_sql = f"""
            SELECT id, reg_no, rto, reg_date, name, address, pincode, make, model_variant, mobile, source_file, source_sheet
            FROM records
            {where_sql}
            ORDER BY {sort_by} {sort_order_clean}
            LIMIT ? OFFSET ?;
        """
        query_params = params + [limit + 1, offset]
        rows = conn.execute(data_sql, query_params).fetchall()

        has_more = len(rows) > limit
        result_rows = rows[:limit]

        columns = [
            "id", "reg_no", "rto", "reg_date", "name", "address", 
            "pincode", "make", "model_variant", "mobile", "source_file", "source_sheet"
        ]
        records = [dict(zip(columns, row)) for row in result_rows]

        return {
            "total": total_rows,
            "page": page,
            "limit": limit,
            "total_pages": (total_rows + limit - 1) // limit if limit > 0 else 1,
            "has_more": has_more,
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
