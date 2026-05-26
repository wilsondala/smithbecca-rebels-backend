def test_payment_on_delivery(client, auth_headers):
    response = client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "payment_method": "entrega",
            "delivery_address": "Benfica",
            "items": [
                {"product_id": 1, "quantity": 1}
            ]
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_method"] == "entrega"
    assert data["payment_status"] == "pending"
