import unittest
from fastapi.testclient import TestClient
from main import app, fake_users_db, products_db, orders_db, pwd_context

client = TestClient(app)

# Test data
test_user = {
    "username": "testuser",
    "full_name": "Test User",
    "email": "testuser@example.com",
    "hashed_password": pwd_context.hash("testpass"),
    "disabled": False,
}

class APITestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Setup for all tests"""
        fake_users_db[test_user["username"]] = test_user

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all tests"""
        fake_users_db.clear()
        products_db.clear()
        orders_db.clear()

    def test_health_check(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertIn("status", response.json())
        self.assertEqual(response.json()["status"], "ok")

    def test_login_for_access_token(self):
        # Test successful login
        response = client.post(
            "/token",
            data={"username": "testuser", "password": "testpass"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())

        # Test failed login
        response = client.post(
            "/token",
            data={"username": "testuser", "password": "wrongpass"}
        )
        self.assertEqual(response.status_code, 401)

    def test_product_crud(self):
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
        self.assertEqual(response.status_code, 200)

        # Verify product
        response = client.get("/products/prod-123")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Test Product")

if __name__ == "__main__":
    unittest.main()
