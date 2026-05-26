from pydantic import BaseModel, EmailStr


class UserUpdate(BaseModel):
    name: str | None = None
    photo: str | None = None
    phone: str | None = None


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str | None = None
    photo: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str | None
    photo: str | None
    role: str | None = None
    is_active: bool | None = None
    auth_provider: str | None = None
    google_id: str | None = None
    facebook_id: str | None = None

    class Config:
        from_attributes = True