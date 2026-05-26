from decimal import Decimal
from app.models.order import Order


def _money(value) -> str:
    try:
        amount = Decimal(str(value or 0))
    except Exception:
        amount = Decimal("0")
    return f"{amount:,.0f} Kz".replace(",", ".")


def _customer_name(order: Order) -> str:
    if getattr(order, "customer_name", None):
        return order.customer_name
    if getattr(order, "user", None) and getattr(order.user, "name", None):
        return order.user.name
    return "Cliente"


def _customer_phone(order: Order) -> str:
    if getattr(order, "user", None) and getattr(order.user, "phone", None):
        return order.user.phone
    return "Não informado"


def _payment_label(order: Order) -> str:
    payment_method = str(getattr(order, "payment_method", "") or "").strip().lower()

    labels = {
        "entrega": "Pagamento na entrega",
        "transferencia": "Transferência",
        "express": "Expresso",
    }
    return labels.get(payment_method, payment_method or "Não informado")


def _delivery_text(order: Order) -> str:
    lines = []

    if getattr(order, "customer_name", None):
        lines.append(f"Nome: {order.customer_name}")

    if getattr(order, "address_line", None):
        lines.append(f"Morada: {order.address_line}")

    if getattr(order, "neighborhood", None):
        lines.append(f"Bairro: {order.neighborhood}")

    if getattr(order, "delivery_address", None):
        lines.append(f"Localização: {order.delivery_address}")

    if getattr(order, "reference", None):
        lines.append(f"Referência: {order.reference}")

    if not lines:
        return "Não informado"

    return "\n".join(lines)


def _order_total(order: Order):
    total = getattr(order, "total", None)
    if total is None:
        total = getattr(order, "total_amount", None)
    if total is None:
        total = 0
    return total


def build_order_message(order: Order) -> str:
    lines = []
    lines.append(" *NOVO PEDIDO RECEBIDO*")
    lines.append("")
    lines.append(f"👤 Cliente: {_customer_name(order)}")
    lines.append(f"📞 Telefone: {_customer_phone(order)}")
    lines.append(f"🧾 Pedido: #{order.id}")
    lines.append("")
    lines.append("📦 *Itens do pedido:*")

    if getattr(order, "items", None):
        for item in order.items:
            product_name = (
                item.product.name
                if getattr(item, "product", None) and getattr(item.product, "name", None)
                else "Produto"
            )
            subtotal = (item.price or 0) * (item.quantity or 0)
            lines.append(
                f"- {product_name} (x{item.quantity}) — {_money(subtotal)}"
            )
    else:
        lines.append("- Sem itens")

    lines.append("")
    lines.append(f" Total: {_money(_order_total(order))}")
    lines.append(f"Pagamento: {_payment_label(order)}")
    lines.append("")
    lines.append("📍 *Entrega:*")
    lines.append(_delivery_text(order))

    return "\n".join(lines)


def build_customer_confirmation_message(order: Order) -> str:
    return "\n".join(
        [
            "*Pedido recebido com sucesso!*",
            "",
            f"Número do pedido: #{order.id}",
            f"Total: {_money(_order_total(order))}",
            f"Pagamento: {_payment_label(order)}",
            "",
            "Recebemos o seu pedido e em breve entraremos em contacto.",
            "Obrigado por comprar na *Paixão Angola*",
        ]
    )