from tests.conftest import auth_headers

def test_admin_login(client, admin_token):
    assert admin_token is not None

def test_register_requires_admin(client):
    response = client.post("/api/v1/auth/register",
        json={"full_name": "Sneaky", "email": "sneaky@test.com", "phone": "9555555555", "password": "Test@1234", "role": "RESTAURANT_OWNER"})
    assert response.status_code == 401

def test_customer_self_registers_no_token_needed(client):
    response = client.post("/api/v1/customers",
        json={"full_name": "Self Reg", "email": "selfreg@test.com", "phone": "9888888888", "password": "Test@1234"})
    assert response.status_code == 201

def test_delivery_partner_self_registers(client):
    response = client.post("/api/v1/delivery-partners",
        json={"full_name": "Self Rider", "email": "selfrider@test.com", "phone": "9777777777", "password": "Test@1234", "vehicle_type": "BIKE", "vehicle_number": "KA-02-CD-2222"})
    assert response.status_code == 201

def test_duplicate_vehicle_number_blocked(client):
    client.post("/api/v1/delivery-partners",
        json={"full_name": "Rider One", "email": "rider1@test.com", "phone": "9666666601", "password": "Test@1234", "vehicle_type": "BIKE", "vehicle_number": "KA-03-XX-9999"})
    response = client.post("/api/v1/delivery-partners",
        json={"full_name": "Rider Two", "email": "rider2@test.com", "phone": "9666666602", "password": "Test@1234", "vehicle_type": "SCOOTER", "vehicle_number": "KA-03-XX-9999"})
    assert response.status_code == 400

def test_activation_blocks_self_change(client, admin_token):
    me = client.get("/api/v1/auth/me", headers=auth_headers(admin_token)).json()["data"]
    response = client.put(f"/api/v1/auth/{me['id']}/activation", json={"is_active": False}, headers=auth_headers(admin_token))
    assert response.status_code == 400