from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


class ProductVariation(BaseModel):
    color: str
    images: List[str] = Field(default_factory=list)


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    stock: int

    category: Optional[str] = None
    subcategory: Optional[str] = None

    is_wholesale: bool = False
    wholesale_price: Optional[Decimal] = None
    is_kit: bool = False

    sizes: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    shoe_sizes: Optional[List[str]] = None

    images: Optional[List[str]] = None
    video_url: Optional[str] = None

    # NOVO
    variations: Optional[List[ProductVariation]] = None

    reviews: Optional[List[dict]] = None
    rating_avg: Optional[Decimal] = None
    rating_count: int = 0


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None

    category: Optional[str] = None
    subcategory: Optional[str] = None

    is_wholesale: Optional[bool] = None
    wholesale_price: Optional[Decimal] = None
    is_kit: Optional[bool] = None

    sizes: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    shoe_sizes: Optional[List[str]] = None

    images: Optional[List[str]] = None
    video_url: Optional[str] = None

    # NOVO
    variations: Optional[List[ProductVariation]] = None

    is_active: Optional[bool] = None

    reviews: Optional[List[dict]] = None
    rating_avg: Optional[Decimal] = None
    rating_count: Optional[int] = None


class ProductOut(ProductBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True