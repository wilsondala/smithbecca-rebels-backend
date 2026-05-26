from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal


class NewsletterCreate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    phone: Optional[str] = Field(default=None, min_length=9, max_length=30)
    email: Optional[EmailStr] = None
    preferred_channel: Literal["whatsapp", "email", "both"] = "whatsapp"