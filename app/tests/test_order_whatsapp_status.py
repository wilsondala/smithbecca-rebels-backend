def test_order_status_changes_to_sent(client, auth_headers):
    # 1️⃣ cria pedido
    create = client.post(
        "/orders/",
        headers=auth_headers,
        json={
            "payment_method": "entrega",
            "items": [
                {"product_id": 1, "quantity": 1}
            ]
        }
    )
    assert create.status_code == 200
    order_id = create.json()["id"]

    # 2️⃣ gera link do WhatsApp
    response = client.get(
        f"/orders/{order_id}/whatsapp",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert "whatsapp_url" in response.json()

    # 3️⃣ verifica status
    orders = client.get(
        "/orders/me",
        headers=auth_headers
    ).json()

    assert orders[0]["status"] == "sent"
