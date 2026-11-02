import sys
import os
import time
import requests

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=" * 60)
    print("  AUTOMATED END-TO-END VERIFICATION TEST")
    print("=" * 60)

    # 1. Health Check
    res = requests.get(f"{BASE_URL}/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] Health Check OK")

    # 2. Admin Login
    login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@example.com",
        "password": "admin123"
    })
    assert login_res.status_code == 200, f"Admin login failed: {login_res.text}"
    admin_data = login_res.json()
    admin_token = admin_data["token"]
    assert admin_data["user"]["role"] == "admin"
    print(f"[PASS] Admin Logged In successfully (Token: {admin_token[:12]}...)")

    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 3. Create a User via Admin Portal
    create_res = requests.post(f"{BASE_URL}/api/admin/users", headers=admin_headers, json={
        "email": "field_staff@example.com",
        "role": "user"
    })
    assert create_res.status_code == 200, f"Create user failed: {create_res.text}"
    user_info = create_res.json()
    otp = user_info["one_time_password"]
    print(f"[PASS] User created: {user_info['email']} with One-Time Password: {otp}")

    # 4. User Log In with One-Time Password
    user_login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "field_staff@example.com",
        "password": otp
    })
    assert user_login_res.status_code == 200, f"User login failed: {user_login_res.text}"
    user_login_data = user_login_res.json()
    user_token = user_login_data["token"]
    assert user_login_data["user"]["must_change_password"] is True, "Expected must_change_password=True"
    print("[PASS] User Logged In with OTP - Flag must_change_password is True")

    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 5. User tries searching before changing password -> Expect 403
    search_blocked_res = requests.get(f"{BASE_URL}/api/search?query=maruti", headers=user_headers)
    assert search_blocked_res.status_code == 403, f"Expected 403 before password change, got {search_blocked_res.status_code}"
    print("[PASS] Search correctly blocked before password change (HTTP 403)")

    # 6. User Changes One-Time Password to permanent password
    change_res = requests.post(f"{BASE_URL}/api/auth/change-password", headers=user_headers, json={
        "old_password": otp,
        "new_password": "MyNewSecretPassword2026!"
    })
    assert change_res.status_code == 200, f"Password change failed: {change_res.text}"
    print("[PASS] Password successfully updated to permanent password")

    # 7. User searches data now
    t0 = time.time()
    search_res = requests.get(f"{BASE_URL}/api/search?query=maruti&limit=25", headers=user_headers)
    t1 = time.time()
    assert search_res.status_code == 200, f"Search failed: {search_res.text}"
    search_data = search_res.json()
    print(f"[PASS] Search query successful: Found {search_data['total']} records in {(t1-t0)*1000:.2f}ms")

    # 8. User tries to ingest data -> Expect 403 (Admin only)
    import_res = requests.post(f"{BASE_URL}/api/import", headers=user_headers, files={"files": ("test.csv", b"dummy")})
    assert import_res.status_code == 403, f"Expected 403 for user importing data, got {import_res.status_code}"
    print("[PASS] Data ingestion correctly restricted to Admin (User got HTTP 403)")

    # 9. User tries to view admin users -> Expect 403
    users_res = requests.get(f"{BASE_URL}/api/admin/users", headers=user_headers)
    assert users_res.status_code == 403, f"Expected 403 for user accessing user management, got {users_res.status_code}"
    print("[PASS] Admin user management correctly restricted to Admin (User got HTTP 403)")

    # 10. Admin revokes User's access
    list_users_res = requests.get(f"{BASE_URL}/api/admin/users", headers=admin_headers)
    all_users = list_users_res.json()["users"]
    target_user = next(u for u in all_users if u["email"] == "field_staff@example.com")
    
    revoke_res = requests.patch(f"{BASE_URL}/api/admin/users/{target_user['id']}/status", headers=admin_headers, json={
        "is_active": False
    })
    assert revoke_res.status_code == 200, f"Revoke failed: {revoke_res.text}"
    print("[PASS] Admin revoked User access successfully")

    # 11. User tries to make a request with old token -> Expect 401/403
    revoked_req = requests.get(f"{BASE_URL}/api/search?query=maruti", headers=user_headers)
    assert revoked_req.status_code in [401, 403], f"Expected 401/403 for revoked session, got {revoked_req.status_code}"
    print("[PASS] Revoked user's active session immediately rejected (HTTP 401/403)")

    # 12. User tries to log in again -> Expect 403
    revoked_login = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "field_staff@example.com",
        "password": "MyNewSecretPassword2026!"
    })
    assert revoked_login.status_code == 403, f"Expected 403 for revoked login, got {revoked_login.status_code}"
    print("[PASS] Revoked user blocked from logging in (HTTP 403)")

    # 13. Admin cleans up test user
    del_res = requests.delete(f"{BASE_URL}/api/admin/users/{target_user['id']}", headers=admin_headers)
    assert del_res.status_code == 200, f"Delete failed: {del_res.text}"
    print("[PASS] Admin deleted test user successfully")

    print("=" * 60)
    print("  ALL 13 TESTS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
