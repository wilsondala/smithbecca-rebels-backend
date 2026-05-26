from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

from app.database.session import get_db
from app.schemas.newsletter import NewsletterCreate
from app.models.newsletter import NewsletterSubscriber

from app.services.email_service import send_email
from app.services.newsletter_email_templates import newsletter_welcome_email

router = APIRouter(prefix="/newsletter", tags=["Newsletter"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def subscribe(payload: NewsletterCreate, db: Session = Depends(get_db)):
    name = payload.name.strip() if payload.name else None
    phone = payload.phone.strip() if payload.phone else None
    email = str(payload.email).strip().lower() if payload.email else None
    preferred_channel = payload.preferred_channel

    # ✅ valida conforme preferência
    if preferred_channel == "whatsapp" and not phone:
        raise HTTPException(
            status_code=400,
            detail="Telefone/WhatsApp é obrigatório para receber novidades por WhatsApp."
        )

    if preferred_channel == "email" and not email:
        raise HTTPException(
            status_code=400,
            detail="E-mail é obrigatório para receber novidades por e-mail."
        )

    if preferred_channel == "both" and (not phone or not email):
        raise HTTPException(
            status_code=400,
            detail="Telefone e e-mail são obrigatórios para receber novidades nos dois canais."
        )

    try:
        # ✅ monta filtros apenas com os dados preenchidos
        filters = []
        if phone:
            filters.append(NewsletterSubscriber.phone == phone)
        if email:
            filters.append(NewsletterSubscriber.email == email)

        if filters:
            existing = db.query(NewsletterSubscriber).filter(or_(*filters)).first()
        else:
            existing = None

        if existing:
            return {
                "ok": True,
                "type": "info",
                "message": "ℹ️ Você já está cadastrado! Em breve você receberá nossas novidades."
            }

        sub = NewsletterSubscriber(
            name=name,
            phone=phone,
            email=email,
            preferred_channel=preferred_channel,
        )

        db.add(sub)
        db.commit()

        # ✅ envia e-mail de boas-vindas só se houver email
        if email:
            subject, html, text = newsletter_welcome_email(name, email)
            try:
                send_email(email, subject, html, text)
            except Exception as e:
                print("Falha ao enviar e-mail newsletter:", e)

        return {
            "ok": True,
            "type": "success",
            "message": "✅ Cadastro realizado com sucesso! Em breve você receberá nossas novidades."
        }

    except IntegrityError:
        db.rollback()
        return {
            "ok": True,
            "type": "info",
            "message": "ℹ️ Você já está cadastrado! Em breve você receberá nossas novidades."
        }
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Não foi possível concluir seu cadastro. Tente novamente."
        )