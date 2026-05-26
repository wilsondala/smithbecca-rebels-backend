import os

from app.models.order import Order
from app.services.order_message import build_order_message
from app.services.whatsapp import generate_whatsapp_link

DEFAULT_SELLER_PHONE = "5511967864913"


def notify_payment_confirmed(order: Order) -> str:
    """
    Gera o link de WhatsApp para avisar a equipa/vendedor
    quando um pagamento for confirmado.
    """

    base_message = build_order_message(order)
    reference = getattr(order, "payment_reference", None) or "N/D"

    message = (
        f"{base_message}\n\n"
        "✅ *Pagamento confirmado via Express*\n"
        f"🧾 Referência: {reference}\n"
        "📦 Pedido pronto para preparação/entrega."
    )

    seller_phone = os.getenv("SELLER_WHATSAPP_PHONE", DEFAULT_SELLER_PHONE)
    return generate_whatsapp_link(seller_phone, message)