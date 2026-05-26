from sqlalchemy import Column, Integer, String, DateTime, func, UniqueConstraint
from app.database.base_class import Base


class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"
    __table_args__ = (
        UniqueConstraint("email", name="uq_newsletter_email"),
        UniqueConstraint("phone", name="uq_newsletter_phone"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=True)
    phone = Column(String(30), nullable=True, index=True)
    email = Column(String(180), nullable=True, index=True)
    preferred_channel = Column(String(20), nullable=False, server_default="whatsapp")
    created_at = Column(DateTime(timezone=True), server_default=func.now())