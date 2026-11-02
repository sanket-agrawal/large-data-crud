import os
import sqlite3
import hashlib
import secrets
import hmac
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

AUTH_DB_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "users.db")

def get_auth_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(AUTH_DB_FILE), exist_ok=True)
    conn = sqlite3.connect(AUTH_DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

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

def init_auth_db():
    conn = get_auth_connection()
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

            # Check if default admin exists
            admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com").strip().lower()
            admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
            
            cur = conn.execute("SELECT id FROM users WHERE email = ?;", (admin_email,))
            if not cur.fetchone():
                pw_hash = hash_password(admin_pass)
                conn.execute("""
                    INSERT INTO users (email, password_hash, role, is_active, must_change_password)
                    VALUES (?, ?, 'admin', 1, 0);
                """, (admin_email, pw_hash))
    finally:
        conn.close()

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    conn = get_auth_connection()
    try:
        clean_email = email.strip().lower()
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

        if not verify_password(password, row["password_hash"]):
            return None

        # Update last login
        with conn:
            conn.execute("UPDATE users SET last_login_at = ? WHERE id = ?;", (datetime.utcnow().isoformat(), row["id"]))

        return {
            "id": row["id"],
            "email": row["email"],
            "role": row["role"],
            "is_active": bool(row["is_active"]),
            "must_change_password": bool(row["must_change_password"])
        }
    finally:
        conn.close()

def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    conn = get_auth_connection()
    try:
        with conn:
            conn.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?);", (token, user_id))
        return token
    finally:
        conn.close()

def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    conn = get_auth_connection()
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
        
        # If user was revoked, purge sessions and return None
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
    conn = get_auth_connection()
    try:
        with conn:
            conn.execute("DELETE FROM sessions WHERE token = ?;", (token,))
    finally:
        conn.close()

def create_user_account(email: str, password: Optional[str] = None, role: str = "user") -> Tuple[bool, str, str]:
    """
    Creates a new user. Returns (success, message, one_time_password).
    """
    clean_email = email.strip().lower()
    if not clean_email or "@" not in clean_email:
        return False, "Invalid email address format.", ""

    one_time_pwd = password.strip() if (password and password.strip()) else f"Pass-{secrets.token_hex(3).upper()}!"
    
    conn = get_auth_connection()
    try:
        with conn:
            cur = conn.execute("SELECT id FROM users WHERE email = ?;", (clean_email,))
            if cur.fetchone():
                return False, f"User with email '{clean_email}' already exists.", ""
            
            pw_hash = hash_password(one_time_pwd)
            conn.execute("""
                INSERT INTO users (email, password_hash, role, is_active, must_change_password)
                VALUES (?, ?, ?, 1, 1);
            """, (clean_email, pw_hash, role))
            
        return True, "User created successfully.", one_time_pwd
    except Exception as e:
        return False, str(e), ""
    finally:
        conn.close()

def list_all_users() -> List[Dict[str, Any]]:
    conn = get_auth_connection()
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
                "created_at": row["created_at"],
                "last_login_at": row["last_login_at"]
            }
            for row in cur.fetchall()
        ]
    finally:
        conn.close()

def set_user_active_status(user_id: int, is_active: bool) -> Tuple[bool, str]:
    conn = get_auth_connection()
    try:
        with conn:
            val = 1 if is_active else 0
            cur = conn.execute("UPDATE users SET is_active = ? WHERE id = ?;", (val, user_id))
            if cur.rowcount == 0:
                return False, "User not found."
            
            # If revoking, terminate all active sessions for this user immediately
            if not is_active:
                conn.execute("DELETE FROM sessions WHERE user_id = ?;", (user_id,))
        return True, "User status updated successfully."
    finally:
        conn.close()

def reset_user_one_time_password(user_id: int, new_password: Optional[str] = None) -> Tuple[bool, str, str]:
    """Admin resets user's password to a one-time password and forces change on next login."""
    one_time_pwd = new_password.strip() if (new_password and new_password.strip()) else f"Pass-{secrets.token_hex(3).upper()}!"
    conn = get_auth_connection()
    try:
        with conn:
            pw_hash = hash_password(one_time_pwd)
            cur = conn.execute("""
                UPDATE users 
                SET password_hash = ?, must_change_password = 1 
                WHERE id = ?;
            """, (pw_hash, user_id))
            if cur.rowcount == 0:
                return False, "User not found.", ""
            # Revoke existing sessions
            conn.execute("DELETE FROM sessions WHERE user_id = ?;", (user_id,))
        return True, "One-time password generated.", one_time_pwd
    finally:
        conn.close()

def user_change_password(user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
    """User changes their one-time or existing password to a new permanent password."""
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters long."
    if old_password == new_password:
        return False, "New password cannot be identical to the old password."

    conn = get_auth_connection()
    try:
        cur = conn.execute("SELECT password_hash FROM users WHERE id = ?;", (user_id,))
        row = cur.fetchone()
        if not row:
            return False, "User not found."

        if not verify_password(old_password, row["password_hash"]):
            return False, "Current / one-time password is incorrect."

        with conn:
            new_hash = hash_password(new_password)
            conn.execute("""
                UPDATE users 
                SET password_hash = ?, must_change_password = 0 
                WHERE id = ?;
            """, (new_hash, user_id))
        return True, "Password changed successfully."
    finally:
        conn.close()

def delete_user_account(user_id: int, current_admin_id: int) -> Tuple[bool, str]:
    if user_id == current_admin_id:
        return False, "You cannot delete your own admin account."
    
    conn = get_auth_connection()
    try:
        with conn:
            cur = conn.execute("DELETE FROM users WHERE id = ?;", (user_id,))
            if cur.rowcount == 0:
                return False, "User not found."
            conn.execute("DELETE FROM sessions WHERE user_id = ?;", (user_id,))
        return True, "User deleted successfully."
    finally:
        conn.close()
