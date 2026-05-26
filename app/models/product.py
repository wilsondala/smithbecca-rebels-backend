from sqlalchemy import Column, Integer, String, Numeric, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from app.database.base_class import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    # =========================
    # BASIC INFO
    # =========================
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0, nullable=False)

    # =========================
    # CATEGORY / FILTERS
    # =========================
    category = Column(String, nullable=True, index=True)
    subcategory = Column(String, nullable=True, index=True)

    # =========================
    # WHOLESALE / KIT
    # =========================
    is_wholesale = Column(Boolean, default=False, nullable=False)
    wholesale_price = Column(Numeric(10, 2), nullable=True)

    is_kit = Column(Boolean, default=False, nullable=False)

    # =========================
    # VARIANTS
    # =========================
    sizes = Column(JSON, nullable=True)        # Ex: ["P", "M", "G", "GG"]
    colors = Column(JSON, nullable=True)       # Ex: ["Preto", "Bege", "Rosa"]
    shoe_sizes = Column(JSON, nullable=True)   # Ex: ["17", "18", ..., "43"]

    # NOVO: variações por cor com imagens próprias
    # Ex:
    # [
    #   {"color": "Preto", "images": ["/uploads/produtos/preto1.jpg"]},
    #   {"color": "Branco", "images": ["/uploads/produtos/branco1.jpg"]}
    # ]
    variations = Column(JSON, nullable=True)

    # =========================
    # MEDIA
    # =========================
    images = Column(JSON, nullable=True)
    video_url = Column(String, nullable=True)

    # =========================
    # STATUS
    # =========================
    is_active = Column(Boolean, default=True, nullable=False)

    # =========================
    # RELATIONSHIPS
    # =========================
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")

    order_items = relationship(
        "OrderItem",
        back_populates="product"
    )