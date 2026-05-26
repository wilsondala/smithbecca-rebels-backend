from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional
import csv
import io

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.newsletter import NewsletterSubscriber
from app.schemas.newsletter_campaign import NewsletterCampaignCreate
from app.services.email_service import send_email
from app.services.newsletter_campaign_templates import campaign_email

router = APIRouter(prefix="/admin/newsletter", tags=["Admin Newsletter"])


def admin_only(current_user: User):
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Acesso permitido apenas para ADMIN")


@router.get("/stats")
def newsletter_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    admin_only(current_user)
    total = db.query(func.count(NewsletterSubscriber.id)).scalar() or 0
    return {"ok": True, "total": total}


@router.get("/subscribers")
def list_subscribers(
    q: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    admin_only(current_user)

    query = db.query(NewsletterSubscriber).order_by(NewsletterSubscriber.created_at.desc())

    if q:
        q_clean = f"%{q.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(func.coalesce(NewsletterSubscriber.email, "")).like(q_clean),
                func.lower(func.coalesce(NewsletterSubscriber.name, "")).like(q_clean),
                func.lower(func.coalesce(NewsletterSubscriber.phone, "")).like(q_clean),
            )
        )

    total = query.count()
    rows = query.offset(offset).limit(min(limit, 500)).all()

    return {
        "ok": True,
        "total": total,
        "items": [
            {
                "id": r.id,
                "name": r.name,
                "phone": r.phone,
                "email": r.email,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }


@router.get("/export.csv")
def export_subscribers_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    admin_only(current_user)

    rows = db.query(NewsletterSubscriber).order_by(NewsletterSubscriber.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "name", "phone", "email", "created_at"])

    for r in rows:
        writer.writerow([
            r.id,
            r.name or "",
            r.phone or "",
            r.email or "",
            r.created_at.isoformat() if r.created_at else "",
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="newsletter_subscribers.csv"'},
    )


@router.post("/campaign")
def send_campaign_to_all(
    payload: NewsletterCampaignCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    admin_only(current_user)

    subs = db.query(NewsletterSubscriber.email).all()
    emails = [e[0] for e in subs if e and e[0]]

    subject, html, text = campaign_email(
        payload.subject,
        payload.title,
        payload.message,
        payload.cta_text,
        payload.cta_url,
    )

    def job():
      for to_email in emails:
          try:
              send_email(to_email, subject, html, text)
          except Exception as e:
              print("Falha ao enviar campanha para:", to_email, e)

    background.add_task(job)

    return {
        "ok": True,
        "queued": len(emails),
        "message": f"Campanha colocada na fila para {len(emails)} inscritos."
    }