from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class NewsletterCampaignCreate(BaseModel):
    subject: str = Field(..., min_length=3, max_length=120)
    title: str = Field(..., min_length=3, max_length=80)
    message: str = Field(..., min_length=3, max_length=2000)
    cta_text: Optional[str] = Field(default="Ver novidades", max_length=40)
    cta_url: Optional[str] = Field(default=None, max_length=300)