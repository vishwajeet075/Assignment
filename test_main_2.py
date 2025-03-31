from nose.tools import assert_equal, assert_true, assert_false, assert_raises
from app.main import app, fake_users_db, products_db, orders_db, pwd_context, get_password_hash
from fastapi.testclient import TestClient
import json

client = TestClient(app)

# Test data remains the same as your pytest version
test_user = {
    "username": "testuser",
    "full_name": "Test User",
    "email": "testuser@example.com",
    "hashed_password": pwd_context.hash("testpass"),
    "disabled": False,
}

def setup_module():
    """Setup for all tests"""
    fake_users_db[test_user["username"]] = test_user

def teardown_module():
    """Cleanup after all tests"""
    fake_users_db.clear()
    products_db.clear()
    orders_db.clear()

def test_health_check():
    response = client.get("/health")
    assert_equal(response.status_code, 200)
    assert_true("status" in response.json())
    assert_equal(response.json()["status"], "ok")

def test_login_for_access_token():
    # Test successful login
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpass"}
    )
    assert_equal(response.status_code, 200)
    assert_true("access_token" in response.json())
    
    # Test failed login
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "wrongpass"}
    )
    assert_equal(response.status_code, 401)

def test_product_crud():
    # Get token first
    token_response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpass"}
    )
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create product
    test_product = {
        "id": "prod-123",
        "name": "Test Product",
        "price": 9.99
    }
    response = client.post(
        "/products/",
        json=test_product,
        headers=headers
    )
    assert_equal(response.status_code, 200)
    
    # Verify product
    response = client.get("/products/prod-123")
    assert_equal(response.json()["name"], "Test Product")