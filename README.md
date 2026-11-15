# 🚀 Universal Data Search & Management Engine (2,000,000+ Records)

A high-performance, mobile-first search and CRUD engine built to query **20 lakh (2 million) records in 2 to 8 milliseconds** with DuckDB ART indexes, PostgreSQL user authentication, and automated HTTPS deployment on **Hostinger VPS (KVM 2)** behind **Cloudflare DNS**.

---

## 🌟 Architecture Overview

```
                      ┌───────────────────────────────────────────────┐
                      │              Cloudflare DNS                   │
                      │         (vehicle.sanketagrawal.com)           │
                      └──────────────────────┬────────────────────────┘
                                             │ HTTPS (:443)
                                             ▼
                      ┌───────────────────────────────────────────────┐
                      │            Hostinger VPS (KVM 2)              │
                      │                                               │
                      │  ┌─────────────────────────────────────────┐  │
                      │  │           Caddy Reverse Proxy           │  │
                      │  │         (Auto SSL & Gzip/Zstd)          │  │
                      │  └───────────────────┬─────────────────────┘  │
                      │                      │                        │
                      │                      ▼                        │
                      │  ┌─────────────────────────────────────────┐  │
                      │  │        FastAPI Application Server       │  │
                      │  │    (Mobile Web App + REST API)          │  │
                      │  └───┬─────────────────────────────────┬───┘  │
                      │      │                                 │      │
                      │      ▼                                 ▼      │
                      │  ┌───────────────┐         ┌───────────────┐  │
                      │  │ PostgreSQL 16 │         │ DuckDB Engine │  │
                      │  │  (Users/Auth) │         │ (2M+ Records) │  │
                      │  └───────────────┘         └───────────────┘  │
                      └───────────────────────────────────────────────┘
```

---

## ⚡ Performance Highlights (2M+ Rows Benchmark)

| Query Type | Input Example | Execution Time | Index Used |
| :--- | :--- | :--- | :--- |
| **Exact Vehicle Number** | `MH12SM5430`, `mh 12 sm 5430` | **2.9 ms – 4.7 ms** | `idx_reg_no` (ART Index) |
| **Mobile Number** | `9354973331`, `9923344399` | **5.3 ms – 7.5 ms** | `idx_mobile` (ART Index) |
| **Exact Owner Name** | `NIDHI BABULAL SINGH` | **6.6 ms – 9.4 ms** | `idx_name` (ART Index) |
| **Prefix Reg No** | `MH12SM%` | **~23 ms** | Range Scan |

---

## 🔐 User & Admin Management Workflow

### 1. Admin Capabilities
- **Data Ingestion**: Upload multi-sheet Excel files or CSVs with live SSE progress.
- **Grant & Revoke Access**: Create users via email; revoke anytime with immediate active session termination.
- **Master Password Assignment**: New users are provisioned with a configurable default master password (`DEFAULT_MASTER_PASSWORD`).
- **Forced Password Change**: On first login, users are locked out from search until they change their password to a permanent one.

### 2. Standard Mobile User Experience
- **Mobile-First Design**: Optimized for smartphones with clean vehicle cards.
- **Instant Result Display**: Highlights **Owner Name**, **Address**, **Mobile Number**, **Vehicle Make & Model**, and **Registration Number**.
- **1-Tap Actions**: Direct **Call** (`tel:`) and **Copy to Clipboard** buttons for phone numbers and details.

---

## 🌐 Deployment to Hostinger VPS (KVM 2)

### Step 1: Cloudflare DNS Setup
1. Log in to your [Cloudflare Dashboard](https://dash.cloudflare.com/).
2. Select domain **`sanketagrawal.com`** ➔ **DNS** ➔ **Records**.
3. Add an **A Record**:
   - **Type**: `A`
   - **Name**: `vehicle` (creates `vehicle.sanketagrawal.com`)
   - **IPv4 Address**: `<YOUR_HOSTINGER_VPS_IP>`
   - **Proxy Status**: **Proxied** (Orange Cloud) or **DNS Only** (Gray Cloud)
   - **TTL**: Auto
4. In **SSL/TLS**: Set encryption mode to **Full** (or **Full Strict**).

---

### Step 2: Upload DuckDB File (~814 MB) to VPS
Run from your local computer:

#### On Windows (PowerShell / Command Prompt):
```bat
upload_duckdb.bat
```
*(Prompts for your VPS IP and uploads `D:\Projects\freelance\records.duckdb` with SSH compression)*

#### Or via direct SCP / Rsync:
```bash
scp -C "D:\Projects\freelance\records.duckdb" root@<VPS_IP>:/opt/large-data-crud/data/records.duckdb
```

---

### Step 3: Run Deployment on VPS
1. SSH into your Hostinger VPS:
   ```bash
   ssh root@<YOUR_VPS_IP>
   ```
2. Clone or copy this repository to `/opt/large-data-crud`:
   ```bash
   mkdir -p /opt/large-data-crud
   cd /opt/large-data-crud
   ```
3. Create your production `.env` file:
   ```bash
   cp .env.example .env
   nano .env
   ```
   Configure your credentials:
   ```env
   DOMAIN_NAME=vehicle.sanketagrawal.com
   SSL_EMAIL=dayamapratik43@gmail.com
   POSTGRES_DB=auth_db
   POSTGRES_USER=appuser
   POSTGRES_PASSWORD=YourSecurePostgresPassword2026!
   ADMIN_EMAIL=dayamapratik43@gmail.com
   ADMIN_PASSWORD=YourAdminPassword2026!
   DEFAULT_MASTER_PASSWORD=Pass@123456
   DUCKDB_PATH=/app/data/records.duckdb
   ```
4. Run the automated deployment script:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

Docker Compose will start:
- `large-data-postgres`: PostgreSQL 16 database for RBAC and sessions.
- `large-data-app`: Python FastAPI + DuckDB engine + pre-built Vue mobile frontend.
- `large-data-caddy`: Automatic HTTPS reverse proxy.

---

## 💻 Local Development Launch

### Quick Launch (Windows):
Double-click `start.bat`.

### Manual Developer Launch:
```bash
# 1. Backend
pip install -r backend/requirements.txt
python backend/main.py

# 2. Frontend
cd frontend
npm install
npm run dev
```

---

## 🔒 Security Summary
- **No Public DB Exposure**: PostgreSQL port 5432 is internal to the Docker network.
- **Session Revocation**: Revoking a user's access immediately drops all active session tokens.
- **One-Time Master Password**: Forced permanent password change on first login.
- **PBKDF2 Password Hashing**: Passwords stored with random salts and 100,000 PBKDF2 iterations.
