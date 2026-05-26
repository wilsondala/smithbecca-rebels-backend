import secrets

import requests
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password
from app.core.config import (
    GOOGLE_CLIENT_ID,
    FACEBOOK_APP_ID,
    FACEBOOK_APP_SECRET,
)


def create_user(db: Session, user: UserCreate) -> User:
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado.")

    new_user = User(
        name=user.name,
        email=user.email,
        phone=user.phone,
        password_hash=get_password_hash(user.password),
        role="customer",
        is_active=True,
        photo=getattr(user, "photo", None),
        auth_provider="local",
        google_id=None,
        facebook_id=None,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None

    if hasattr(user, "is_active") and not user.is_active:
        return None

    if not getattr(user, "password_hash", None):
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def verify_google_token(id_token: str) -> dict:
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GOOGLE_CLIENT_ID não configurado no servidor.",
        )

    try:
        token_data = google_id_token.verify_oauth2_token(
            id_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Google inválido.",
        )

    email = token_data.get("email")
    email_verified = token_data.get("email_verified")
    google_sub = token_data.get("sub")

    if not email or not google_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Google sem dados obrigatórios.",
        )

    if not email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email Google não verificado.",
        )

    return token_data


def authenticate_or_create_google_user(db: Session, id_token: str) -> User:
    token_data = verify_google_token(id_token)

    email = token_data.get("email", "").strip().lower()
    name = (token_data.get("name") or email.split("@")[0]).strip()
    picture = token_data.get("picture")
    google_sub = token_data.get("sub")

    user = db.query(User).filter(User.email == email).first()

    if user:
        if hasattr(user, "is_active") and not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo. Entre em contato com o administrador.",
            )

        updated = False

        if getattr(user, "google_id", None) in (None, ""):
            user.google_id = google_sub
            updated = True

        auth_provider = getattr(user, "auth_provider", "local")
        if auth_provider in (None, "", "local"):
            user.auth_provider = "google"
            updated = True

        if picture and not getattr(user, "photo", None):
            user.photo = picture
            updated = True

        if name and not getattr(user, "name", None):
            user.name = name
            updated = True

        if updated:
            db.commit()
            db.refresh(user)

        return user

    random_password = secrets.token_urlsafe(32)

    new_user = User(
        name=name,
        email=email,
        phone=None,
        password_hash=get_password_hash(random_password),
        role="customer",
        is_active=True,
        photo=picture,
        auth_provider="google",
        google_id=google_sub,
        facebook_id=None,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def verify_facebook_token(access_token: str) -> dict:
    if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="FACEBOOK_APP_ID ou FACEBOOK_APP_SECRET não configurados no servidor.",
        )

    app_access_token = f"{FACEBOOK_APP_ID}|{FACEBOOK_APP_SECRET}"

    try:
        debug_resp = requests.get(
            "https://graph.facebook.com/debug_token",
            params={
                "input_token": access_token,
                "access_token": app_access_token,
            },
            timeout=10,
        )
        debug_resp.raise_for_status()
        debug_data = debug_resp.json().get("data", {})
    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível validar o token do Facebook.",
        )

    if not debug_data.get("is_valid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Facebook inválido.",
        )

    if str(debug_data.get("app_id")) != str(FACEBOOK_APP_ID):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Facebook emitido para outro aplicativo.",
        )

    try:
        me_resp = requests.get(
            "https://graph.facebook.com/me",
            params={
                "fields": "id,name,email,picture.type(large)",
                "access_token": access_token,
            },
            timeout=10,
        )
        me_resp.raise_for_status()
        profile = me_resp.json()
    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível obter os dados do usuário no Facebook.",
        )

    facebook_id = profile.get("id")
    email = (profile.get("email") or "").strip().lower()
    name = (profile.get("name") or "").strip()
    picture = (
        profile.get("picture", {})
        .get("data", {})
        .get("url")
    )

    if not facebook_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Facebook não retornou o identificador do usuário.",
        )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Facebook não retornou email. Autorize o email no login do Facebook.",
        )

    return {
        "facebook_id": facebook_id,
        "email": email,
        "name": name or email.split("@")[0],
        "picture": picture,
    }


def authenticate_or_create_facebook_user(db: Session, access_token: str) -> User:
    token_data = verify_facebook_token(access_token)

    email = token_data["email"]
    name = token_data["name"]
    picture = token_data.get("picture")
    facebook_id = token_data["facebook_id"]

    user = db.query(User).filter(User.email == email).first()

    if user:
        if hasattr(user, "is_active") and not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo. Entre em contato com o administrador.",
            )

        updated = False

        if getattr(user, "facebook_id", None) in (None, ""):
            user.facebook_id = facebook_id
            updated = True

        auth_provider = getattr(user, "auth_provider", "local")
        if auth_provider in (None, "", "local"):
            user.auth_provider = "facebook"
            updated = True

        if picture and not getattr(user, "photo", None):
            user.photo = picture
            updated = True

        if name and not getattr(user, "name", None):
            user.name = name
            updated = True

        if updated:
            db.commit()
            db.refresh(user)

        return user

    random_password = secrets.token_urlsafe(32)

    new_user = User(
        name=name,
        email=email,
        phone=None,
        password_hash=get_password_hash(random_password),
        role="customer",
        is_active=True,
        photo=picture,
        auth_provider="facebook",
        google_id=None,
        facebook_id=facebook_id,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user