from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database.session import get_db
from app.models.order import Order
from app.services.express_payment import create_express_payment

router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
)


def _extract_order_amount(order: Order) -> float:
    """
    Tenta descobrir o valor total do pedido sem depender
    de um único campo do model.
    """

    possible_fields = [
        "total_amount",
        "total",
        "subtotal",
        "amount",
    ]

    for field in possible_fields:
        value = getattr(order, field, None)
        if value is not None:
            try:
                amount = float(value)
                if amount > 0:
                    return round(amount, 2)
            except (TypeError, ValueError):
                pass

    items = getattr(order, "items", None) or []
    total_from_items = 0.0

    for item in items:
        quantity = getattr(item, "quantity", 0) or 0
        unit_price = (
            getattr(item, "unit_price", None)
            or getattr(item, "price", None)
            or 0
        )

        try:
            total_from_items += float(quantity) * float(unit_price)
        except (TypeError, ValueError):
            continue

    return round(total_from_items, 2)


@router.post("/create")
def create_payment(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Cria uma cobrança para um pedido existente.

    Espera:
    {
        "order_id": 123
    }
    """

    order_id = payload.get("order_id")

    if not order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="order_id é obrigatório"
        )

    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado"
        )

    amount = _extract_order_amount(order)

    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível calcular um valor válido para o pedido"
        )

    try:
        payment_data = create_express_payment(order.id, amount)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc

    if hasattr(order, "payment_status"):
        order.payment_status = "pending"

    if hasattr(order, "payment_reference"):
        order.payment_reference = payment_data.get("reference")

    if hasattr(order, "status"):
        current_status = (getattr(order, "status", "") or "").strip().lower()
        if current_status in {"", "pending", "created"}:
            order.status = "pending_payment"

    db.commit()
    db.refresh(order)

    return {
        "message": "Pagamento criado com sucesso",
        "payment": payment_data,
        "order_id": order.id,
        "payment_status": getattr(order, "payment_status", None),
        "order_status": getattr(order, "status", None),
    }


@router.post("/webhook")
def payment_webhook(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Webhook genérico mantido por compatibilidade.
    O ideal é usar /webhooks/express como endpoint principal.

    Espera:
    {
        "order_id": int,
        "status": "paid" | "pending" | "failed",
        "payment_reference": "EXP-XXXX"
    }
    """

    order_id = payload.get("order_id")
    payment_status = (payload.get("status") or "").strip().lower()
    payment_reference = payload.get("payment_reference") or payload.get("reference")

    if not order_id or not payment_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload inválido"
        )

    if payment_status not in {"paid", "pending", "failed"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Status inválido. Use: paid, pending, failed"
        )

    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado"
        )

    if hasattr(order, "payment_reference") and payment_reference:
        order.payment_reference = payment_reference

    if hasattr(order, "payment_status"):
        order.payment_status = payment_status

    if hasattr(order, "status"):
        if payment_status == "paid":
            order.status = "confirmed"
        elif payment_status == "pending":
            order.status = "pending_payment"
        elif payment_status == "failed":
            order.status = "payment_failed"

    db.commit()
    db.refresh(order)

    return {
        "message": "Webhook processado com sucesso",
        "order_id": order.id,
        "payment_status": getattr(order, "payment_status", None),
        "order_status": getattr(order, "status", None),
    }