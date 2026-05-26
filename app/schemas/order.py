from pydantic import BaseModel, Field
from decimal import Decimal
from typing import List, Optional


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class OrderCreate(BaseModel):
    payment_method: str
    delivery_address: Optional[str] = None

    customer_name: Optional[str] = Field(default=None, max_length=160)

    # 🔥 ADICIONA ISSO
    phone: Optional[str] = Field(default=None, max_length=20)

    address_line: Optional[str] = Field(default=None, max_length=255)
    neighborhood: Optional[str] = Field(default=None, max_length=160)
    reference: Optional[str] = Field(default=None, max_length=255)

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    items: List[OrderItemCreate]


class OrderItemOut(BaseModel):
    product_id: int
    quantity: int
    price: Decimal
    product_image: Optional[str] = None


class ProductSimple(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    status: str
    product_image: Optional[str] = None
    product: ProductSimple

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    status: str
    payment_method: str

    payment_status: Optional[str] = None
    payment_reference: Optional[str] = None

    total_amount: Optional[Decimal] = Decimal("0.00")
    delivery_fee: Optional[Decimal] = Decimal("0.00")

    delivery_address: Optional[str] = None

    customer_name: Optional[str] = None
    phone: Optional[str] = Field(default=None, max_length=20)  # 🔥 NOVO
    address_line: Optional[str] = None
    neighborhood: Optional[str] = None
    reference: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None

    items: List["OrderItemResponse"] = []

    class Config:
        from_attributes = True


class OrderConfirmDelivery(BaseModel):
    payment_method: str