import os
from urllib.parse import urlencode
from uuid import uuid4

import requests
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_db
from app.schemas.user import UserCreate, UserOut
from app.services.auth import (
    create_user,
    authenticate_user,
    authenticate_or_create_google_user,
    authenticate_or_create_facebook_user,
)
from app.core.security import create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

UPLOAD_DIR = "uploads/users"
os.makedirs(UPLOAD_DIR, exist_ok=True)

FACEBOOK_REDIRECT_URI = os.getenv(
    "FACEBOOK_REDIRECT_URI",
    "https://api.paixaoangola.com/api/v1/auth/facebook/callback",
).strip()
FRONTEND_LOGIN_URL = os.getenv(
    "FRONTEND_LOGIN_URL",
    "https://www.paixaoangola.com/login",
).strip()
FACEBOOK_APP_ID = (os.getenv("FACEBOOK_APP_ID") or "").strip()
FACEBOOK_APP_SECRET = (os.getenv("FACEBOOK_APP_SECRET") or "").strip()


class GoogleLoginRequest(BaseModel):
    id_token: str


class FacebookLoginRequest(BaseModel):
    access_token: str


def build_token_payload(user) -> dict:
    return {
        "sub": str(user.id),
        "role": getattr(user, "role", "customer"),
        "email": getattr(user, "email", ""),
        "name": getattr(user, "name", ""),
        "photo": getattr(user, "photo", None),
        "auth_provider": getattr(user, "auth_provider", "local"),
    }


@router.post("/register")
def register(payload: UserCreate, db: Session = Depends(get_db)):
    user = create_user(db, payload)

    token = create_access_token(build_token_payload(user))

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserOut.model_validate(user),
    }


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos.",
        )

    token = create_access_token(build_token_payload(user))

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserOut.model_validate(user),
    }


@router.post("/google")
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    user = authenticate_or_create_google_user(db, payload.id_token)

    token = create_access_token(build_token_payload(user))

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserOut.model_validate(user),
    }


@router.post("/facebook")
def facebook_login(payload: FacebookLoginRequest, db: Session = Depends(get_db)):
    user = authenticate_or_create_facebook_user(db, payload.access_token)

    token = create_access_token(build_token_payload(user))

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserOut.model_validate(user),
    }


@router.get("/facebook/callback", name="facebook_callback")
def facebook_callback(
    code: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if error:
        query = urlencode(
            {
                "facebook_error": error_description or error,
            }
        )
        return RedirectResponse(url=f"{FRONTEND_LOGIN_URL}?{query}", status_code=302)

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de autorização do Facebook não informado.",
        )

    if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="FACEBOOK_APP_ID ou FACEBOOK_APP_SECRET não configurados no servidor.",
        )

    try:
        token_resp = requests.get(
            "https://graph.facebook.com/v19.0/oauth/access_token",
            params={
                "client_id": FACEBOOK_APP_ID,
                "redirect_uri": FACEBOOK_REDIRECT_URI,
                "client_secret": FACEBOOK_APP_SECRET,
                "code": code,
            },
            timeout=15,
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível trocar o código do Facebook por token.",
        )

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Facebook não retornou access_token.",
        )

    user = authenticate_or_create_facebook_user(db, access_token)
    token = create_access_token(build_token_payload(user))

    redirect_url = f"{FRONTEND_LOGIN_URL}#access_token={token}&provider=facebook"
    return RedirectResponse(url=redirect_url, status_code=302)


@router.put("/update-profile")
async def update_user_profile(
    name: str | None = Form(default=None),
    phone: str | None = Form(default=None),
    photo: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if name is not None:
        current_user.name = name

    if phone is not None:
        current_user.phone = phone

    if photo is not None:
        if photo.content_type not in ("image/jpeg", "image/png", "image/webp"):
            raise HTTPException(status_code=400, detail="Formato de imagem inválido.")

        ext = os.path.splitext(photo.filename or "")[1].lower()
        if ext not in (".jpg", ".jpeg", ".png", ".webp"):
            ext = ".jpg" if photo.content_type == "image/jpeg" else ".png"

        filename = f"{uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        content = await photo.read()
        with open(filepath, "wb") as f:
            f.write(content)

        current_user.photo = f"/uploads/users/{filename}"

    db.commit()
    db.refresh(current_user)

    new_token = create_access_token(build_token_payload(current_user))

    return {
        "user": UserOut.model_validate(current_user),
        "access_token": new_token,
        "token_type": "bearer",
    }
