from sqlalchemy import Column, Integer, ForeignKey, String, Numeric, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base_class import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    status = Column(String, default="pending", nullable=True)
    payment_status = Column(String, default="pending", nullable=True)

    payment_method = Column(String, nullable=True)
    payment_reference = Column(String, nullable=True)

    delivery_fee = Column(Numeric(10, 2), default=0, nullable=True)

    # compatibilidade com pedidos antigos e resumo final
    delivery_address = Column(String, nullable=True)

    # novos campos estruturados
    customer_name = Column(String(160), nullable=True)
    phone = Column(String(20), nullable=True)  # 🔥 NOVO
    address_line = Column(String(255), nullable=True)
    neighborhood = Column(String(160), nullable=True)
    reference = Column(String(255), nullable=True)
    latitude = Column(Numeric(10, 6), nullable=True)
    longitude = Column(Numeric(10, 6), nullable=True)

    total = Column(Numeric(10, 2), default=0, nullable=True)

    created_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=True
    )

    user = relationship("User", back_populates="orders")

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )