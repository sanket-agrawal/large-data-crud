import os
import shutil
import tempfile
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import io

from database import (
    init_db,
    ingest_excel_file,
    ingest_files_generator,
    search_records,
    get_dashboard_stats,
    add_record,
    update_record,
    delete_record,
    clear_database
)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DuckDB tables on application startup."""
    init_db()
    yield

app = FastAPI(
    title="Large Data CRUD & Search API",
    description="DuckDB-powered instant search and management for 700k+ records",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic schemas
class RecordSchema(BaseModel):
    reg_no: Optional[str] = ""
    rto: Optional[str] = ""
    reg_date: Optional[str] = ""
    name: Optional[str] = ""
    address: Optional[str] = ""
    pincode: Optional[str] = ""
    make: Optional[str] = ""
    model_variant: Optional[str] = ""
    mobile: Optional[str] = ""
    source_file: Optional[str] = "Manual Entry"
    source_sheet: Optional[str] = "Manual"

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "DuckDB Search API is running"}

@app.get("/api/stats")
def stats_endpoint():
    return get_dashboard_stats()

@app.get("/api/search")
def search_endpoint(
    query: Optional[str] = Query(None, description="Global search query across all fields"),
    make: Optional[str] = Query(None, description="Filter by Make / Brand"),
    pincode: Optional[str] = Query(None, description="Filter by Pincode"),
    rto: Optional[str] = Query(None, description="Filter by RTO code"),
    source_sheet: Optional[str] = Query(None, description="Filter by source sheet"),
    source_file: Optional[str] = Query(None, description="Filter by source file"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=500, description="Records per page"),
    sort_by: str = Query("id", description="Column to sort by"),
    sort_order: str = Query("ASC", description="Sort order: ASC or DESC")
):
    return search_records(
        query=query,
        make=make,
        pincode=pincode,
        rto=rto,
        source_sheet=source_sheet,
        source_file=source_file,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )

@app.post("/api/import")
async def import_excel_files(files: List[UploadFile] = File(...)):
    """Upload one or multiple Excel files and stream progress percentages to frontend."""
    temp_dir = tempfile.mkdtemp()
    saved_files = []

    for file in files:
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            continue
        temp_path = os.path.join(temp_dir, file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append((temp_path, file.filename))

    def stream_wrapper():
        try:
            for chunk in ingest_files_generator(saved_files):
                yield chunk
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    return StreamingResponse(stream_wrapper(), media_type="text/event-stream")

@app.post("/api/records")
def create_record(record: RecordSchema):
    return add_record(record.model_dump())

@app.put("/api/records/{record_id}")
def edit_record(record_id: int, record: RecordSchema):
    return update_record(record_id, record.model_dump())

@app.delete("/api/records/{record_id}")
def remove_record(record_id: int):
    return delete_record(record_id)

@app.post("/api/clear")
def clear_db():
    return clear_database()

@app.get("/api/export")
def export_records(
    query: Optional[str] = None,
    make: Optional[str] = None,
    pincode: Optional[str] = None,
    rto: Optional[str] = None,
    source_sheet: Optional[str] = None,
    source_file: Optional[str] = None,
    format: str = Query("csv", pattern="^(csv|xlsx)$")
):
    """Export matching search query results (up to 100,000 rows) as CSV or Excel."""
    res = search_records(
        query=query,
        make=make,
        pincode=pincode,
        rto=rto,
        source_sheet=source_sheet,
        source_file=source_file,
        page=1,
        limit=100000
    )
    
    df = pd.DataFrame(res["data"])
    if df.empty:
        df = pd.DataFrame(columns=["reg_no", "rto", "reg_date", "name", "address", "pincode", "make", "model_variant", "mobile"])

    if format == "csv":
        stream = io.StringIO()
        df.to_csv(stream, index=False)
        response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=filtered_records.csv"
        return response
    else:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Filtered Records")
        output.seek(0)
        return StreamingResponse(
            output, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=filtered_records.xlsx"}
        )

# Serve static frontend built files if available
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
