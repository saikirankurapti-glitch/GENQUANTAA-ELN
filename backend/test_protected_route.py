import urllib.request
import urllib.parse
import json
import os

base_url = "http://127.0.0.1:8000/api/v1"
email = "login_test_me@example.com"
password = "SecurePassword123!"

# 1. Register
payload_reg = {
    "first_name": "Login",
    "last_name": "Test",
    "email": email,
    "password": password
}
data_reg = json.dumps(payload_reg).encode('utf-8')
req_reg = urllib.request.Request(f"{base_url}/auth/register", data=data_reg, headers={'Content-Type': 'application/json'}, method='POST')

try:
    with urllib.request.urlopen(req_reg) as response:
        print("Register Status:", response.status)
except urllib.error.HTTPError as e:
    print("Register Failed:", e.code, e.read().decode())
    # Might already exist, that's fine, proceed to login

# 2. Login
payload_login = {
    "username_or_email": email,
    "password": password
}
data_login = json.dumps(payload_login).encode('utf-8')
req_login = urllib.request.Request(f"{base_url}/auth/login", data=data_login, headers={'Content-Type': 'application/json'}, method='POST')

access_token = None
try:
    with urllib.request.urlopen(req_login) as response:
        print("Login Status:", response.status)
        resp_data = json.loads(response.read().decode())
        access_token = resp_data.get('access_token')
except urllib.error.HTTPError as e:
    print("Login Failed:", e.code, e.read().decode())

# 3. Access Protected Route (e.g. /users/me or /auth/me depending on what exists)
# First let's just try /users/me which is typically protected
if access_token:
    req_me = urllib.request.Request(f"{base_url}/users/me", headers={'Authorization': f'Bearer {access_token}'}, method='GET')
    try:
        with urllib.request.urlopen(req_me) as response:
            print("GET /users/me Status:", response.status)
            print("Response:", response.read().decode())
    except urllib.error.HTTPError as e:
        print("GET /users/me Failed:", e.code, e.read().decode())
