from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.product import Product
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewOut

router = APIRouter(prefix="/products", tags=["Reviews"])


@router.get("/{product_id}/reviews")
def list_reviews(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    # 🔥 REVIEWS COM NOME DO USUÁRIO
    rows = (
        db.query(Review, User.name)
        .join(User, User.id == Review.user_id)
        .filter(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .all()
    )

    reviews = []
    for review, user_name in rows:
        reviews.append(
            {
                "id": review.id,
                "rating": review.rating,
                "comment": review.comment,
                "created_at": review.created_at,
                "user_name": user_name,
            }
        )

    # ⭐ MÉDIA E TOTAL
    avg_rating = db.query(func.avg(Review.rating)).filter(
        Review.product_id == product_id
    ).scalar()

    count = db.query(func.count(Review.id)).filter(
        Review.product_id == product_id
    ).scalar()

    return {
        "reviews": reviews,
        "rating_avg": round(avg_rating or 0, 1),
        "rating_count": count,
    }


@router.post("/{product_id}/reviews", response_model=ReviewOut, status_code=201)
def create_review(
    product_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    exists = (
        db.query(Review)
        .filter(Review.product_id == product_id, Review.user_id == current_user.id)
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=400,
            detail="Você já avaliou este produto. (1 avaliação por produto)",
        )

    review = Review(
        product_id=product_id,
        user_id=current_user.id,
        rating=payload.rating,
        comment=payload.comment,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return ReviewOut(
        id=review.id,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
        user_name=current_user.name,
    )