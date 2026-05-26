from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database.session import get_db
from app.models.order import Order
from app.schemas.webhook import ExpressWebhook
from app.services.payment_notification import notify_payment_confirmed

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/express")
def express_payment_webhook(
    payload: ExpressWebhook,
    db: Session = Depends(get_db)
):
    """
    Webhook principal do pagamento Express.
    Esse endpoint deve ser chamado pelo provedor/gateway quando o pagamento mudar de estado.
    """

    payment_status = (payload.status or "").strip().lower()

    if payment_status not in {"paid", "pending", "failed"}:
        raise HTTPException(
            status_code=422,
            detail="Status inválido. Use: paid, pending, failed"
        )

    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == payload.order_id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    current_payment_status = (getattr(order, "payment_status", "") or "").strip().lower()
    already_paid = current_payment_status == "paid"

    if hasattr(order, "payment_reference") and getattr(payload, "payment_reference", None):
        order.payment_reference = payload.payment_reference

    # -------------------------
    # ✅ PAGAMENTO CONFIRMADO
    # -------------------------
    if payment_status == "paid":
        if hasattr(order, "payment_status"):
            order.payment_status = "paid"

        if hasattr(order, "status"):
            current_order_status = (getattr(order, "status", "") or "").strip().lower()
            if current_order_status in {"pending", "created", "pending_payment", "payment_pending"}:
                order.status = "confirmed"

        for item in getattr(order, "items", []) or []:
            current_item_status = (getattr(item, "status", "") or "").strip().lower()
            if current_item_status in {"", "pending", "paid"}:
                item.status = "preparing"

        db.commit()
        db.refresh(order)

        whatsapp_link = None

        if not already_paid:
            try:
                whatsapp_link = notify_payment_confirmed(order)
            except Exception as exc:
                print("Falha notify_payment_confirmed:", exc)

        return {
            "message": "Pagamento confirmado. Pedido em preparação.",
            "order_id": order.id,
            "payment_status": getattr(order, "payment_status", None),
            "order_status": getattr(order, "status", None),
            "whatsapp_url": whatsapp_link
        }

    # -------------------------
    # ⏳ PAGAMENTO PENDENTE
    # -------------------------
    if payment_status == "pending":
        if hasattr(order, "payment_status"):
            order.payment_status = "pending"

        if hasattr(order, "status"):
            current_order_status = (getattr(order, "status", "") or "").strip().lower()
            if current_order_status in {"", "pending", "created"}:
                order.status = "pending_payment"

        db.commit()
        db.refresh(order)

        return {
            "message": "Pagamento pendente registrado",
            "order_id": order.id,
            "payment_status": getattr(order, "payment_status", None),
            "order_status": getattr(order, "status", None),
        }

    # -------------------------
    # ❌ PAGAMENTO FALHOU
    # -------------------------
    if hasattr(order, "payment_status"):
        order.payment_status = "failed"

    if hasattr(order, "status"):
        order.status = "payment_failed"

    db.commit()
    db.refresh(order)

    return {
        "message": "Pagamento recusado",
        "order_id": order.id,
        "payment_status": getattr(order, "payment_status", None),
        "order_status": getattr(order, "status", None),
    }