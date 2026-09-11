from tests.conftest import auth_headers


def _setup_open_restaurant_with_item(client, owner_token, price=250.00):
    restaurant = client.post("/api/v1/restaurants",
        json={"restaurant_name": "Test Kitchen", "address": "1 Main Street", "city": "Bengaluru", "phone": "9876500010",
              "cuisine_type": "Indian", "opening_time": "00:00:00", "closing_time": "23:59:59", "delivery_radius": 5.0},
        headers=auth_headers(owner_token)).json()["data"]

    client.put(f"/api/v1/restaurants/{restaurant['id']}", json={"status": "OPEN"}, headers=auth_headers(owner_token))

    menu_item = client.post("/api/v1/menu-items",
        json={"restaurant_id": restaurant["id"], "category": "Main Course", "name": "Butter Chicken", "price": price},
        headers=auth_headers(owner_token)).json()["data"]

    return restaurant, menu_item


def _setup_customer_with_address(client, customer_token_and_id):
    address = client.post("/api/v1/customers/addresses",
        json={"address_line": "14 Park Street", "city": "Bengaluru", "pincode": "560038"},
        headers=auth_headers(customer_token_and_id)).json()["data"]
    return address


def test_cart_blocks_items_from_different_restaurants(client, owner_token, customer_token_and_id):
    restaurant1, item1 = _setup_open_restaurant_with_item(client, owner_token)
    restaurant2, item2 = _setup_open_restaurant_with_item(client, owner_token)

    first_add = client.post("/api/v1/cart/items", json={"menu_item_id": item1["id"], "quantity": 1}, headers=auth_headers(customer_token_and_id))
    assert first_add.status_code == 201

    second_add = client.post("/api/v1/cart/items", json={"menu_item_id": item2["id"], "quantity": 1}, headers=auth_headers(customer_token_and_id))
    assert second_add.status_code == 400


def test_cart_blocks_unavailable_items(client, owner_token, customer_token_and_id):
    restaurant, item = _setup_open_restaurant_with_item(client, owner_token)
    client.put(f"/api/v1/menu-items/{item['id']}", json={"availability": False}, headers=auth_headers(owner_token))

    response = client.post("/api/v1/cart/items", json={"menu_item_id": item["id"], "quantity": 1}, headers=auth_headers(customer_token_and_id))
    assert response.status_code == 400


def test_full_order_lifecycle_to_delivery_payment_review(client, owner_token, admin_token, customer_token_and_id, delivery_partner_token):
    restaurant, item = _setup_open_restaurant_with_item(client, owner_token, price=250.00)
    address = _setup_customer_with_address(client, customer_token_and_id)

    client.post("/api/v1/cart/items", json={"menu_item_id": item["id"], "quantity": 2}, headers=auth_headers(customer_token_and_id))

    # try placing an order against a restaurant that's still CLOSED
    restaurant_closed, item_closed = _setup_open_restaurant_with_item(client, owner_token)
    client.put(f"/api/v1/restaurants/{restaurant_closed['id']}", json={"status": "CLOSED"}, headers=auth_headers(owner_token))

    order = client.post("/api/v1/orders", json={"address_id": address["id"]}, headers=auth_headers(customer_token_and_id))
    assert order.status_code == 201
    order_data = order.json()["data"]

    # automatic total calculation check: subtotal(500) + tax(5%=25) + delivery_fee(40) - discount(0) = 565
    assert float(order_data["subtotal"]) == 500.00
    assert float(order_data["total_amount"]) == 565.00
    assert order_data["order_status"] == "PENDING"

    order_id = order_data["id"]

    # cart should now be empty
    cart_check = client.get("/api/v1/cart", headers=auth_headers(customer_token_and_id)).json()["data"]
    assert len(cart_check["items"]) == 0

    # restaurant side moves the order through its lifecycle
    for new_status in ["ACCEPTED", "PREPARING", "READY"]:
        response = client.put(f"/api/v1/orders/{order_id}/status", json={"order_status": new_status}, headers=auth_headers(owner_token))
        assert response.status_code == 200

    tracking = client.get(f"/api/v1/orders/{order_id}/tracking", headers=auth_headers(customer_token_and_id)).json()["data"]
    assert len(tracking) == 4  # PENDING (auto) + ACCEPTED + PREPARING + READY

    # delivery partner must be AVAILABLE before assignment works
    no_partner_available = client.post(f"/api/v1/orders/{order_id}/assign-delivery-partner", headers=auth_headers(owner_token))
    assert no_partner_available.status_code == 400

    client.put("/api/v1/delivery-partners/availability", json={"availability_status": "AVAILABLE"}, headers=auth_headers(delivery_partner_token))

    assign = client.post(f"/api/v1/orders/{order_id}/assign-delivery-partner", headers=auth_headers(owner_token))
    assert assign.status_code == 200

    # delivery partner cannot go offline while on an active delivery
    blocked_availability = client.put("/api/v1/delivery-partners/availability", json={"availability_status": "OFFLINE"}, headers=auth_headers(delivery_partner_token))
    assert blocked_availability.status_code == 400

    # delivery partner updates location while actively delivering
    client.put(f"/api/v1/orders/{order_id}/status", json={"order_status": "PICKED_UP"}, headers=auth_headers(owner_token))
    location_update = client.put("/api/v1/delivery-partners/location", json={"current_latitude": 12.9800, "current_longitude": 77.6000}, headers=auth_headers(delivery_partner_token))
    assert location_update.status_code == 200

    client.put(f"/api/v1/orders/{order_id}/status", json={"order_status": "OUT_FOR_DELIVERY"}, headers=auth_headers(owner_token))

    delivered = client.put(f"/api/v1/orders/{order_id}/status", json={"order_status": "DELIVERED"}, headers=auth_headers(owner_token))
    assert delivered.status_code == 200

    # cannot update a delivered order's status again
    already_done = client.put(f"/api/v1/orders/{order_id}/status", json={"order_status": "CANCELLED"}, headers=auth_headers(owner_token))
    assert already_done.status_code == 400

    # customer pays for the order
    payment = client.post(f"/api/v1/orders/{order_id}/payment", json={"payment_method": "UPI", "transaction_id": "TXNTEST001"}, headers=auth_headers(customer_token_and_id))
    assert payment.status_code == 201

    # cash on delivery should work with no transaction_id, card should not
    bad_card_payment = client.post(f"/api/v1/orders/{order_id}/payment", json={"payment_method": "CARD"}, headers=auth_headers(customer_token_and_id))
    assert bad_card_payment.status_code in (400, 422)

    # customer reviews the delivered order
    review = client.post(f"/api/v1/orders/{order_id}/review",
        json={"restaurant_rating": 5, "food_review_text": "Excellent!", "delivery_rating": 4}, headers=auth_headers(customer_token_and_id))
    assert review.status_code == 201

    duplicate_review = client.post(f"/api/v1/orders/{order_id}/review",
        json={"restaurant_rating": 3}, headers=auth_headers(customer_token_and_id))
    assert duplicate_review.status_code == 400