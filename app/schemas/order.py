from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class OrderBase(BaseModel):
    trading_symbol: str
    order_type: str
    quantity: int
    trigger_price: Optional[float] = None
    order_limit: Optional[float] = None
    variety: str
    validity: str
    product: str

class OrderCreate(OrderBase):
    status: str = "ACTIVE"  # Default status
    created_at: datetime = datetime.now()  # Default to current time

class Order(OrderBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True  # Changed from orm_mode=True for newer Pydantic versions 