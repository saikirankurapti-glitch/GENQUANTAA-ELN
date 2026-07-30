import urllib.request
import urllib.parse
import json

base_url = "http://127.0.0.1:8000/api/v1/auth"
email = "login_test@example.com"
password = "SecurePassword123!"

# 1. Register
payload_reg = {
    "first_name": "Login",
    "last_name": "Test",
    "email": email,
    "password": password
}
data_reg = json.dumps(payload_reg).encode('utf-8')
req_reg = urllib.request.Request(f"{base_url}/register", data=data_reg, headers={'Content-Type': 'application/json'}, method='POST')

try:
    with urllib.request.urlopen(req_reg) as response:
        print("Register Status:", response.status)
except urllib.error.HTTPError as e:
    print("Register Failed:", e.code, e.read().decode())

# 2. Login
payload_login = {
    "username_or_email": email,
    "password": password
}
data_login = json.dumps(payload_login).encode('utf-8')
req_login = urllib.request.Request(f"{base_url}/login", data=data_login, headers={'Content-Type': 'application/json'}, method='POST')

try:
    with urllib.request.urlopen(req_login) as response:
        print("Login Status:", response.status)
        print("Response:", response.read().decode())
except urllib.error.HTTPError as e:
    print("Login Failed:", e.code, e.read().decode())
