from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HomeBannerBase(BaseModel):
    title: str
    subtitle: Optional[str] = None

    button_text: Optional[str] = None
    button_link: Optional[str] = None

    image_url: Optional[str] = None
    mobile_image_url: Optional[str] = None

    video_url: Optional[str] = None
    mobile_video_url: Optional[str] = None

    position: int = 0
    is_active: bool = True

    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


class HomeBannerCreate(HomeBannerBase):
    pass


class HomeBannerUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None

    button_text: Optional[str] = None
    button_link: Optional[str] = None

    image_url: Optional[str] = None
    mobile_image_url: Optional[str] = None

    video_url: Optional[str] = None
    mobile_video_url: Optional[str] = None

    position: Optional[int] = None
    is_active: Optional[bool] = None

    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None


class HomeBannerOut(HomeBannerBase):
    id: int

    class Config:
        from_attributes = True


class HomeSectionPublicOut(BaseModel):
    id: int
    key: str
    title: str
    subtitle: Optional[str] = None
    is_active: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class HomeContentOut(BaseModel):
    banners: List[HomeBannerOut] = Field(default_factory=list)

    categories: Optional[HomeSectionPublicOut] = None
    showcase: Optional[HomeSectionPublicOut] = None
    campaigns: Optional[HomeSectionPublicOut] = None

    hero_side_card: Optional[HomeSectionPublicOut] = None  # 🔥 ESSENCIAL

    why_choose: Optional[HomeSectionPublicOut] = None
    testimonials: Optional[HomeSectionPublicOut] = None
    resellers: Optional[HomeSectionPublicOut] = None

    contacts: Optional[HomeSectionPublicOut] = None
    footer: Optional[HomeSectionPublicOut] = None

    final_cta: Optional[HomeSectionPublicOut] = None

    class Config:
        from_attributes = True