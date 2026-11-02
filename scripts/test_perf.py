import os
import sys
import time
import duckdb

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "records.duckdb")
conn = duckdb.connect(DB_FILE)

print("Total rows:", conn.execute("SELECT count(*) FROM records").fetchone()[0])

# Test 1: Current multi-ILIKE approach
t0 = time.time()
r1 = conn.execute("""
    SELECT id, name, reg_no, mobile, make FROM records
    WHERE (
        reg_no ILIKE '%MARUTI%' OR rto ILIKE '%MARUTI%' OR name ILIKE '%MARUTI%' OR
        address ILIKE '%MARUTI%' OR pincode ILIKE '%MARUTI%' OR make ILIKE '%MARUTI%' OR
        model_variant ILIKE '%MARUTI%' OR mobile ILIKE '%MARUTI%'
    ) AND (
        reg_no ILIKE '%411033%' OR rto ILIKE '%411033%' OR name ILIKE '%411033%' OR
        address ILIKE '%411033%' OR pincode ILIKE '%411033%' OR make ILIKE '%411033%' OR
        model_variant ILIKE '%411033%' OR mobile ILIKE '%411033%'
    )
    LIMIT 50
""").fetchall()
t1 = time.time()
print(f"Test 1 (Current 16 ILIKE checks): {len(r1)} rows in {(t1-t0)*1000:.2f} ms")

# Test 2: Check with search_blob or search_text column
conn.execute("ALTER TABLE records ADD COLUMN IF NOT EXISTS search_text VARCHAR;")
conn.execute("""
    UPDATE records 
    SET search_text = lower(concat_ws(' ', coalesce(reg_no,''), coalesce(name,''), coalesce(mobile,''), coalesce(make,''), coalesce(model_variant,''), coalesce(pincode,''), coalesce(rto,''), coalesce(address,'')))
    WHERE search_text IS NULL;
""")

t0 = time.time()
r2 = conn.execute("""
    SELECT id, name, reg_no, mobile, make FROM records
    WHERE search_text LIKE '%maruti%' AND search_text LIKE '%411033%'
    LIMIT 50
""").fetchall()
t2 = time.time()
print(f"Test 2 (Consolidated lower search_text with LIKE): {len(r2)} rows in {(t2-t0)*1000:.2f} ms")

# Test 3: Check FTS extension
try:
    conn.execute("INSTALL fts; LOAD fts;")
    t0 = time.time()
    conn.execute("PRAGMA create_fts_index('records', 'id', 'name', 'reg_no', 'mobile', 'make', 'model_variant', 'pincode', 'rto', 'address', overwrite=1);")
    t1 = time.time()
    print(f"FTS index built in {(t1-t0)*1000:.2f} ms")
    
    t0 = time.time()
    r3 = conn.execute("""
        SELECT r.id, r.name, r.reg_no, r.mobile, r.make, score
        FROM (
            SELECT *, fts_main_records.match_bm25(id, 'MARUTI 411033') AS score
            FROM records
        ) r
        WHERE score IS NOT NULL
        ORDER BY score DESC
        LIMIT 50;
    """).fetchall()
    t2 = time.time()
    print(f"Test 3 (FTS BM25 search): {len(r3)} rows in {(t2-t0)*1000:.2f} ms")
except Exception as e:
    print("FTS error:", e)

conn.close()
