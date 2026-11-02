import os
import shutil
import tempfile
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, UploadFile, File, Query, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
import pandas as pd
import io

from database import (
    init_db,
    ingest_files_generator,
    search_records,
    get_dashboard_stats,
    add_record,
    update_record,
    delete_record,
    clear_database
)

from auth import (
    init_auth_db,
    authenticate_user,
    create_session,
    get_user_by_token,
    invalidate_session,
    create_user_account,
    list_all_users,
    set_user_active_status,
    reset_user_one_time_password,
    user_change_password,
    delete_user_account
)

from contextlib import asynccontextmanager

def extract_token(authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)) -> Optional[str]:
    if authorization:
        parts = authorization.split(" ")
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
    return token

def get_current_user(authorization: Optional[str] = Header(None), token: Optional[str] = Query(None)) -> Dict[str, Any]:
    tok = extract_token(authorization, token)
    if not tok:
        raise HTTPException(status_code=401, detail="Authentication token required.")
    
    user = get_user_by_token(tok)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or account revoked. Please log in again.")
    
    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="Account has been revoked by administrator.")
    
    user["token"] = tok
    return user

def get_current_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required for this action.")
    return user

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DuckDB tables and SQLite Auth DB on application startup."""
    init_auth_db()
    init_db()
    yield

app = FastAPI(
    title="Universal Data Search & CRUD Engine",
    description="DuckDB-powered instant search and management for 700k+ records with RBAC",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
class LoginRequest(BaseModel):
    email: str
    password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class CreateUserRequest(BaseModel):
    email: str
    password: Optional[str] = None
    role: Optional[str] = "user"

class UpdateUserStatusRequest(BaseModel):
    is_active: bool

class ResetPasswordRequest(BaseModel):
    new_password: Optional[str] = None

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

# --- Authentication Endpoints ---

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Engine running smoothly"}

@app.post("/api/auth/login")
def login_endpoint(req: LoginRequest):
    auth_res = authenticate_user(req.email, req.password)
    if not auth_res:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    if auth_res.get("error") == "revoked":
        raise HTTPException(status_code=403, detail="Account access has been revoked. Contact administrator.")
    
    token = create_session(auth_res["id"])
    return {
        "status": "success",
        "token": token,
        "user": {
            "id": auth_res["id"],
            "email": auth_res["email"],
            "role": auth_res["role"],
            "must_change_password": auth_res["must_change_password"]
        }
    }

@app.get("/api/auth/me")
def get_current_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    return {
        "id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "must_change_password": user["must_change_password"]
    }

@app.post("/api/auth/change-password")
def change_password_endpoint(
    req: ChangePasswordRequest, 
    user: Dict[str, Any] = Depends(get_current_user)
):
    ok, msg = user_change_password(user["id"], req.old_password, req.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg}

@app.post("/api/auth/logout")
def logout_endpoint(user: Dict[str, Any] = Depends(get_current_user)):
    invalidate_session(user.get("token", ""))
    return {"status": "success", "message": "Logged out successfully."}

# --- Admin Portal User Management Endpoints ---

@app.get("/api/admin/users")
def get_users_list(admin: Dict[str, Any] = Depends(get_current_admin)):
    return {"users": list_all_users()}

@app.post("/api/admin/users")
def add_new_user(req: CreateUserRequest, admin: Dict[str, Any] = Depends(get_current_admin)):
    role = "admin" if req.role == "admin" else "user"
    ok, msg, otp = create_user_account(req.email, req.password, role)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {
        "status": "success",
        "message": msg,
        "one_time_password": otp,
        "email": req.email.strip().lower()
    }

@app.patch("/api/admin/users/{user_id}/status")
def update_user_status(user_id: int, req: UpdateUserStatusRequest, admin: Dict[str, Any] = Depends(get_current_admin)):
    if user_id == admin["id"] and not req.is_active:
        raise HTTPException(status_code=400, detail="You cannot revoke your own admin account.")
    ok, msg = set_user_active_status(user_id, req.is_active)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg}

@app.post("/api/admin/users/{user_id}/reset-password")
def reset_user_password_endpoint(
    user_id: int, 
    req: ResetPasswordRequest, 
    admin: Dict[str, Any] = Depends(get_current_admin)
):
    ok, msg, otp = reset_user_one_time_password(user_id, req.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {
        "status": "success",
        "message": msg,
        "one_time_password": otp
    }

@app.delete("/api/admin/users/{user_id}")
def delete_user_endpoint(user_id: int, admin: Dict[str, Any] = Depends(get_current_admin)):
    ok, msg = delete_user_account(user_id, admin["id"])
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg}

# --- Search & Read Endpoints (Users & Admins) ---

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
    sort_order: str = Query("ASC", description="Sort order: ASC or DESC"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # Enforce password change before accessing search data
    if current_user.get("must_change_password"):
        raise HTTPException(status_code=403, detail="You must change your one-time password before accessing search data.")

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

@app.get("/api/stats")
def stats_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)):
    return get_dashboard_stats()

# --- Admin Ingestion & Record CRUD Endpoints (ADMIN ONLY) ---

@app.post("/api/import")
async def import_excel_files(
    files: List[UploadFile] = File(...),
    admin: Dict[str, Any] = Depends(get_current_admin)
):
    """Upload Excel/CSV files and stream progress percentages to frontend (Admin Only)."""
    temp_dir = tempfile.mkdtemp()
    saved_files = []

    for file in files:
        if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
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
def create_record(record: RecordSchema, admin: Dict[str, Any] = Depends(get_current_admin)):
    return add_record(record.model_dump())

@app.put("/api/records/{record_id}")
def edit_record(record_id: int, record: RecordSchema, admin: Dict[str, Any] = Depends(get_current_admin)):
    return update_record(record_id, record.model_dump())

@app.delete("/api/records/{record_id}")
def remove_record(record_id: int, admin: Dict[str, Any] = Depends(get_current_admin)):
    return delete_record(record_id)

@app.post("/api/clear")
def clear_db(admin: Dict[str, Any] = Depends(get_current_admin)):
    return clear_database()

@app.get("/api/export")
def export_records(
    query: Optional[str] = None,
    make: Optional[str] = None,
    pincode: Optional[str] = None,
    rto: Optional[str] = None,
    source_sheet: Optional[str] = None,
    source_file: Optional[str] = None,
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    current_user: Dict[str, Any] = Depends(get_current_user)
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
