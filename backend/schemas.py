from datetime import datetime
from pydantic import BaseModel, EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


class StockCreate(BaseModel):
    item_name: str
    quantity: int
    price_per_unit: float


class StockUpdate(BaseModel):
    item_name: str
    quantity: int
    price_per_unit: float


class StockOut(BaseModel):
    id: int
    item_name: str
    quantity: int
    price_per_unit: float
    added_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class SaleItemInput(BaseModel):
    stock_id: int
    quantity: int


class SaleCreate(BaseModel):
    buyer_id: int
    items: list[SaleItemInput]


class SaleItemOut(BaseModel):
    item_name: str
    quantity: int
    price: float

    class Config:
        from_attributes = True


class SaleOut(BaseModel):
    id: int
    buyer_id: int
    sold_by: int
    total_amount: float
    created_at: datetime
    items: list[SaleItemOut]

    class Config:
        from_attributes = True
