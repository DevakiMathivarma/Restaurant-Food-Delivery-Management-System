from tests.conftest import auth_headers

def test_restaurant_hours_validation(client, owner_token):
    response = client.post("/api/v1/restaurants",
        json={"restaurant_name": "Bad Hours", "address": "1 Main Street", "city": "Bengaluru", "phone": "9876500001",
              "cuisine_type": "Indian", "opening_time": "22:00:00", "closing_time": "10:00:00", "delivery_radius": 5.0},
        headers=auth_headers(owner_token))
    assert response.status_code == 422

def test_create_restaurant_success(client, owner_token):
    response = client.post("/api/v1/restaurants",
        json={"restaurant_name": "Spice Garden", "address": "12 MG Road", "city": "Bengaluru", "phone": "9876500002",
              "cuisine_type": "Indian", "opening_time": "10:00:00", "closing_time": "22:00:00", "delivery_radius": 5.0},
        headers=auth_headers(owner_token))
    assert response.status_code == 201
    assert response.json()["data"]["status"] == "CLOSED"

def test_menu_item_price_must_be_positive(client, owner_token):
    restaurant = client.post("/api/v1/restaurants",
        json={"restaurant_name": "Test Rest", "address": "1 Main Street", "city": "Bengaluru", "phone": "9876500003",
              "cuisine_type": "Indian", "opening_time": "10:00:00", "closing_time": "22:00:00", "delivery_radius": 5.0},
        headers=auth_headers(owner_token)).json()["data"]

    response = client.post("/api/v1/menu-items",
        json={"restaurant_id": restaurant["id"], "category": "Main Course", "name": "Bad Item", "price": -50.00},
        headers=auth_headers(owner_token))
    assert response.status_code == 422

def test_menu_item_ownership_scoping(client, owner_token, admin_token):
    restaurant = client.post("/api/v1/restaurants",
        json={"restaurant_name": "Owner Rest", "address": "1 Main Street", "city": "Bengaluru", "phone": "9876500004",
              "cuisine_type": "Indian", "opening_time": "10:00:00", "closing_time": "22:00:00", "delivery_radius": 5.0},
        headers=auth_headers(owner_token)).json()["data"]

    # a different restaurant owner registered by admin, trying to edit someone else's restaurant's menu
    client.post("/api/v1/auth/register",
        json={"full_name": "Other Owner", "email": "other_owner@test.com", "phone": "9666600001", "password": "Test@1234", "role": "RESTAURANT_OWNER"},
        headers=auth_headers(admin_token))
    other_login = client.post("/api/v1/auth/login", data={"username": "other_owner@test.com", "password": "Test@1234"})
    other_token = other_login.json()["access_token"]

    response = client.post("/api/v1/menu-items",
        json={"restaurant_id": restaurant["id"], "category": "Main Course", "name": "Sneaky Item", "price": 100.00},
        headers=auth_headers(other_token))
    assert response.status_code == 403