import json
import os
import shutil
import uuid
from datetime import datetime
from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.home_banner import HomeBanner
from app.models.home_section import HomeSection
from app.models.user import User
from app.schemas.home_banner import (
    HomeBannerCreate,
    HomeBannerOut,
    HomeBannerUpdate,
)
from app.schemas.home_section import (
    HomeSectionCreate,
    HomeSectionOut,
    HomeSectionUpdate,
)

router = APIRouter(tags=["Admin Home"])

BANNERS_UPLOAD_DIR = "uploads/home/banners"
SECTIONS_UPLOAD_DIR = "uploads/home/sections"

os.makedirs(BANNERS_UPLOAD_DIR, exist_ok=True)
os.makedirs(SECTIONS_UPLOAD_DIR, exist_ok=True)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
        )

    if str(current_user.role).lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado",
        )

    if hasattr(current_user, "is_active") and not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo",
        )

    return current_user


def _normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _normalize_bool(value, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


def _normalize_int(value, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _is_uploaded_file(value) -> bool:
    return bool(value and getattr(value, "filename", None))


def _save_upload_file(upload_file, folder: str) -> str:
    filename = upload_file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(folder, safe_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    relative_folder = folder.replace("\\", "/").strip("/")
    return f"/{relative_folder}/{safe_name}"


def _safe_remove_uploaded_file(file_url: Optional[str], folder: str) -> None:
    if not file_url:
        return

    normalized = str(file_url).strip()
    prefix = f"/{folder.replace(os.sep, '/').strip('/')}/"

    if not normalized.startswith(prefix):
        return

    relative_path = normalized.lstrip("/")
    absolute_path = os.path.abspath(relative_path)
    upload_root = os.path.abspath(folder)

    if not absolute_path.startswith(upload_root):
        return

    if os.path.isfile(absolute_path):
        try:
            os.remove(absolute_path)
        except OSError:
            pass


def _parse_datetime(value):
    if value in (None, "", "null"):
        return None

    if isinstance(value, datetime):
        return value

    text = str(value).strip()
    if not text:
        return None

    for fmt in (
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(text)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data inválida: {text}",
        )


def _ensure_dict(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    return {}


def _ensure_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    return []


def _extract_section_file_targets(section_key: str, data: dict) -> list[tuple[str, str]]:
    """
    Retorna pares (campo_form, campo_item_ou_data) esperados no frontend.
    """
    if section_key in {"categories", "showcase", "campaigns"}:
        items = _ensure_list(data.get("items"))
        targets: list[tuple[str, str]] = []
        for index, _item in enumerate(items):
            targets.append((f"item_image_file_{index}", f"image"))
        return targets

    if section_key == "final_cta":
        return [("section_image_file", "image")]

    return []


def _apply_section_uploads(section_key: str, data: dict, form) -> dict:
    next_data = dict(data or {})

    if section_key in {"categories", "showcase", "campaigns"}:
        items = []
        for index, item in enumerate(_ensure_list(next_data.get("items"))):
            next_item = dict(item or {})
            image_file = form.get(f"item_image_file_{index}")

            if _is_uploaded_file(image_file):
                previous_url = _normalize_text(next_item.get("image"))
                created_url = _save_upload_file(image_file, SECTIONS_UPLOAD_DIR)
                next_item["image"] = created_url

                if previous_url and previous_url != created_url:
                    _safe_remove_uploaded_file(previous_url, SECTIONS_UPLOAD_DIR)

            else:
                next_item["image"] = _normalize_text(next_item.get("image"))

            items.append(next_item)

        next_data["items"] = items
        return next_data

    if section_key == "final_cta":
        image_file = form.get("section_image_file")
        previous_url = _normalize_text(next_data.get("image"))

        if _is_uploaded_file(image_file):
            created_url = _save_upload_file(image_file, SECTIONS_UPLOAD_DIR)
            next_data["image"] = created_url

            if previous_url and previous_url != created_url:
                _safe_remove_uploaded_file(previous_url, SECTIONS_UPLOAD_DIR)
        else:
            next_data["image"] = previous_url

    return next_data


def _parse_section_payload_from_form(form) -> HomeSectionCreate:
    key = _normalize_text(form.get("key"))
    title = _normalize_text(form.get("title"))
    subtitle = _normalize_text(form.get("subtitle"))
    is_active = _normalize_bool(form.get("is_active"), default=True)

    raw_data = form.get("data")
    if raw_data in (None, ""):
        data = {}
    else:
        try:
            data = json.loads(raw_data)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campo 'data' inválido. JSON malformado.",
            )

    if not key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chave da seção é obrigatória.",
        )

    data = _apply_section_uploads(key, _ensure_dict(data), form)

    return HomeSectionCreate(
        key=key.strip(),
        title=title,
        subtitle=subtitle,
        data=data,
        is_active=is_active,
    )


def _parse_section_update_from_form(form, current_key: str) -> HomeSectionUpdate:
    key = _normalize_text(form.get("key")) or current_key
    title = _normalize_text(form.get("title"))
    subtitle = _normalize_text(form.get("subtitle"))
    is_active = _normalize_bool(form.get("is_active"), default=True)

    raw_data = form.get("data")
    if raw_data in (None, ""):
        data = {}
    else:
        try:
            data = json.loads(raw_data)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campo 'data' inválido. JSON malformado.",
            )

    data = _apply_section_uploads(key, _ensure_dict(data), form)

    return HomeSectionUpdate(
        key=key.strip(),
        title=title,
        subtitle=subtitle,
        data=data,
        is_active=is_active,
    )


# =========================
# SECTIONS
# =========================
@router.get("/admin/home/sections/", response_model=list[HomeSectionOut])
def list_home_sections(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    sections = db.query(HomeSection).order_by(HomeSection.id.asc()).all()
    return sections


@router.get("/admin/home/sections/{key}", response_model=HomeSectionOut)
def get_home_section(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    section = db.query(HomeSection).filter(HomeSection.key == key).first()

    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seção não encontrada",
        )

    return section


@router.post(
    "/admin/home/sections/",
    response_model=HomeSectionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_home_section(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    content_type = request.headers.get("content-type", "").lower()

    if "multipart/form-data" in content_type:
        form = await request.form()
        payload = _parse_section_payload_from_form(form)
    else:
        body = await request.json()
        payload = HomeSectionCreate(**body)

    existing = db.query(HomeSection).filter(HomeSection.key == payload.key).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma seção com essa chave",
        )

    section = HomeSection(
        key=payload.key.strip(),
        title=(payload.title or "").strip() or None,
        subtitle=(payload.subtitle or "").strip() or None,
        data=payload.data or {},
        is_active=payload.is_active,
    )

    db.add(section)
    db.commit()
    db.refresh(section)

    return section


@router.put("/admin/home/sections/{key}", response_model=HomeSectionOut)
async def update_home_section(
    key: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    section = db.query(HomeSection).filter(HomeSection.key == key).first()

    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seção não encontrada",
        )

    content_type = request.headers.get("content-type", "").lower()

    if "multipart/form-data" in content_type:
        form = await request.form()
        payload = _parse_section_update_from_form(form, current_key=section.key)
    else:
        body = await request.json()
        payload = HomeSectionUpdate(**body)

    update_data = payload.model_dump(exclude_unset=True)

    if "key" in update_data and update_data["key"]:
        next_key = update_data["key"].strip()

        if next_key != section.key:
            existing = db.query(HomeSection).filter(HomeSection.key == next_key).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Já existe uma seção com essa chave",
                )
            section.key = next_key

    if "title" in update_data:
        section.title = (update_data["title"] or "").strip() or None

    if "subtitle" in update_data:
        section.subtitle = (update_data["subtitle"] or "").strip() or None

    if "data" in update_data:
        section.data = update_data["data"] or {}

    if "is_active" in update_data:
        section.is_active = bool(update_data["is_active"])

    db.commit()
    db.refresh(section)

    return section


@router.delete("/admin/home/sections/{key}")
def delete_home_section(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    section = db.query(HomeSection).filter(HomeSection.key == key).first()

    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seção não encontrada",
        )

    # remove imagens locais das seções
    data = _ensure_dict(section.data)

    if section.key in {"categories", "showcase", "campaigns"}:
        for item in _ensure_list(data.get("items")):
            _safe_remove_uploaded_file(_normalize_text((item or {}).get("image")), SECTIONS_UPLOAD_DIR)

    if section.key == "final_cta":
        _safe_remove_uploaded_file(_normalize_text(data.get("image")), SECTIONS_UPLOAD_DIR)

    db.delete(section)
    db.commit()

    return {"ok": True, "message": "Seção excluída com sucesso"}


# =========================
# BANNERS
# =========================
@router.get("/admin/home/banners/", response_model=list[HomeBannerOut])
def list_home_banners(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    banners = (
        db.query(HomeBanner)
        .order_by(HomeBanner.position.asc(), HomeBanner.id.desc())
        .all()
    )
    return banners


@router.get("/admin/home/banners/{banner_id}", response_model=HomeBannerOut)
def get_home_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    banner = db.query(HomeBanner).filter(HomeBanner.id == banner_id).first()

    if not banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner não encontrado",
        )

    return banner


@router.post(
    "/admin/home/banners/",
    response_model=HomeBannerOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_home_banner(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    content_type = request.headers.get("content-type", "").lower()

    created_image_url = None
    created_mobile_image_url = None
    created_video_url = None
    created_mobile_video_url = None

    try:
        if "multipart/form-data" in content_type:
            form = await request.form()

            title = _normalize_text(form.get("title"))
            subtitle = _normalize_text(form.get("subtitle"))
            button_text = _normalize_text(form.get("button_text"))
            button_link = _normalize_text(form.get("button_link"))

            image_url = _normalize_text(form.get("image_url"))
            mobile_image_url = _normalize_text(form.get("mobile_image_url"))
            video_url = _normalize_text(form.get("video_url"))
            mobile_video_url = _normalize_text(form.get("mobile_video_url"))

            position = _normalize_int(form.get("position"), default=0)
            is_active = _normalize_bool(form.get("is_active"), default=True)

            starts_at = _parse_datetime(form.get("starts_at"))
            ends_at = _parse_datetime(form.get("ends_at"))

            image_file = form.get("image_file")
            mobile_image_file = form.get("mobile_image_file")
            video_file = form.get("video_file")
            mobile_video_file = form.get("mobile_video_file")

            if _is_uploaded_file(image_file):
                created_image_url = _save_upload_file(image_file, BANNERS_UPLOAD_DIR)

            if _is_uploaded_file(mobile_image_file):
                created_mobile_image_url = _save_upload_file(mobile_image_file, BANNERS_UPLOAD_DIR)

            if _is_uploaded_file(video_file):
                created_video_url = _save_upload_file(video_file, BANNERS_UPLOAD_DIR)

            if _is_uploaded_file(mobile_video_file):
                created_mobile_video_url = _save_upload_file(mobile_video_file, BANNERS_UPLOAD_DIR)

            final_image_url = created_image_url or image_url
            final_mobile_image_url = created_mobile_image_url or mobile_image_url
            final_video_url = created_video_url or video_url
            final_mobile_video_url = created_mobile_video_url or mobile_video_url

            if not title:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Título é obrigatório",
                )

            if not final_image_url and not final_video_url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Envie pelo menos uma mídia principal: imagem desktop ou vídeo desktop.",
                )

            payload = HomeBannerCreate(
                title=title,
                subtitle=subtitle,
                button_text=button_text,
                button_link=button_link,
                image_url=final_image_url,
                mobile_image_url=final_mobile_image_url,
                video_url=final_video_url,
                mobile_video_url=final_mobile_video_url,
                position=position,
                is_active=is_active,
                starts_at=starts_at,
                ends_at=ends_at,
            )
        else:
            body = await request.json()
            payload = HomeBannerCreate(**body)

        banner = HomeBanner(
            title=payload.title,
            subtitle=payload.subtitle,
            button_text=payload.button_text,
            button_link=payload.button_link,
            image_url=payload.image_url,
            mobile_image_url=payload.mobile_image_url,
            video_url=payload.video_url,
            mobile_video_url=payload.mobile_video_url,
            position=payload.position,
            is_active=payload.is_active,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
        )

        db.add(banner)
        db.commit()
        db.refresh(banner)

        return banner

    except Exception:
        for file_url in [
            created_image_url,
            created_mobile_image_url,
            created_video_url,
            created_mobile_video_url,
        ]:
            _safe_remove_uploaded_file(file_url, BANNERS_UPLOAD_DIR)
        raise


@router.put("/admin/home/banners/{banner_id}", response_model=HomeBannerOut)
async def update_home_banner(
    banner_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    banner = db.query(HomeBanner).filter(HomeBanner.id == banner_id).first()

    if not banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner não encontrado",
        )

    content_type = request.headers.get("content-type", "").lower()

    if "multipart/form-data" in content_type:
        form = await request.form()

        title = _normalize_text(form.get("title"))
        subtitle = _normalize_text(form.get("subtitle"))
        button_text = _normalize_text(form.get("button_text"))
        button_link = _normalize_text(form.get("button_link"))

        image_url = _normalize_text(form.get("image_url"))
        mobile_image_url = _normalize_text(form.get("mobile_image_url"))
        video_url = _normalize_text(form.get("video_url"))
        mobile_video_url = _normalize_text(form.get("mobile_video_url"))

        position = _normalize_int(form.get("position"), default=banner.position)
        is_active = _normalize_bool(form.get("is_active"), default=banner.is_active)

        starts_at = _parse_datetime(form.get("starts_at"))
        ends_at = _parse_datetime(form.get("ends_at"))

        image_file = form.get("image_file")
        mobile_image_file = form.get("mobile_image_file")
        video_file = form.get("video_file")
        mobile_video_file = form.get("mobile_video_file")

        if _is_uploaded_file(image_file):
            _safe_remove_uploaded_file(banner.image_url, BANNERS_UPLOAD_DIR)
            banner.image_url = _save_upload_file(image_file, BANNERS_UPLOAD_DIR)
        else:
            banner.image_url = image_url or banner.image_url

        if _is_uploaded_file(mobile_image_file):
            _safe_remove_uploaded_file(banner.mobile_image_url, BANNERS_UPLOAD_DIR)
            banner.mobile_image_url = _save_upload_file(mobile_image_file, BANNERS_UPLOAD_DIR)
        else:
            banner.mobile_image_url = mobile_image_url or banner.mobile_image_url

        if _is_uploaded_file(video_file):
            _safe_remove_uploaded_file(banner.video_url, BANNERS_UPLOAD_DIR)
            banner.video_url = _save_upload_file(video_file, BANNERS_UPLOAD_DIR)
        else:
            banner.video_url = video_url or banner.video_url

        if _is_uploaded_file(mobile_video_file):
            _safe_remove_uploaded_file(banner.mobile_video_url, BANNERS_UPLOAD_DIR)
            banner.mobile_video_url = _save_upload_file(mobile_video_file, BANNERS_UPLOAD_DIR)
        else:
            banner.mobile_video_url = mobile_video_url or banner.mobile_video_url

        if title is not None:
            banner.title = title
        banner.subtitle = subtitle
        banner.button_text = button_text
        banner.button_link = button_link
        banner.position = position
        banner.is_active = is_active
        banner.starts_at = starts_at
        banner.ends_at = ends_at

    else:
        body = await request.json()
        payload = HomeBannerUpdate(**body)
        update_data = payload.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(banner, field, value)

    db.commit()
    db.refresh(banner)

    return banner


@router.delete("/admin/home/banners/{banner_id}")
def delete_home_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    banner = db.query(HomeBanner).filter(HomeBanner.id == banner_id).first()

    if not banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner não encontrado",
        )

    _safe_remove_uploaded_file(banner.image_url, BANNERS_UPLOAD_DIR)
    _safe_remove_uploaded_file(banner.mobile_image_url, BANNERS_UPLOAD_DIR)
    _safe_remove_uploaded_file(banner.video_url, BANNERS_UPLOAD_DIR)
    _safe_remove_uploaded_file(banner.mobile_video_url, BANNERS_UPLOAD_DIR)

    db.delete(banner)
    db.commit()

    return {"ok": True, "message": "Banner excluído com sucesso"}