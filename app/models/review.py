from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text, UniqueConstraint, String
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.base_class import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)

    media_url = Column(String, nullable=True)
    media_type = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("product_id", "user_id", name="uq_review_product_user"),
    )

    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")