from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from app.database.base_class import Base


class HomeBanner(Base):
    __tablename__ = "home_banners"

    id = Column(Integer, primary_key=True, index=True)

    # =========================
    # CONTENT
    # =========================
    title = Column(String, nullable=False)
    subtitle = Column(Text, nullable=True)

    button_text = Column(String, nullable=True)
    button_link = Column(String, nullable=True)

    image_url = Column(String, nullable=False)
    mobile_image_url = Column(String, nullable=True)

    # 🔥 NOVO — SUPORTE A VÍDEO
    video_url = Column(String, nullable=True)
    mobile_video_url = Column(String, nullable=True)

    # =========================
    # DISPLAY / CONTROL
    # =========================
    position = Column(Integer, default=0, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)