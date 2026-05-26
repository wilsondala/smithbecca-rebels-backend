from decimal import Decimal
import json
import logging
import os
import shutil
import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

UPLOAD_DIR = "uploads/produtos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado"
        )

    if str(current_user.role).lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )

    if hasattr(current_user, "is_active") and not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )

    return current_user


def _to_decimal_or_none(value):
    if value is None or value == "":
        return None
    return Decimal(str(value))


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


def _normalize_text(value: Optional[str]) -> str:
    return str(value or "").strip()


def _save_upload_file(upload_file: UploadFile) -> str:
    filename = upload_file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return f"/uploads/produtos/{safe_name}"


def _dedupe_list(values: List[str]) -> List[str]:
    cleaned = []
    seen = set()

    for item in values or []:
        value = str(item or "").strip()
        if not value:
            continue
        if value not in seen:
            cleaned.append(value)
            seen.add(value)

    return cleaned


def _ensure_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip().startswith("["):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
    return []


def _normalize_variations(value) -> List[dict]:
    raw_list = _ensure_list(value)
    normalized = []

    for item in raw_list:
        if not isinstance(item, dict):
            continue

        color = str(item.get("color") or "").strip()
        images = _dedupe_list(_ensure_list(item.get("images")))

        if not color:
            continue

        normalized.append({
            "color": color,
            "images": images,
        })

    return normalized


def _extract_colors_from_variations(variations: List[dict]) -> List[str]:
    return _dedupe_list([item.get("color") for item in variations if item.get("color")])


def _extract_images_from_variations(variations: List[dict]) -> List[str]:
    images = []
    for item in variations:
        images.extend(_ensure_list(item.get("images")))
    return _dedupe_list(images)


def _prepare_variation_payload(
    *,
    variations,
    colors: List[str],
    images: List[str],
) -> tuple[List[dict], List[str], List[str]]:
    normalized_variations = _normalize_variations(variations)
    normalized_colors = _dedupe_list(colors or [])
    normalized_images = _dedupe_list(images or [])

    if normalized_variations:
        merged_colors = _dedupe_list([*normalized_colors, *_extract_colors_from_variations(normalized_variations)])
        merged_images = _dedupe_list([*normalized_images, *_extract_images_from_variations(normalized_variations)])
        return normalized_variations, merged_colors, merged_images

    return [], normalized_colors, normalized_images


def _apply_product_data(existing_product: Product, product: ProductCreate) -> Product:
    final_variations, final_colors, final_images = _prepare_variation_payload(
        variations=getattr(product, "variations", None),
        colors=product.colors or [],
        images=product.images or [],
    )

    existing_product.name = product.name
    existing_product.description = product.description
    existing_product.price = Decimal(str(product.price))
    existing_product.stock = product.stock
    existing_product.category = product.category
    existing_product.subcategory = product.subcategory
    existing_product.is_wholesale = product.is_wholesale
    existing_product.wholesale_price = _to_decimal_or_none(product.wholesale_price)
    existing_product.is_kit = product.is_kit
    existing_product.images = final_images
    existing_product.video_url = product.video_url
    existing_product.variations = final_variations

    if hasattr(product, "colors") and hasattr(existing_product, "colors"):
        existing_product.colors = final_colors

    if hasattr(product, "sizes") and hasattr(existing_product, "sizes"):
        existing_product.sizes = product.sizes

    if hasattr(product, "shoe_sizes") and hasattr(existing_product, "shoe_sizes"):
        existing_product.shoe_sizes = product.shoe_sizes

    return existing_product


def _apply_product_form_data(
    existing_product: Product,
    *,
    name: str,
    description: str,
    price,
    stock,
    category: Optional[str],
    subcategory: str,
    is_wholesale,
    wholesale_price,
    is_kit,
    images: List[str],
    video_url: Optional[str],
    colors: List[str],
    sizes: List[str],
    shoe_sizes: List[str],
    variations,
) -> Product:
    final_variations, final_colors, final_images = _prepare_variation_payload(
        variations=variations,
        colors=colors,
        images=images,
    )

    existing_product.name = _normalize_text(name)
    existing_product.description = _normalize_text(description)
    existing_product.price = Decimal(str(price))
    existing_product.stock = int(stock)
    existing_product.category = _normalize_text(category) or None
    existing_product.subcategory = _normalize_text(subcategory)
    existing_product.is_wholesale = _to_bool(is_wholesale)
    existing_product.wholesale_price = _to_decimal_or_none(wholesale_price)
    existing_product.is_kit = _to_bool(is_kit)
    existing_product.images = final_images
    existing_product.video_url = _normalize_text(video_url) or None
    existing_product.variations = final_variations

    if hasattr(existing_product, "colors"):
        existing_product.colors = final_colors

    if hasattr(existing_product, "sizes"):
        existing_product.sizes = _dedupe_list(sizes)

    if hasattr(existing_product, "shoe_sizes"):
        existing_product.shoe_sizes = _dedupe_list(shoe_sizes)

    return existing_product


@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    total_users = db.query(User).count()
    total_products = db.query(Product).count()
    total_orders = db.query(Order).count()

    delivered_orders = db.query(Order).filter(Order.status == "DELIVERED").count()
    pending_orders = db.query(Order).filter(Order.status == "PENDING").count()

    total_revenue = db.query(func.sum(Order.total)).scalar() or 0

    return {
        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "pending_orders": pending_orders,
        "total_revenue": float(total_revenue),
    }


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    query = db.query(User)
    total = query.count()
    users = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "phone": u.phone,
                "role": u.role,
                "is_active": u.is_active,
            }
            for u in users
        ],
    }


@router.patch("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode desativar seu próprio usuário admin."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    try:
        user.is_active = False
        db.commit()
        db.refresh(user)
        return {"ok": True, "message": "Usuário desativado com sucesso."}
    except Exception:
        db.rollback()
        logger.exception("Erro ao desativar usuário")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao desativar usuário."
        )


@router.patch("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode alterar o status do seu próprio usuário admin."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    try:
        user.is_active = True
        db.commit()
        db.refresh(user)
        return {"ok": True, "message": "Usuário ativado com sucesso."}
    except Exception:
        db.rollback()
        logger.exception("Erro ao ativar usuário")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao ativar usuário."
        )


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode excluir seu próprio usuário admin."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    has_orders = db.query(Order).filter(Order.user_id == user.id).first()
    if has_orders:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este usuário possui pedidos vinculados. Desative a conta em vez de excluir."
        )

    try:
        db.delete(user)
        db.commit()
        return {"ok": True, "message": "Usuário excluído com sucesso."}
    except Exception:
        db.rollback()
        logger.exception("Erro ao excluir usuário")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao excluir usuário."
        )


@router.post("/products")
async def create_product(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    content_type = request.headers.get("content-type", "").lower()

    try:
        if "multipart/form-data" in content_type:
            form = await request.form()

            name = form.get("name", "")
            description = form.get("description", "")
            price = form.get("price", 0)
            stock = form.get("stock", 0)
            category = form.get("category")
            subcategory = form.get("subcategory", "")
            is_wholesale = form.get("is_wholesale", False)
            wholesale_price = form.get("wholesale_price")
            is_kit = form.get("is_kit", False)
            video_url = form.get("video_url")

            images = form.getlist("images")
            colors = form.getlist("colors")
            sizes = form.getlist("sizes")
            shoe_sizes = form.getlist("shoe_sizes")
            variations = form.get("variations")

            image_files = form.getlist("image_files")
            video_file = form.get("video")

            uploaded_images = []
            for image in image_files:
                if isinstance(image, UploadFile) and image.filename:
                    uploaded_images.append(_save_upload_file(image))

            uploaded_video_url = None
            if isinstance(video_file, UploadFile) and video_file.filename:
                uploaded_video_url = _save_upload_file(video_file)

            final_images = _dedupe_list([*images, *uploaded_images])
            final_video_url = uploaded_video_url or (_normalize_text(video_url) or None)

            new_product = Product()
            new_product = _apply_product_form_data(
                new_product,
                name=name,
                description=description,
                price=price,
                stock=stock,
                category=category,
                subcategory=subcategory,
                is_wholesale=is_wholesale,
                wholesale_price=wholesale_price,
                is_kit=is_kit,
                images=final_images,
                video_url=final_video_url,
                colors=colors,
                sizes=sizes,
                shoe_sizes=shoe_sizes,
                variations=variations,
            )
        else:
            payload = await request.json()
            product = ProductCreate(**payload)

            new_product = Product()
            new_product = _apply_product_data(new_product, product)

        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        return {
            "message": "Produto criado com sucesso",
            "product_id": new_product.id,
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Erro ao criar produto")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao criar produto."
        )


@router.put("/products/{product_id}")
async def update_product(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing_product = db.query(Product).filter(Product.id == product_id).first()

    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )

    content_type = request.headers.get("content-type", "").lower()

    try:
        if "multipart/form-data" in content_type:
            form = await request.form()

            name = form.get("name", existing_product.name)
            description = form.get("description", existing_product.description)
            price = form.get("price", existing_product.price)
            stock = form.get("stock", existing_product.stock)
            category = form.get("category", existing_product.category)
            subcategory = form.get("subcategory", existing_product.subcategory or "")
            is_wholesale = form.get("is_wholesale", existing_product.is_wholesale)
            wholesale_price = form.get("wholesale_price", existing_product.wholesale_price)
            is_kit = form.get("is_kit", existing_product.is_kit)
            video_url = form.get("video_url", existing_product.video_url)

            images = form.getlist("images")
            colors = form.getlist("colors")
            sizes = form.getlist("sizes")
            shoe_sizes = form.getlist("shoe_sizes")
            variations = form.get("variations")

            image_files = form.getlist("image_files")
            video_file = form.get("video")

            uploaded_images = []
            for image in image_files:
                if isinstance(image, UploadFile) and image.filename:
                    uploaded_images.append(_save_upload_file(image))

            uploaded_video_url = None
            if isinstance(video_file, UploadFile) and video_file.filename:
                uploaded_video_url = _save_upload_file(video_file)

            final_images = _dedupe_list([*images, *uploaded_images])
            final_video_url = uploaded_video_url or (_normalize_text(video_url) or None)

            existing_product = _apply_product_form_data(
                existing_product,
                name=name,
                description=description,
                price=price,
                stock=stock,
                category=category,
                subcategory=subcategory,
                is_wholesale=is_wholesale,
                wholesale_price=wholesale_price,
                is_kit=is_kit,
                images=final_images,
                video_url=final_video_url,
                colors=colors,
                sizes=sizes,
                shoe_sizes=shoe_sizes,
                variations=variations,
            )
        else:
            payload = await request.json()
            product = ProductCreate(**payload)
            existing_product = _apply_product_data(existing_product, product)

        db.commit()
        db.refresh(existing_product)

        return {
            "message": "Produto atualizado com sucesso",
            "product_id": existing_product.id,
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Erro ao atualizar produto")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao atualizar produto."
        )


@router.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )

    try:
        db.delete(product)
        db.commit()
        return {"message": "Produto excluído com sucesso"}
    except Exception:
        db.rollback()
        logger.exception("Erro ao excluir produto")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao excluir produto."
        )