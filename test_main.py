import os
import sys
import pytest
from fastapi.testclient import TestClient
from main import app, fake_users_db, products_db, orders_db, pwd_context, get_password_hash

client = TestClient(app)

# Test data
test_user = {
    "username": "testuser",
    "full_name": "Test User",
    "email": "testuser@example.com",
    "hashed_password": get_password_hash("testpass"),
    "disabled": False,
}

test_product = {
    "id": "prod-123",
    "name": "Test Product",
    "description": "A test product",
    "price": 9.99,
    "tax": 1.99
}

test_order = {
    "id": "order-123",
    "user_id": "testuser",
    "products": [test_product],
    "total": 11.98,
    "status": "pending"
}

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup: Add test user to fake db
    fake_users_db[test_user["username"]] = test_user
    
    # Run the test
    yield
    
    # Teardown: Clear test data
    fake_users_db.pop(test_user["username"], None)
    products_db.clear()
    orders_db.clear()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "ok"

def test_login_for_access_token():
    # Test successful login
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
    
    # Test wrong password
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "wrongpass"}
    )
    assert response.status_code == 401
    
    # Test non-existent user
    response = client.post(
        "/token",
        data={"username": "nonexistent", "password": "testpass"}
    )
    assert response.status_code == 401

def test_read_users_me():
    # First get a token
    token_response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpass"}
    )
    token = token_response.json()["access_token"]
    
    # Test authorized access
    response = client.get(
        "/users/me/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
    
    # Test unauthorized access
    response = client.get(
        "/users/me/",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401

def test_product_crud():
    # Get token first
    token_response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpass"}
    )
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create product
    response = client.post(
        "/products/",
        json=test_product,
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["id"] == "prod-123"
    
    # Get product
    response = client.get("/products/prod-123")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Product"
    
    # Get all products
    response = client.get("/products/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    
    # Try to create duplicate product
    response = client.post(
        "/products/",
        json=test_product,
        headers=headers
    )
    assert response.status_code == 400

def test_order_crud():
    # Get token first
    token_response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpass"}
    )
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # First create a product that will be in the order
    client.post(
        "/products/",
        json=test_product,
        headers=headers
    )
    
    # Create order
    response = client.post(
        "/orders/",
        json=test_order,
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["id"] == "order-123"
    
    # Get order
    response = client.get(
        "/orders/order-123",
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["total"] == 11.98
    
    # Try to get order with wrong user (should fail)
    # Create another test user
    fake_users_db["anotheruser"] = {
        "username": "anotheruser",
        "full_name": "Another User",
        "email": "another@example.com",
        "hashed_password": get_password_hash("anotherpass"),
        "disabled": False,
    }
    
    # Get token for another user
    another_token_response = client.post(
        "/token",
        data={"username": "anotheruser", "password": "anotherpass"}
    )
    another_token = another_token_response.json()["access_token"]
    another_headers = {"Authorization": f"Bearer {another_token}"}
    
    # Try to access the order
    response = client.get(
        "/orders/order-123",
        headers=another_headers
    )
    assert response.status_code == 403

def test_order_with_nonexistent_product():
    # Get token first
    token_response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpass"}
    )
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create order with non-existent product
    bad_order = test_order.copy()
    bad_order["products"][0]["id"] = "nonexistent-product"
    
    response = client.post(
        "/orders/",
        json=bad_order,
        headers=headers
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]