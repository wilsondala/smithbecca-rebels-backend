import json
from decimal import Decimal
from threading import Thread

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate, OrderOut
from app.services.whatsapp_service import send_order_notifications

router = APIRouter(prefix="/orders", tags=["Orders"])


def build_delivery_address(order: OrderCreate) -> str | None:
    parts = [
        f"Nome do Cliente: {order.customer_name.strip()}" if order.customer_name else "",
        f"Morada: {order.address_line.strip()}" if order.address_line else "",
        f"Bairro: {order.neighborhood.strip()}" if order.neighborhood else "",
        f"Localização: {order.delivery_address.strip()}" if order.delivery_address else "",
        f"Referência: {order.reference.strip()}" if order.reference else "",
    ]
    final_text = "\n".join([p for p in parts if p.strip()])
    return final_text or order.delivery_address


def _load_order_with_relations(db: Session, order_id: int) -> Order | None:
    return (
        db.query(Order)
        .options(
            joinedload(Order.user),
            joinedload(Order.items).joinedload(OrderItem.product),
        )
        .filter(Order.id == order_id)
        .first()
    )


def _dispatch_order_notifications(order: Order):
    try:
        send_order_notifications(order)
    except Exception as e:
        print("Falha ao enviar notificação WhatsApp:", e)


def _extract_product_image(product: Product) -> str | None:
    if not product:
        return None

    raw_images = getattr(product, "images", None)

    if not raw_images:
        return None

    # Caso já seja lista
    if isinstance(raw_images, list):
        for img in raw_images:
            if str(img or "").strip():
                return img
        return None

    # Caso seja string
    if isinstance(raw_images, str):
        value = raw_images.strip()
        if not value:
            return None

        try:
            parsed = json.loads(value)

            if isinstance(parsed, list):
                for img in parsed:
                    if str(img or "").strip():
                        return img

            if isinstance(parsed, str) and parsed.strip():
                return parsed.strip()

        except Exception:
            return value

    return None


def _build_safe_order_item(item: OrderItem) -> OrderItem:
    return OrderItem(
        id=item.id,
        order_id=item.order_id,
        product_id=item.product_id or 0,
        quantity=item.quantity or 0,
        price=item.price or Decimal("0.00"),
        status=item.status or "unknown",
        product_image=item.product_image,
        product=item.product if item.product else Product(
            id=0,
            name="Produto não disponível",
            price=Decimal("0.00"),
            stock=0,
        ),
    )


@router.get("/latest")
def get_latest_orders(db: Session = Depends(get_db)):
    try:
        orders = (
            db.query(Order)
            .options(
                joinedload(Order.user),
                joinedload(Order.items).joinedload(OrderItem.product),
            )
            .filter(Order.status == "confirmed")
            .order_by(desc(Order.id))
            .limit(5)
            .all()
        )

        results = []

        for order in orders:
            if not order.items:
                continue

            first_item = order.items[0]

            first_name = "Cliente"

            if order.customer_name:
                first_name = order.customer_name.split(" ")[0]
            elif order.user:
                user_name = getattr(order.user, "name", None)
                if user_name:
                    first_name = user_name.split(" ")[0]

            city_text = (
                order.neighborhood
                or order.address_line
                or order.delivery_address
                or "Angola"
            )

            results.append(
                {
                    "id": order.id,
                    "first_name": first_name,
                    "city": city_text,
                    "product_name": first_item.product.name if first_item.product else "Produto",
                    "created_at": order.created_at,
                }
            )

        return results

    except Exception as e:
        print("[orders/latest] erro:", repr(e))
        return []


@router.get("/", response_model=list[OrderOut])
def get_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product)
    )

    if user.role != "admin":
        query = query.filter(Order.user_id == user.id)

    orders = query.order_by(desc(Order.id)).all()

    for order in orders:
        safe_items = []
        for item in order.items:
            safe_items.append(_build_safe_order_item(item))
        order.items = safe_items

    return orders


@router.get("/me", response_model=list[OrderOut])
def list_orders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    query = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product)
    )

    if user.role != "admin":
        query = query.filter(Order.user_id == user.id)

    orders = query.order_by(desc(Order.id)).all()

    for order in orders:
        safe_items = []
        for item in order.items:
            safe_items.append(_build_safe_order_item(item))
        order.items = safe_items

    return orders


@router.get("/{order_id}", response_model=OrderOut)
def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    if user.role != "admin" and order.user_id != user.id:
        raise HTTPException(status_code=403, detail="Não autorizado")

    safe_items = []
    for item in order.items:
        safe_items.append(_build_safe_order_item(item))
    order.items = safe_items

    return order


@router.post("/", response_model=OrderOut)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not order.items:
        raise HTTPException(
            status_code=400,
            detail="Pedido deve conter pelo menos um item"
        )

    payment_method = (order.payment_method or "").strip().lower()

    if payment_method not in {"entrega", "transferencia"}:
        raise HTTPException(
            status_code=400,
            detail="Forma de pagamento inválida."
        )

    final_delivery_address = build_delivery_address(order)

    db_order = Order(
        user_id=user.id,
        payment_method=payment_method,
        status="pending",
        payment_status="pending",
        delivery_address=final_delivery_address,

        customer_name=(order.customer_name or "").strip() or None,
        phone=(order.phone or "").strip() or None,  # 🔥 AQUI

        address_line=(order.address_line or "").strip() or None,
        neighborhood=(order.neighborhood or "").strip() or None,
        reference=(order.reference or "").strip() or None,
    )

    items_total = Decimal("0.00")

    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()

        if not product:
            raise HTTPException(status_code=404, detail="Produto não encontrado")

        if hasattr(product, "is_active") and not product.is_active:
            raise HTTPException(
                status_code=400,
                detail=f"{product.name} não está disponível"
            )

        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Estoque insuficiente para {product.name}"
            )

        product.stock -= item.quantity

        product_image = _extract_product_image(product)

        db_order.items.append(
            OrderItem(
                product_id=product.id,
                quantity=item.quantity,
                price=product.price,
                status="pending",
                product_image=product_image,
            )
        )

        items_total += Decimal(str(product.price)) * Decimal(str(item.quantity))

    delivery_fee = Decimal("1500.00") if payment_method == "entrega" else Decimal("0.00")

    db_order.delivery_fee = delivery_fee
    db_order.total = items_total + delivery_fee

    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    order_with_relations = _load_order_with_relations(db, db_order.id)
    if order_with_relations:
        Thread(
            target=_dispatch_order_notifications,
            args=(order_with_relations,),
            daemon=True,
        ).start()

    return db_order


@router.post("/{order_id}/confirm")
def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    if user.role != "admin" and order.user_id != user.id:
        raise HTTPException(status_code=403, detail="Não autorizado")

    if order.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Pedido só pode ser confirmado se estiver pendente"
        )

    if order.delivery_fee > 0 and order.payment_status != "paid":
        raise HTTPException(
            status_code=400,
            detail="A entrega só será realizada após o pagamento do frete."
        )

    order.status = "confirmed"
    db.commit()

    order_with_relations = _load_order_with_relations(db, order.id)
    if order_with_relations:
        Thread(
            target=_dispatch_order_notifications,
            args=(order_with_relations,),
            daemon=True,
        ).start()

    return {"status": order.status}


@router.post("/{order_id}/pay-delivery")
def pay_delivery(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    if user.role != "admin" and order.user_id != user.id:
        raise HTTPException(status_code=403, detail="Não autorizado")

    if order.delivery_fee <= 0:
        raise HTTPException(
            status_code=400,
            detail="Este pedido não possui taxa de entrega."
        )

    order.payment_status = "paid"
    db.commit()

    return {"message": "Frete pago com sucesso. Pedido liberado para entrega."}


class UpdateItemStatus(BaseModel):
    status: str


@router.put("/items/{item_id}/status")
def update_item_status(
    item_id: int,
    data: UpdateItemStatus,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    item = (
        db.query(OrderItem)
        .options(
            joinedload(OrderItem.order).joinedload(Order.user),
            joinedload(OrderItem.product),
        )
        .filter(OrderItem.id == item_id)
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    if user.role != "admin" and item.order and item.order.user_id != user.id:
        raise HTTPException(status_code=403, detail="Não autorizado")

    allowed = {"pending", "paid", "cancelled", "shipped", "delivered"}
    new_status = (data.status or "").strip().lower()

    if new_status not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Status inválido. Use: {sorted(allowed)}"
        )

    item.status = new_status
    db.commit()
    db.refresh(item)

    if item.order:
        order_with_relations = _load_order_with_relations(db, item.order.id)
        if order_with_relations:
            Thread(
                target=_dispatch_order_notifications,
                args=(order_with_relations,),
                daemon=True,
            ).start()

    return {
        "message": "Status updated",
        "item": {
            "id": item.id,
            "order_id": item.order_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price": str(item.price),
            "status": item.status,
            "product_image": item.product_image,
        }
    }