import asyncio
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)

def run_tests():
    # 1. Invalid password -> HTTP 422
    payload_invalid_password = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "password": "short"
    }
    response = client.post("/api/v1/auth/register", json=payload_invalid_password)
    print("Invalid Password Response:", response.status_code, response.json())
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    # 2. Valid password -> User registration succeeds
    payload_valid = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test_unique1@example.com",
        "password": "ValidPassword123!"
    }
    response = client.post("/api/v1/auth/register", json=payload_valid)
    print("Valid Registration Response:", response.status_code, response.json())
    assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"

    # 3. Duplicate email -> Appropriate 400 or 409
    response = client.post("/api/v1/auth/register", json=payload_valid)
    print("Duplicate Email Response:", response.status_code, response.json())
    assert response.status_code in [400, 409], f"Expected 400/409, got {response.status_code}"

if __name__ == "__main__":
    run_tests()
