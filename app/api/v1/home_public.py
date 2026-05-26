from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.home_banner import HomeBanner
from app.models.home_section import HomeSection
from app.schemas.home_banner import HomeContentOut
from app.schemas.home_section import HomeContentSectionOut

router = APIRouter(tags=["Home"])


@router.get("/home-content", response_model=HomeContentOut)
def get_home_content(db: Session = Depends(get_db)):
    now = datetime.utcnow()

    banners = (
        db.query(HomeBanner)
        .filter(HomeBanner.is_active.is_(True))
        .filter(or_(HomeBanner.starts_at.is_(None), HomeBanner.starts_at <= now))
        .filter(or_(HomeBanner.ends_at.is_(None), HomeBanner.ends_at >= now))
        .order_by(HomeBanner.position.asc(), HomeBanner.id.desc())
        .all()
    )

    sections = db.query(HomeSection).all()

    sections_map = {}
    for section in sections:
        sections_map[section.key] = HomeContentSectionOut(
            id=section.id,
            key=section.key,
            title=section.title,
            subtitle=section.subtitle,
            data=section.data or {},
            is_active=section.is_active,
        )

    return {
        "banners": banners,
        "categories": sections_map.get("categories"),
        "showcase": sections_map.get("showcase"),
        "campaigns": sections_map.get("campaigns"),
        "contacts": sections_map.get("contacts"),
        "final_cta": sections_map.get("final_cta"),
    }