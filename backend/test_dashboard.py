import urllib.request
import urllib.parse
import json

base_url = "http://127.0.0.1:8000/api/v1"
email = "login_test_me@example.com"
password = "SecurePassword123!"

payload_login = {
    "username_or_email": email,
    "password": password
}
data_login = json.dumps(payload_login).encode('utf-8')
req_login = urllib.request.Request(f"{base_url}/auth/login", data=data_login, headers={'Content-Type': 'application/json'}, method='POST')

access_token = None
try:
    with urllib.request.urlopen(req_login) as response:
        resp_data = json.loads(response.read().decode())
        access_token = resp_data.get('access_token')
except urllib.error.HTTPError as e:
    print("Login Failed:", e.code, e.read().decode())

if access_token:
    req_dash = urllib.request.Request(f"{base_url}/dashboard/summary", headers={'Authorization': f'Bearer {access_token}'}, method='GET')
    try:
        with urllib.request.urlopen(req_dash) as response:
            print("GET /dashboard/summary Status:", response.status)
    except urllib.error.HTTPError as e:
        print("GET /dashboard/summary Failed:", e.code, e.read().decode())

    req_me = urllib.request.Request(f"{base_url}/auth/me", headers={'Authorization': f'Bearer {access_token}'}, method='GET')
    try:
        with urllib.request.urlopen(req_me) as response:
            print("GET /auth/me Status:", response.status)
    except urllib.error.HTTPError as e:
        print("GET /auth/me Failed:", e.code, e.read().decode())
