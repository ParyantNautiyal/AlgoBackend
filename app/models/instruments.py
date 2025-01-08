from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from ..database import Base

class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, index=True)
    instrument_token = Column(Integer, unique=True, index=True)
    exchange_token = Column(Integer)
    tradingsymbol = Column(String, index=True)
    name = Column(String)
    last_price = Column(Float)
    expiry = Column(DateTime, nullable=True)
    strike = Column(Float, nullable=True)
    tick_size = Column(Float)
    lot_size = Column(Integer)
    instrument_type = Column(String)
    segment = Column(String)
    exchange = Column(String) 