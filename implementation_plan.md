# Large Data Search & CRUD Application (DuckDB + Modern Web Dashboard)

A high-performance local application designed to ingest, combine, search, edit, and export 600,000–700,000+ real estate/automobile records across multiple Excel files and sheets using **DuckDB**.

## User Review Required

> [!IMPORTANT]
> **Key Architecture Decisions:**
> 1. **Database Engine (DuckDB)**: DuckDB will store the unified dataset locally in a `.duckdb` file. It delivers sub-10ms search queries across 700,000+ rows while keeping memory usage under ~100MB.
> 2. **Backend Framework**: Python (FastAPI) + DuckDB + OpenPyXL/Pandas for maximum DuckDB performance and streaming Excel sheet ingestion.
> 3. **Frontend Dashboard**: React + Vite + Modern UI (Dark/Light mode, Glassmorphism design, virtualized data grid for smooth 60 FPS rendering, full-text instant search, column-level filters, CRUD modals, and export tools).
> 4. **Ease of Use for Non-Tech Users**:
>    - **One-Click Double-Click Launcher (`start.bat` / `start.ps1`)**: Automatically starts the server and opens the browser interface.
>    - **Docker Compose Setup (`docker-compose.yml`)**: Single-command container launcher for Docker users (`docker compose up`).
>    - **Comprehensive README Guide**: Detailed step-by-step user guide with visuals.

---

## Key Features

1. **Multi-File & Multi-Sheet Excel Importer**:
   - Drag & drop 4–5 Excel files containing 10–12 sheets each.
   - Automatically merges all sheets, normalizes column names (`REG NO`, `RTO`, `REG DATE`, `NAME`, `ADDRESS`, `PINCODE`, `MAKE`, `MODEL VARIANT`, `MOBILE`), and tracks file/sheet metadata.
   - Live progress indicator showing row counts and sheet parsing status.

2. **Ultra-Fast Global & Column Search**:
   - Instant search across all fields (Name, Mobile, Reg No, Address, Pincode, Make, Model, Sheet Name).
   - SQL-indexed queries and DuckDB Full-Text Search (FTS) for sub-second responses on 700,000+ records.
   - Multi-column filtering (e.g., Filter by Pincode, Make, Registration Date Range, RTO).

3. **High-Performance Virtualized Table & CRUD**:
   - Virtualized row rendering to scroll smoothly through 700,000 records without UI lag.
   - Inline row viewing & modal editing (Add new entry, Edit existing entry, Delete record).

4. **1-Click Exporting**:
   - Export filtered query results back to `.xlsx` or `.csv`.

5. **Local & Private Execution**:
   - 100% offline local execution, zero subscription fees, complete data privacy.

---

## Proposed Changes

### Root Directory

#### [NEW] [README.md](file:///d:/Projects/freelance/large-data-crud/README.md)
Comprehensive user guide for non-technical users, step-by-step setup instructions, launch scripts documentation, and Docker Compose usage.

#### [NEW] [start.bat](file:///d:/Projects/freelance/large-data-crud/start.bat)
Windows double-click launcher script that installs requirements (if needed), starts the server, and opens `http://localhost:8000` automatically in the browser.

#### [NEW] [docker-compose.yml](file:///d:/Projects/freelance/large-data-crud/docker-compose.yml) & [Dockerfile](file:///d:/Projects/freelance/large-data-crud/Dockerfile)
Docker configuration to launch the full application with a single command `docker compose up`.

---

### Backend (`/backend`)

#### [NEW] [backend/main.py](file:///d:/Projects/freelance/large-data-crud/backend/main.py)
FastAPI application providing APIs for:
- `/api/import`: Ingesting Excel files (.xlsx, .csv) with multi-sheet auto-detection and DuckDB insertion.
- `/api/search`: Fast paginated search with global search term, column filters, and sorting.
- `/api/stats`: Overview dashboard statistics (total rows, counts by Make, Pincode, Year/Sheet).
- `/api/records`: CRUD operations (Create, Read, Update, Delete).
- `/api/export`: Exporting filtered results to CSV/Excel.

#### [NEW] [backend/database.py](file:///d:/Projects/freelance/large-data-crud/backend/database.py)
DuckDB connection manager, schema initializer, indexing, FTS setup, and query execution helper functions.

#### [NEW] [backend/requirements.txt](file:///d:/Projects/freelance/large-data-crud/backend/requirements.txt)
Dependencies: `fastapi`, `uvicorn`, `duckdb`, `pandas`, `openpyxl`, `python-multipart`, `pydantic`.

---

### Frontend (`/frontend`)

#### [NEW] Modern Frontend Dashboard (React + Vite + CSS)
- **Import Screen**: Drag & drop upload with progress bars.
- **Search & Data Grid**: Ultra-fast search bar, column filters, pagination, virtualized grid, edit modal, delete modal, export buttons.
- **Analytics & Stats Bar**: Quick insight cards (Total Records, Unique Brands, Pincodes).
- **Settings / File Management**: Option to view imported files or reset the database.

---

## Verification Plan

### Automated Tests
- Run API unit tests for DuckDB search queries, pagination, and filter accuracy.
- Test multi-sheet Excel parsing with sample Excel generator scripts.

### Manual Verification
- Test uploading multi-sheet Excel files containing large synthetic datasets (e.g. 500,000+ rows).
- Verify instant search latency ($<50\text{ms}$) across 500,000+ rows for Name, Mobile, Pincode, and Reg No.
- Test CRUD operations (editing a record, adding a new record, deleting a record) and confirm immediate DuckDB reflection.
- Verify `start.bat` launch experience and browser auto-opening.
