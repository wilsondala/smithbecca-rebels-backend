from pydantic import BaseModel

class ExpressPaymentResponse(BaseModel):
    reference: str
    amount: float
    currency: str
    message: str
