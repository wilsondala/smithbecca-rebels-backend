from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.database.base_class import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)

    role = Column(String, default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    password_hash = Column(String, nullable=False)
    photo = Column(String, nullable=True)

    # Login social
    auth_provider = Column(String, nullable=False, default="local")
    google_id = Column(String, unique=True, nullable=True, index=True)
    facebook_id = Column(String, unique=True, nullable=True, index=True)

    # pedidos: sem cascade de delete físico
    orders = relationship("Order", back_populates="user")

    reviews = relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan",
    )