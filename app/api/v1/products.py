import json
import os
import shutil
import uuid
from decimal import Decimal
from typing import Optional, Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String, or_

from app.api.deps import get_current_user, get_db
from app.models.product import Product
from app.models.review import Review
from app.models.user import User
from app.schemas.product import ProductUpdate, ProductOut

router = APIRouter(prefix="/products", tags=["Products"])
admin_router = APIRouter(prefix="/admin/products", tags=["Admin Products"])

UPLOAD_DIR = "uploads/produtos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


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


def _normalize_text(value: Optional[str]) -> str:
    return str(value or "").strip()


def _normalize_text_lower(value: Optional[str]) -> str:
    return _normalize_text(value).lower()


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


def _merge_general_images_with_variations(images: List[str], variations: List[dict]) -> List[str]:
    return _dedupe_list([*(images or []), *_extract_images_from_variations(variations)])


def _product_to_dict(p: Product) -> dict[str, Any]:
    variations = _normalize_variations(getattr(p, "variations", None))

    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": float(p.price) if p.price is not None else 0.0,
        "stock": p.stock,
        "category": p.category,
        "subcategory": getattr(p, "subcategory", None),
        "is_wholesale": bool(getattr(p, "is_wholesale", False)),
        "wholesale_price": float(p.wholesale_price) if getattr(p, "wholesale_price", None) is not None else None,
        "is_kit": bool(getattr(p, "is_kit", False)),
        "sizes": _ensure_list(getattr(p, "sizes", None)),
        "colors": _ensure_list(getattr(p, "colors", None)),
        "shoe_sizes": _ensure_list(getattr(p, "shoe_sizes", None)),
        "variations": variations,
        "images": _ensure_list(getattr(p, "images", None)),
        "video_url": getattr(p, "video_url", None),
        "is_active": getattr(p, "is_active", True),
        "created_at": getattr(p, "created_at", None),
        "updated_at": getattr(p, "updated_at", None),
    }


def _get_reviews_summary(db: Session, product_id: int):
    avg, cnt = (
        db.query(
            func.coalesce(func.avg(Review.rating), 0),
            func.count(Review.id)
        )
        .filter(Review.product_id == product_id)
        .one()
    )

    rows = (
        db.query(Review, User.name)
        .join(User, User.id == Review.user_id)
        .filter(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .all()
    )

    reviews_out = [
        {
            "id": r.id,
            "rating": int(r.rating),
            "comment": r.comment,
            "created_at": r.created_at,
            "user_name": user_name,
            "media_url": r.media_url,
            "media_type": r.media_type,
        }
        for r, user_name in rows
    ]

    return float(avg or 0), int(cnt or 0), reviews_out


def _save_upload_file(upload_file: UploadFile, folder: str = UPLOAD_DIR) -> str:
    filename = upload_file.filename or ""
    ext = os.path.splitext(filename)[1].lower() or ""
    safe_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(folder, safe_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return f"/uploads/produtos/{safe_name}"


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
        variation_colors = _extract_colors_from_variations(normalized_variations)
        merged_colors = _dedupe_list([*normalized_colors, *variation_colors])
        merged_images = _merge_general_images_with_variations(normalized_images, normalized_variations)
        return normalized_variations, merged_colors, merged_images

    return [], normalized_colors, normalized_images


def _apply_product_fields(
    db_product: Product,
    *,
    name: str,
    description: str,
    price: float,
    stock: int,
    category: Optional[str],
    subcategory: str,
    is_wholesale: bool,
    wholesale_price: Optional[float],
    is_kit: bool,
    colors: List[str],
    sizes: List[str],
    shoe_sizes: List[str],
    variations: List[dict],
    images: List[str],
    video_url: Optional[str],
):
    final_variations, final_colors, final_images = _prepare_variation_payload(
        variations=variations,
        colors=colors,
        images=images,
    )

    db_product.name = name.strip()
    db_product.description = description.strip()
    db_product.price = price
    db_product.stock = stock
    db_product.category = category.strip() if category else None
    db_product.subcategory = subcategory.strip()
    db_product.is_wholesale = is_wholesale
    db_product.wholesale_price = wholesale_price
    db_product.is_kit = is_kit
    db_product.colors = final_colors
    db_product.sizes = sizes or []
    db_product.shoe_sizes = shoe_sizes or []
    db_product.variations = final_variations
    db_product.images = final_images
    db_product.video_url = video_url


@router.get("/", response_model=list[ProductOut])
def list_products(
    category: Optional[str] = Query(None),
    subcategory: Optional[str] = Query(None),
    is_wholesale: Optional[bool] = Query(None),
    is_kit: Optional[bool] = Query(None),
    q: Optional[str] = Query(None),
    min_price: Optional[Decimal] = Query(None),
    max_price: Optional[Decimal] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.is_active == True)

    if category:
        category_normalized = _normalize_text_lower(category)
        query = query.filter(func.lower(func.trim(Product.category)) == category_normalized)

    if subcategory:
        subcategory_normalized = _normalize_text_lower(subcategory)
        query = query.filter(
            func.lower(func.trim(Product.subcategory)).like(f"%{subcategory_normalized}%")
        )

    if is_wholesale is not None:
        query = query.filter(Product.is_wholesale == is_wholesale)

    if is_kit is not None:
        query = query.filter(Product.is_kit == is_kit)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if q:
        q = _normalize_text(q)
        if q:
            search = f"%{q}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search),
                    Product.description.ilike(search),
                    Product.category.ilike(search),
                    Product.subcategory.ilike(search),
                    cast(Product.price, String).ilike(search),
                )
            )

    products = query.order_by(Product.id.desc()).all()

    out = []
    for p in products:
        base = _product_to_dict(p)
        rating_avg, rating_count, _ = _get_reviews_summary(db, p.id)
        base["rating_avg"] = rating_avg
        base["rating_count"] = rating_count
        base["reviews"] = []
        out.append(base)

    return out


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    base = _product_to_dict(product)
    rating_avg, rating_count, reviews_out = _get_reviews_summary(db, product.id)
    base["rating_avg"] = rating_avg
    base["rating_count"] = rating_count
    base["reviews"] = reviews_out

    return base


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db)
):
    db_product = db.query(Product).filter(Product.id == product_id).first()

    if not db_product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    update_data = product.dict(exclude_unset=True)

    if "variations" in update_data:
        final_variations, final_colors, final_images = _prepare_variation_payload(
            variations=update_data.get("variations"),
            colors=update_data.get("colors", _ensure_list(getattr(db_product, "colors", None))),
            images=update_data.get("images", _ensure_list(getattr(db_product, "images", None))),
        )
        update_data["variations"] = final_variations
        update_data["colors"] = final_colors
        update_data["images"] = final_images

    for field, value in update_data.items():
        setattr(db_product, field, value)

    db.commit()
    db.refresh(db_product)

    base = _product_to_dict(db_product)
    rating_avg, rating_count, reviews_out = _get_reviews_summary(db, db_product.id)
    base["rating_avg"] = rating_avg
    base["rating_count"] = rating_count
    base["reviews"] = reviews_out

    return base


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()

    if not db_product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    try:
        db.delete(db_product)
        db.commit()
        return {"ok": True, "message": "Produto excluído com sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao excluir produto: {str(e)}"
        )


@admin_router.post("")
def create_product_admin_json(
    product: ProductUpdate,
    db: Session = Depends(get_db)
):
    data = product.dict(exclude_unset=True)

    final_variations, final_colors, final_images = _prepare_variation_payload(
        variations=data.get("variations"),
        colors=data.get("colors", []),
        images=data.get("images", []),
    )

    db_product = Product(
        name=data.get("name", "").strip(),
        description=data.get("description", "").strip(),
        price=data.get("price", 0),
        stock=data.get("stock", 0),
        category=data.get("category"),
        subcategory=data.get("subcategory", ""),
        is_wholesale=data.get("is_wholesale", False),
        wholesale_price=data.get("wholesale_price"),
        is_kit=data.get("is_kit", False),
        colors=final_colors,
        sizes=data.get("sizes", []),
        shoe_sizes=data.get("shoe_sizes", []),
        variations=final_variations,
        images=final_images,
        video_url=data.get("video_url"),
        is_active=data.get("is_active", True),
    )

    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    base = _product_to_dict(db_product)
    rating_avg, rating_count, reviews_out = _get_reviews_summary(db, db_product.id)
    base["rating_avg"] = rating_avg
    base["rating_count"] = rating_count
    base["reviews"] = reviews_out

    return base


@admin_router.post("/")
def create_product_admin_form(
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    stock: int = Form(...),
    category: Optional[str] = Form(None),
    subcategory: str = Form(""),
    is_wholesale: bool = Form(False),
    wholesale_price: Optional[float] = Form(None),
    is_kit: bool = Form(False),
    video_url: Optional[str] = Form(None),
    images: List[str] = Form(default=[]),
    colors: List[str] = Form(default=[]),
    sizes: List[str] = Form(default=[]),
    shoe_sizes: List[str] = Form(default=[]),
    variations: Optional[str] = Form(None),
    image_files: List[UploadFile] = File(default=[]),
    video: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    uploaded_images = []
    for img in image_files:
        if img and img.filename:
            uploaded_images.append(_save_upload_file(img))

    uploaded_video_url = None
    if video and video.filename:
        uploaded_video_url = _save_upload_file(video)

    base_images = list(dict.fromkeys([*(images or []), *uploaded_images]))
    parsed_variations = _normalize_variations(variations)

    db_product = Product()
    _apply_product_fields(
        db_product,
        name=name,
        description=description,
        price=price,
        stock=stock,
        category=category,
        subcategory=subcategory,
        is_wholesale=is_wholesale,
        wholesale_price=wholesale_price,
        is_kit=is_kit,
        colors=colors or [],
        sizes=sizes or [],
        shoe_sizes=shoe_sizes or [],
        variations=parsed_variations,
        images=base_images,
        video_url=uploaded_video_url or video_url,
    )
    db_product.is_active = True

    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    base = _product_to_dict(db_product)
    rating_avg, rating_count, reviews_out = _get_reviews_summary(db, db_product.id)
    base["rating_avg"] = rating_avg
    base["rating_count"] = rating_count
    base["reviews"] = reviews_out

    return base


@admin_router.put("/{product_id}")
def update_product_admin_json(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db)
):
    db_product = db.query(Product).filter(Product.id == product_id).first()

    if not db_product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    update_data = product.dict(exclude_unset=True)

    if "variations" in update_data:
        final_variations, final_colors, final_images = _prepare_variation_payload(
            variations=update_data.get("variations"),
            colors=update_data.get("colors", _ensure_list(getattr(db_product, "colors", None))),
            images=update_data.get("images", _ensure_list(getattr(db_product, "images", None))),
        )
        update_data["variations"] = final_variations
        update_data["colors"] = final_colors
        update_data["images"] = final_images

    for field, value in update_data.items():
        setattr(db_product, field, value)

    db.commit()
    db.refresh(db_product)

    base = _product_to_dict(db_product)
    rating_avg, rating_count, reviews_out = _get_reviews_summary(db, db_product.id)
    base["rating_avg"] = rating_avg
    base["rating_count"] = rating_count
    base["reviews"] = reviews_out

    return base


@admin_router.put("/{product_id}/upload")
def update_product_admin_form(
    product_id: int,
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    stock: int = Form(...),
    category: Optional[str] = Form(None),
    subcategory: str = Form(""),
    is_wholesale: bool = Form(False),
    wholesale_price: Optional[float] = Form(None),
    is_kit: bool = Form(False),
    video_url: Optional[str] = Form(None),
    images: List[str] = Form(default=[]),
    colors: List[str] = Form(default=[]),
    sizes: List[str] = Form(default=[]),
    shoe_sizes: List[str] = Form(default=[]),
    variations: Optional[str] = Form(None),
    image_files: List[UploadFile] = File(default=[]),
    video: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    db_product = db.query(Product).filter(Product.id == product_id).first()

    if not db_product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    uploaded_images = []
    for img in image_files:
        if img and img.filename:
            uploaded_images.append(_save_upload_file(img))

    uploaded_video_url = None
    if video and video.filename:
        uploaded_video_url = _save_upload_file(video)

    base_images = list(dict.fromkeys([*(images or []), *uploaded_images]))
    parsed_variations = _normalize_variations(variations)

    _apply_product_fields(
        db_product,
        name=name,
        description=description,
        price=price,
        stock=stock,
        category=category,
        subcategory=subcategory,
        is_wholesale=is_wholesale,
        wholesale_price=wholesale_price,
        is_kit=is_kit,
        colors=colors,
        sizes=sizes,
        shoe_sizes=shoe_sizes,
        variations=parsed_variations,
        images=base_images,
        video_url=uploaded_video_url or video_url,
    )

    db.commit()
    db.refresh(db_product)

    base = _product_to_dict(db_product)
    rating_avg, rating_count, reviews_out = _get_reviews_summary(db, db_product.id)
    base["rating_avg"] = rating_avg
    base["rating_count"] = rating_count
    base["reviews"] = reviews_out

    return base


@router.post("/{product_id}/review")
def create_review_with_media(
    product_id: int,
    rating: int = Form(...),
    comment: str = Form(""),
    media: UploadFile = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),  # usa teu auth
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    media_url = None
    media_type = None

    if media:
        ext = os.path.splitext(media.filename)[1].lower()
        filename = f"{uuid.uuid4().hex}{ext}"
        path = f"uploads/reviews/{filename}"

        os.makedirs("uploads/reviews", exist_ok=True)

        with open(path, "wb") as f:
            shutil.copyfileobj(media.file, f)

        media_url = f"/{path}"
        media_type = "video" if ext in [".mp4", ".mov", ".webm"] else "image"

    review = Review(
        product_id=product_id,
        user_id=user.id,
        rating=rating,
        comment=comment,
        media_url=media_url,
        media_type=media_type,
    )

    db.add(review)
    db.commit()

    return {"ok": True}