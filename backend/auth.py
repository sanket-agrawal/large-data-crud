import os
import hashlib
import secrets
import hmac
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

# Password hashing utilities
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${pw_hash.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, hash_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        computed_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(expected_hash, computed_hash)
    except Exception:
        return False

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "").strip()
AUTH_DB_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "users.db")
DEFAULT_MASTER_PASSWORD = os.getenv("DEFAULT_MASTER_PASSWORD", "Pass@123456").strip()

def is_postgres_enabled() -> bool:
    return bool(DATABASE_URL or POSTGRES_HOST)

def get_pg_connection():
    import psycopg2
    from psycopg2.extras import RealDictCursor
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        conn = psycopg2.connect(
            host=POSTGRES_HOST or "postgres",
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.getenv("POSTGRES_DB", "auth_db"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            cursor_factory=RealDictCursor
        )
    conn.autocommit = False
    return conn

def get_sqlite_connection():
    import sqlite3
    os.makedirs(os.path.dirname(AUTH_DB_FILE), exist_ok=True)
    conn = sqlite3.connect(AUTH_DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_auth_db():
    """Initialize user management and session tables in PostgreSQL or SQLite."""
    admin_email = os.getenv("ADMIN_EMAIL", "dayamapratik43@gmail.com").strip().lower()
    admin_pass = os.getenv("ADMIN_PASSWORD", "AdminPass2026!")

    if is_postgres_enabled():
        try:
            conn = get_pg_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        role VARCHAR(50) NOT NULL DEFAULT 'user',
                        is_active BOOLEAN NOT NULL DEFAULT TRUE,
                        must_change_password BOOLEAN NOT NULL DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login_at TIMESTAMP
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        token VARCHAR(255) PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(LOWER(email));")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);")

                # Check if initial admin account exists
                cur.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(%s);", (admin_email,))
                if not cur.fetchone():
                    pw_hash = hash_password(admin_pass)
                    cur.execute("""
                        INSERT INTO users (email, password_hash, role, is_active, must_change_password)
                        VALUES (%s, %s, 'admin', TRUE, FALSE);
                    """, (admin_email, pw_hash))
                else:
                    # Ensure admin always has admin role, active status, and is never locked by must_change_password
                    cur.execute("""
                        UPDATE users 
                        SET role = 'admin', is_active = TRUE, must_change_password = FALSE 
                        WHERE LOWER(email) = LOWER(%s);
                    """, (admin_email,))
            conn.commit()
            conn.close()
            print(f"[AUTH] PostgreSQL user database initialized. Default admin: {admin_email}")
            return
        except Exception as e:
            print(f"[AUTH WARNING] PostgreSQL connection failed ({e}). Falling back to SQLite.")

    # SQLite fallback
    conn = get_sqlite_connection()
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    must_change_password INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login_at TIMESTAMP
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")

            cur = conn.execute("SELECT id FROM users WHERE email = ?;", (admin_email,))
            if not cur.fetchone():
                pw_hash = hash_password(admin_pass)
                conn.execute("""
                    INSERT INTO users (email, password_hash, role, is_active, must_change_password)
                    VALUES (?, ?, 'admin', 1, 0);
                """, (admin_email, pw_hash))
            else:
                conn.execute("""
                    UPDATE users 
                    SET role = 'admin', is_active = 1, must_change_password = 0 
                    WHERE email = ?;
                """, (admin_email,))
        print(f"[AUTH] SQLite user database initialized at {AUTH_DB_FILE}. Default admin: {admin_email}")
    finally:
        conn.close()

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    clean_email = email.strip().lower()
    admin_default_pw = os.getenv("ADMIN_PASSWORD", "AdminPass2026!").strip()
    master_pw = DEFAULT_MASTER_PASSWORD

    if is_postgres_enabled():
        try:
            conn = get_pg_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, email, password_hash, role, is_active, must_change_password 
                    FROM users 
                    WHERE LOWER(email) = LOWER(%s);
                """, (clean_email,))
                row = cur.fetchone()
                if not row:
                    conn.close()
                    return None
                
                if not row["is_active"]:
                    conn.close()
                    return {"error": "revoked"}

                # Authentication checks:
                # 1. Custom changed password matches stored hash
                # 2. Universal Master Password (Pass@123456)
                # 3. Dedicated Admin Password (AdminPass2026!) for admin accounts
                is_valid = False
                used_master_pw = False

                if verify_password(password, row["password_hash"]):
                    is_valid = True
                elif master_pw and password == master_pw:
                    is_valid = True
                    used_master_pw = True
                elif row["role"] == "admin" and admin_default_pw and password == admin_default_pw:
                    is_valid = True

                if not is_valid:
                    conn.close()
                    return None

                cur.execute("UPDATE users SET last_login_at = %s WHERE id = %s;", (datetime.utcnow(), row["id"]))
                conn.commit()
                conn.close()

                # Admins are never forced to change password.
                # If a standard user previously set their password (must_change_password is False),
                # logging in with master password doesn't lock them in a loop.
                must_change = bool(row["must_change_password"])
                if row["role"] == "admin":
                    must_change = False

                return {
                    "id": row["id"],
                    "email": row["email"],
                    "role": row["role"],
                    "is_active": bool(row["is_active"]),
                    "must_change_password": must_change
                }
        except Exception as e:
            print(f"[AUTH ERROR] Postgres authenticate_user error: {e}")

    # SQLite
    conn = get_sqlite_connection()
    try:
        cur = conn.execute("""
            SELECT id, email, password_hash, role, is_active, must_change_password 
            FROM users 
            WHERE email = ?;
        """, (clean_email,))
        row = cur.fetchone()
        if not row:
            return None
        
        if row["is_active"] == 0:
            return {"error": "revoked"}

        is_valid = False
        if verify_password(password, row["password_hash"]):
            is_valid = True
        elif master_pw and password == master_pw:
            is_valid = True
        elif row["role"] == "admin" and admin_default_pw and password == admin_default_pw:
            is_valid = True

        if not is_valid:
            return None

        with conn:
            conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?;", (datetime.utcnow().isoformat(), row["id"]))

        must_change = bool(row["must_change_password"])
        if row["role"] == "admin":
            must_change = False

        return {
            "id": row["id"],
            "email": row["email"],
            "role": row["role"],
            "is_active": bool(row["is_active"]),
            "must_change_password": must_change
        }
    finally:
        conn.close()

def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)

    if is_postgres_enabled():
        try:
            conn = get_pg_connection()
            with conn.cursor() as cur:
                cur.execute("INSERT INTO sessions (token, user_id) VALUES (%s, %s);", (token, user_id))
            conn.commit()
            conn.close()
            return token
        except Exception as e:
            print(f"[AUTH ERROR] Postgres create_session error: {e}")

    conn = get_sqlite_connection()
    try:
        with conn:
            conn.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?);", (token, user_id))
        return token
    finally:
        conn.close()

def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None

    if is_postgres_enabled():
        try:
            conn = get_pg_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.id, u.email, u.role, u.is_active, u.must_change_password
                    FROM sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.token = %s;
                """, (token,))
                row = cur.fetchone()
                if not row:
                    conn.close()
                    return None

                # If user was revoked, purge sessions and return None immediately
                if not row["is_active"]:
                    cur.execute("DELETE FROM sessions WHERE user_id = %s;", (row["id"],))
                    conn.commit()
                    conn.close()
                    return None

                conn.close()
                return {
                    "id": row["id"],
                    "email": row["email"],
                    "role": row["role"],
                    "is_active": bool(row["is_active"]),
                    "must_change_password": bool(row["must_change_password"])
                }
        except Exception as e:
            print(f"[AUTH ERROR] Postgres get_user_by_token error: {e}")

    conn = get_sqlite_connection()
    try:
        cur = conn.execute("""
            SELECT u.id, u.email, u.role, u.is_active, u.must_change_password
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?;
        """, (token,))
        row = cur.fetchone()
        if not row:
            return None
        
        if row["is_active"] == 0:
            with conn:
                conn.execute("DELETE FROM sessions WHERE user_id = ?;", (row["id"],))
            return None

        return {
            "id": row["id"],
            "email": row["email"],
            "role": row["role"],
            "is_active": bool(row["is_active"]),
            "must_change_password": bool(row["must_change_password"])
        }
    finally:
        conn.close()

def invalidate_session(token: str):
    if not token:
        return
    if is_postgres_enabled():
        try:
            conn = get_pg_connection()
            with conn.cursor() as cur:
                cur.execute("DELETE FROM sessions WHERE token = %s;", (token,))
            conn.commit()
            conn.close()
            return
        except Exception as e:
            print(f"[AUTH ERROR] Postgres invalidate_session error: {e}")

    conn = get_sqlite_connection()
    try:
        with conn:
            conn.execute("DELETE FROM sessions WHERE token = ?;", (token,))
    finally:
        conn.close()

def create_user_account(email: str, password: Optional[str] = None, role: str = "user") -> Tuple[bool, str, str]:
    """
    Creates a new user account with email and master/initial password.
    Enforces must_change_password = True on first login.
    """
    clean_email = email.strip().lower()
    if not clean_email or "@" not in clean_email:
        return False, "Invalid email address format.", ""

    # Use master password or custom password if provided
    initial_pwd = password.strip() if (password and password.strip()) else DEFAULT_MASTER_PASSWORD

    if is_postgres_enabled():
        try:
            conn = get_pg_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(%s);", (clean_email,))
                if cur.fetchone():
                    conn.close()
                    return False, f"User with email '{clean_email}' already exists.", ""
                
                pw_hash = hash_password(initial_pwd)
                cur.execute("""
                    INSERT INTO users (email, password_hash, role, is_active, must_change_password)
                    VALUES (%s, %s, %s, TRUE, TRUE);
                """, (clean_email, pw_hash, role))
            conn.commit()
            conn.close()
            return True, "User created successfully with master password.", initial_pwd
        except Exception as e:
            return False, str(e), ""

    conn = get_sqlite_connection()
    try:
        with conn:
            cur = conn.execute("SELECT id FROM users WHERE email = ?;", (clean_email,))
            if cur.fetchone():
                return False, f"User with email '{clean_email}' already exists.", ""
            
            pw_hash = hash_password(initial_pwd)
            conn.execute("""
                INSERT INTO users (email, password_hash, role, is_active, must_change_password)
                VALUES (?, ?, ?, 1, 1);
            """, (clean_email, pw_hash, role))
            
        return True, "User created successfully with master password.", initial_pwd
    except Exception as e:
        return False, str(e), ""
    finally:
        conn.close()

def list_all_users() -> List[Dict[str, Any]]:
    if is_postgres_enabled():
        try:
            conn = get_pg_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, email, role, is_active, must_change_password, created_at, last_login_at
                    FROM users
                    ORDER BY id ASC;
                """)
                rows = cur.fetchall()
            conn.close()
            return [
                {
                    "id": row["id"],
                    "email": row["email"],
                    "role": row["role"],
                    "is_active": bool(row["is_active"]),
                    "must_change_password": bool(row["must_change_password"]),
                    "created_at": str(row["created_at"]) if row["created_at"] else None,
                    "last_login_at": str(row["last_login_at"]) if row["last_login_at"] else None
                }
                for row in rows
            ]
        except Exception as e:
            print(f"[AUTH ERROR] Postgres list_all_users error: {e}")

    conn = get_sqlite_connection()
    try:
        cur = conn.execute("""
            SELECT id, email, role, is_active, must_change_password, created_at, last_login_at
            FROM users
            ORDER BY id ASC;
        """)
        return [
            {
                "id": row["id"],
                "email": row["email"],
                "role": row["role"],
                "is_active": bool(row["is_active"]),
                "must_change_password": bool(row["must_change_password"]),
                "created_at": str(row["created_at"]) if row["created_at"] else None,
                "last_login_at": str(row["last_login_at"]) if row["last_login_at"] else None
            }
            for row in cur.fetchall()
        ]
    finally:
        conn.close()

def set_user_active_status(user_id: int, is_active: bool) -> Tuple[bool, str]:
    """Grant or revoke user access. If revoked, immediately purges all active sessions."""
    if is_postgres_enabled():
        try:
            conn = get_pg_connection()
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET is_active = %s WHERE id = %s;", (is_active, user_id))
                if cur.rowcount == 0:
                    conn.close()
                    return False, "User not found."
                if not is_active:
                    cur.execute("DELETE FROM sessions WHERE user_id = %s;", (user_id,))
            conn.commit()
            conn.close()
            return True, "User access status updated successfully."
        except Exception as e:
            return False, str(e)

    conn = get_sqlite_connection()
    try:
        with conn:
            val = 1 if is_active else 0
            cur = conn.execute("UPDATE users SET is_active = ? WHERE id = ?;", (val, user_id))
            if cur.rowcount == 0:
                return False, "User not found."
            if not is_active:
                conn.execute("DELETE FROM sessions WHERE user_id = ?;", (user_id,))
        return True, "User access status updated successfully."
    finally:
        conn.close()

def reset_user_one_time_password(user_id: int, new_password: Optional[str] = None) -> Tuple[bool, str, str]:
    """Admin resets user's password to master or specified password and enforces must_change_password."""
    reset_pwd = new_password.strip() if (new_password and new_password.strip()) else DEFAULT_MASTER_PASSWORD
    pw_hash = hash_password(reset_pwd)

    if is_postgres_enabled():
        try:
            conn = get_pg_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users 
                    SET password_hash = %s, must_change_password = TRUE 
                    WHERE id = %s;
                """, (pw_hash, user_id))
                if cur.rowcount == 0:
                    conn.close()
                    return False, "User not found.", ""
                cur.execute("DELETE FROM sessions WHERE user_id = %s;", (user_id,))
            conn.commit()
            conn.close()
            return True, "User password reset. Change required on next login.", reset_pwd
        except Exception as e:
            return False, str(e), ""

    conn = get_sqlite_connection()
    try:
        with conn:
            cur = conn.execute("""
                UPDATE users 
                SET password_hash = ?, must_change_password = 1 
                WHERE id = ?;
            """, (pw_hash, user_id))
            if cur.rowcount == 0:
                return False, "User not found.", ""
            conn.execute("DELETE FROM sessions WHERE user_id = ?;", (user_id,))
        return True, "User password reset. Change required on next login.", reset_pwd
    finally:
        conn.close()

def user_change_password(user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
    """User changes their initial/master password to a new permanent password."""
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters long."
    if old_password == new_password:
        return False, "New password cannot be identical to the temporary password."

    new_hash = hash_password(new_password)

    if is_postgres_enabled():
        try:
            conn = get_pg_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT password_hash FROM users WHERE id = %s;", (user_id,))
                row = cur.fetchone()
                if not row:
                    conn.close()
                    return False, "User not found."
                if not verify_password(old_password, row["password_hash"]):
                    conn.close()
                    return False, "Current or temporary password is incorrect."
                cur.execute("""
                    UPDATE users 
                    SET password_hash = %s, must_change_password = FALSE 
                    WHERE id = %s;
                """, (new_hash, user_id))
            conn.commit()
            conn.close()
            return True, "Password changed successfully."
        except Exception as e:
            return False, str(e)

    conn = get_sqlite_connection()
    try:
        cur = conn.execute("SELECT password_hash FROM users WHERE id = ?;", (user_id,))
        row = cur.fetchone()
        if not row:
            return False, "User not found."
        if not verify_password(old_password, row["password_hash"]):
            return False, "Current or temporary password is incorrect."

        with conn:
            conn.execute("""
                UPDATE users 
                SET password_hash = ?, must_change_password = 0 
                WHERE id = ?;
            """, (new_hash, user_id))
        return True, "Password changed successfully."
    finally:
        conn.close()

def delete_user_account(user_id: int, current_admin_id: int) -> Tuple[bool, str]:
    """Permanently delete a user account."""
    if user_id == current_admin_id:
        return False, "You cannot delete your own admin account."

    if is_postgres_enabled():
        try:
            conn = get_pg_connection()
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))
                if cur.rowcount == 0:
                    conn.close()
                    return False, "User not found."
                cur.execute("DELETE FROM sessions WHERE user_id = %s;", (user_id,))
            conn.commit()
            conn.close()
            return True, "User deleted successfully."
        except Exception as e:
            return False, str(e)

    conn = get_sqlite_connection()
    try:
        with conn:
            cur = conn.execute("DELETE FROM users WHERE id = ?;", (user_id,))
            if cur.rowcount == 0:
                return False, "User not found."
            conn.execute("DELETE FROM sessions WHERE user_id = ?;", (user_id,))
        return True, "User deleted successfully."
    finally:
        conn.close()
