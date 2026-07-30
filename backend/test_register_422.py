import urllib.request
import urllib.parse
import json

url = "http://127.0.0.1:8000/api/v1/auth/register"
payload = {
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane.doe3@example.com",
    "password": "SecurePassword123!"
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')

try:
    with urllib.request.urlopen(req) as response:
        print(response.status)
        print(response.read().decode())
except urllib.error.HTTPError as e:
    print(e.code)
    print(e.read().decode())
