import requests
import pytest

BASE_URL = "http://localhost:8004"
API_BASE = f"{BASE_URL}/api/v1"

@pytest.fixture(scope="module")
def test_data_setup():
    # Este test asume que 1-test_data_setup.py ya fue ejecutado
    # y los usuarios de prueba existen en la base de datos
    pass

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("healthy", "degraded")

@pytest.fixture(scope="module")
def login_token():
    login_data = {
        "email": "test1@google.com",
        "password": "Abc@1234"
    }
    response = requests.post(
        f"{API_BASE}/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    return data["token"]

def test_verify_token(login_token):
    response = requests.get(
        f"{API_BASE}/verify-token",
        params={"token": login_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "email" in data
    assert "roles" in data

@pytest.mark.parametrize("email,password", [
    ("maria@test.com", "Test@1234"),
    ("pedro@test.com", "Password@1234")
])
def test_other_users(email, password):
    response = requests.post(
        f"{API_BASE}/login",
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "roles" in data

def test_invalid_login():
    login_data = {
        "email": "invalid@test.com",
        "password": "wrongpassword"
    }
    response = requests.post(
        f"{API_BASE}/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 401
