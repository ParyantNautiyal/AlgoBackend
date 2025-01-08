from fastapi import APIRouter, HTTPException
from typing import List
from ..services.instrument_service import InstrumentService
from ..schemas.instrument import Instrument

router = APIRouter(prefix="/instruments", tags=["instruments"])
instrument_service = InstrumentService()

@router.post("/sync")
async def sync_instruments():
    """Sync instruments from Kite"""
    try:
        count = await instrument_service.sync_instruments()
        return {"message": f"Successfully synced {count} instruments"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[Instrument])
async def get_instruments():
    """Get all instruments"""
    try:
        return await instrument_service.get_all_instruments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}", response_model=Instrument)
async def get_instrument(symbol: str):
    """Get instrument by symbol"""
    instrument = await instrument_service.get_instrument_by_symbol(symbol)
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return instrument 

@router.get("/filter")
async def filter_instruments(
    exchange: str,
    segment: str,
    instrument_type: str,
    strike: float = None,
    expiry: str = None
):
    """Get instruments filtered by criteria"""
    try:
        instruments = await instrument_service.filter_instruments(
            exchange, segment, instrument_type, strike, expiry
        )
        return instruments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 