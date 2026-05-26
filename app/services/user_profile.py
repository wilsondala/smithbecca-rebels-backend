from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserUpdate

def update_profile(db: Session, user: User, payload: UserUpdate) -> User:
    if payload.name is not None:
        user.name = payload.name

    if payload.phone is not None:
        user.phone = payload.phone

    if payload.photo is not None:
        user.photo = payload.photo

    db.add(user)
    db.commit()
    db.refresh(user)
    return user