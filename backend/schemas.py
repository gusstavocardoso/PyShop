from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ─── Product ────────────────────────────────────────────────────────────────

class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    category: str
    image_url: str
    stock: int = 100


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Order Items ─────────────────────────────────────────────────────────────

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float

    model_config = {"from_attributes": True}


# ─── Order ──────────────────────────────────────────────────────────────────

class OrderCreate(BaseModel):
    customer_name: str
    customer_email: str
    address: str
    city: str
    postal_code: str
    items: List[OrderItemCreate]


class OrderResponse(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    address: str
    city: str
    postal_code: str
    total: float
    status: str
    created_at: datetime
    items: List[OrderItemResponse]

    model_config = {"from_attributes": True}
