# 🚀 Universal Data Search & CRUD Engine (700,000+ Records)

An ultra-fast, local search and management application designed for teams handling large datasets (600,000–700,000+ records) across multiple Excel files and sheets.

Powered by **DuckDB**, this system replaces slow Excel searches with instant ($<10\text{ms}$) queries across all columns, multi-sheet ingestion, CRUD record editing, and export capabilities.

---

## 🌟 Why This Solution?

Excel freezes or crashes when searching 700,000 records across multiple sheets. This application solves that problem by:
- **Instant Search ($<10\text{ms}$)**: Global full-text search across Name, Mobile Number, Registration Number, Pincode, Make/Model, Address, or Sheet.
- **Multi-Sheet Automatic Import**: Drag & drop 4–5 Excel files with 10–12 sheets each. Standardizes headers and combines everything into a single database.
- **Zero Tech Knowledge Needed**: Double-click `start.bat` on Windows to launch the server and open the browser automatically.
- **100% Offline & Private**: Runs completely on your local computer. No cloud fees or privacy risks.
- **Exporting**: Filter data by any keyword/column and export matching records back to Excel (`.xlsx`) or CSV in 1 click.

---

## 📸 Main Features & Workflow

1. **Global Multi-Word Search**: Type any combination of search terms (e.g., `MARUTI 411033 AMAR`) to find records matching all terms across all fields.
2. **Column-Level Filtering**: Filter by Make/Brand, Pincode, RTO Code, Registration Date Range, or Source Sheet.
3. **Record Management (CRUD)**: Add new leads, edit existing details inline/modal, or delete obsolete records.
4. **Excel/CSV Export**: Download active search results for sales calls.
5. **Analytics Dashboard**: Instant insight into total leads, top brands, and pincodes.

---

## 🚀 Quick Start Guide (For Non-Technical Users)

### Option 1: One-Click Launchers (Windows & macOS / Linux)

#### On Windows:
1. Make sure **Python 3.10+** is installed on your computer.
2. Double-click the **`start.bat`** file in the project folder.

#### On macOS / Linux:
1. Open Terminal, navigate to the project directory, and run:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

Both scripts automatically install dependencies, initialize DuckDB, build frontend assets if needed, launch the server, and open `http://localhost:8000` in your web browser.

---

### Option 2: Docker Compose (Single Command)

If you have Docker Desktop installed:
```bash
docker compose up -d
```
Then open your browser and navigate to:
```
http://localhost:8000
```

---

### Option 3: Manual Developer Launch

#### Backend API (Python FastAPI + DuckDB):
```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Run backend server
python backend/main.py
```

#### Frontend Dashboard (React + Vite):
```bash
# 1. Install packages
cd frontend
npm install

# 2. Start dev server
npm run dev
```

---

## 📊 Sample Excel Schema Supported

The importer automatically normalizes headers matching your dataset:

| Excel Header Variant | Standardized DB Field | Description |
| :--- | :--- | :--- |
| `REG NO`, `Registration No` | `reg_no` | Vehicle Registration Number |
| `RTO` | `rto` | RTO Region Code (e.g., MH14) |
| `REG DATE`, `Date` | `reg_date` | Date of registration |
| `NAME`, `Owner Name` | `name` | Lead / Owner Full Name |
| `ADDRESS`, `Addr` | `address` | Street, Flat, Society Address |
| `PINCODE`, `Postal Code` | `pincode` | Area Pincode |
| `MAKE`, `Brand` | `make` | Vehicle Manufacturer |
| `MODEL VARIANT` | `model_variant` | Specific Variant / Specs |
| `MOBILE`, `Phone`, `Contact` | `mobile` | Lead Phone Number |

---

## 🛠️ Testing With Synthetic Sample Data

To test the application immediately with 50,000 realistic sample rows:
```bash
python scripts/generate_sample_data.py
```
This generates `sample_data/Pune_Car_Data_2018_to_2025_Sample.xlsx` with 5 sheets (`2018`, `2019`, `2020`, `2021`, `2022`). Upload this file in the **Import Excel Files** tab to verify instant search performance!

---

## 📁 Repository Structure

```
large-data-crud/
├── backend/
│   ├── database.py       # DuckDB engine, search queries, indexing & ingestion
│   ├── main.py           # FastAPI REST endpoints & static file server
│   └── requirements.txt  # Python packages (fastapi, duckdb, pandas, etc.)
├── frontend/
│   ├── src/
│   │   ├── App.jsx       # React dashboard UI & search grid
│   │   ├── index.css     # Sleek dark/light theme styling
│   │   └── main.jsx      # React DOM entrypoint
│   ├── package.json      # Node dependencies
│   └── vite.config.js    # Vite configuration
├── scripts/
│   └── generate_sample_data.py # Sample multi-sheet Excel generator
├── data/                 # Local DuckDB database storage (.duckdb)
├── start.bat             # 1-Click Windows launcher script
├── docker-compose.yml    # Docker Compose setup
├── Dockerfile            # Multi-stage Docker build config
└── README.md             # Detailed documentation
```

---

## 🔒 Security & Data Privacy

- **100% Local Storage**: All data is stored locally in `data/records.duckdb`.
- **Zero Cloud Leakage**: No data is sent over the internet.
- **Port Binding**: By default binds to `localhost` (127.0.0.1) or port `8000`.

---

## 📄 License
MIT License. Free to use for personal, commercial, and agency work.
