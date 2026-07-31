import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from database import init_db, ingest_excel_file, search_records, get_dashboard_stats

def main():
    print("Testing DuckDB engine...")
    init_db()
    
    sample_file = os.path.join(os.path.dirname(__file__), "..", "sample_data", "Pune_Car_Data_2018_to_2025_Sample.xlsx")
    if os.path.exists(sample_file):
        print(f"Ingesting sample Excel file: {sample_file}")
        t0 = time.time()
        res = ingest_excel_file(sample_file, "Pune_Car_Data_2018_to_2025_Sample.xlsx")
        t1 = time.time()
        print(f"Ingested {res['total_rows']} rows across {len(res['sheets'])} sheets in {(t1 - t0):.2f} seconds.")
    else:
        print("Sample file not ready yet. Skipping ingestion test.")

    print("\nExecuting instant search benchmarks...")
    
    # Benchmark 1: Global keyword search
    t0 = time.time()
    s1 = search_records(query="MARUTI 411033", limit=25)
    t1 = time.time()
    print(f"Search 'MARUTI 411033': Found {s1['total']} records in {(t1 - t0)*1000:.2f} ms!")

    # Benchmark 2: Name search
    t0 = time.time()
    s2 = search_records(query="AMAR", limit=25)
    t1 = time.time()
    print(f"Search Name 'AMAR': Found {s2['total']} records in {(t1 - t0)*1000:.2f} ms!")

    # Benchmark 3: Filter by Make & Pincode
    t0 = time.time()
    s3 = search_records(make="HYUNDAI", pincode="411027", limit=25)
    t1 = time.time()
    print(f"Filter Make='HYUNDAI' & Pincode='411027': Found {s3['total']} records in {(t1 - t0)*1000:.2f} ms!")

    # Stats
    stats = get_dashboard_stats()
    print("\nDashboard Statistics:")
    print(f"- Total Database Records: {stats['total_records']:,}")
    print(f"- Database File Size: {stats['db_size_mb']} MB")
    print(f"- Sheets Count: {len(stats['sheets'])}")

if __name__ == "__main__":
    main()
