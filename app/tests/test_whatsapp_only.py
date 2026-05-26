from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_whatsapp_link_simple():
    # 1️⃣ login
    login = client.post(
        "/auth/login",
        data={
            "username": "dala@example.com",
            "password": "dala123"
        }
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # 2️⃣ pegar produtos
    products = client.get("/products/", headers=headers)
    assert products.status_code == 200

    product_id = products.json()[0]["id"]

    # 3️⃣ criar pedido
    order = client.post(
        "/orders/",
        headers=headers,
        json={
            "payment_method": "Entrega",
            "items": [
                {"product_id": product_id, "quantity": 1}
            ]
        }
    )
    assert order.status_code == 200

    order_id = order.json()["id"]

    # 4️⃣ gerar link WhatsApp
    whatsapp = client.get(
        f"/orders/{order_id}/whatsapp",
        headers=headers
    )

    assert whatsapp.status_code == 200

    data = whatsapp.json()
    assert "whatsapp_url" in data
    assert data["whatsapp_url"].startswith("https://wa.me/")
