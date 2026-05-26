from app.services.whatsapp import generate_whatsapp_link

def test_generate_whatsapp_link():
    phone = "5511967864913"
    message = "Pedido #1 - Total: 1500 Kz"

    link = generate_whatsapp_link(phone, message)

    assert link.startswith("https://wa.me/5511967864913")
    assert "Pedido+%231" in link or "Pedido+%231+-+Total" in link
