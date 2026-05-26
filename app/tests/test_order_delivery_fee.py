def test_order_has_delivery_fee(client, auth_headers):
    response = client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "payment_method": "entrega",
            "delivery_address": "Talatona",
            "items": [
                {"product_id": 1, "quantity": 1}
            ]
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "delivery_fee" in data
    assert float(data["delivery_fee"]) > 0

    assert "total_amount" in data
    assert float(data["total_amount"]) >= float(data["delivery_fee"])
