from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class InstrumentBase(BaseModel):
    instrument_token: int
    exchange_token: int
    tradingsymbol: str
    name: str
    last_price: Optional[float] = None
    expiry: Optional[datetime] = None
    strike: Optional[float] = None
    tick_size: float
    lot_size: int
    instrument_type: str
    segment: str
    exchange: str

class InstrumentCreate(InstrumentBase):
    pass

class Instrument(InstrumentBase):
    id: int

    class Config:
        orm_mode = True 