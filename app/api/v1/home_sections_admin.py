from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.home_section import HomeSection
from app.models.user import User
from app.schemas.home_section import (
    HomeSectionCreate,
    HomeSectionOut,
    HomeSectionUpdate,
)

router = APIRouter(prefix="/admin/home/sections", tags=["Admin Home Sections"])


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


@router.get("/", response_model=list[HomeSectionOut])
def list_home_sections(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        sections = db.query(HomeSection).order_by(HomeSection.id.asc()).all()
        return sections
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar seções: {str(e)}",
        )


@router.get("/{section_key}", response_model=HomeSectionOut)
def get_home_section(
    section_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        normalized_key = section_key.strip().lower()

        section = (
            db.query(HomeSection)
            .filter(HomeSection.key == normalized_key)
            .first()
        )

        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seção não encontrada",
            )

        return section
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar seção: {str(e)}",
        )


@router.post("/", response_model=HomeSectionOut, status_code=status.HTTP_201_CREATED)
def create_home_section(
    payload: HomeSectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        normalized_key = payload.key.strip().lower()

        existing = (
            db.query(HomeSection)
            .filter(HomeSection.key == normalized_key)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A seção '{normalized_key}' já existe",
            )

        section = HomeSection(
            key=normalized_key,
            title=payload.title.strip() if payload.title else None,
            subtitle=payload.subtitle.strip() if payload.subtitle else None,
            data=payload.data if payload.data is not None else {},
            is_active=payload.is_active,
        )

        db.add(section)
        db.commit()
        db.refresh(section)
        return section

    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro de integridade ao criar seção: {str(e.orig)}",
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro de banco ao criar seção: {str(e)}",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao criar seção: {str(e)}",
        )


@router.put("/{section_key}", response_model=HomeSectionOut)
def update_home_section(
    section_key: str,
    payload: HomeSectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        normalized_key = section_key.strip().lower()

        section = (
            db.query(HomeSection)
            .filter(HomeSection.key == normalized_key)
            .first()
        )

        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seção não encontrada",
            )

        if hasattr(payload, "model_dump"):
            update_data = payload.model_dump(exclude_unset=True)
        else:
            update_data = payload.dict(exclude_unset=True)

        if "key" in update_data and update_data["key"]:
            update_data["key"] = update_data["key"].strip().lower()

            existing = (
                db.query(HomeSection)
                .filter(
                    HomeSection.key == update_data["key"],
                    HomeSection.id != section.id,
                )
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A seção '{update_data['key']}' já existe",
                )

        if "title" in update_data and isinstance(update_data["title"], str):
            update_data["title"] = update_data["title"].strip() or None

        if "subtitle" in update_data and isinstance(update_data["subtitle"], str):
            update_data["subtitle"] = update_data["subtitle"].strip() or None

        for field, value in update_data.items():
            setattr(section, field, value)

        db.commit()
        db.refresh(section)
        return section

    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro de integridade ao atualizar seção: {str(e.orig)}",
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro de banco ao atualizar seção: {str(e)}",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao atualizar seção: {str(e)}",
        )


@router.delete("/{section_key}")
def delete_home_section(
    section_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    try:
        normalized_key = section_key.strip().lower()

        section = (
            db.query(HomeSection)
            .filter(HomeSection.key == normalized_key)
            .first()
        )

        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Seção não encontrada",
            )

        db.delete(section)
        db.commit()

        return {"ok": True, "message": "Seção excluída com sucesso"}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao excluir seção: {str(e)}",
        )