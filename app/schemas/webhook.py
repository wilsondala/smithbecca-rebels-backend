from pydantic import BaseModel


class ExpressWebhook(BaseModel):
    order_id: int
    payment_reference: str
    status: str  # "paid" ou "failed"
