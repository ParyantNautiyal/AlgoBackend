from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..utils.kite_connect import KiteApp
from ..database import get_db
from ..services.instrument_service import InstrumentService
from ..repositories.instrument_repository import InstrumentRepository
from typing import List, Dict
from logging import getLogger

logger = getLogger(__name__)

router = APIRouter(prefix="/kite", tags=["kite"])
kite_app = KiteApp()

@router.get("/login")
async def login():
    """Generate login URL for Kite Connect"""
    try:
        login_url = kite_app.kite.login_url()
        return {"login_url": login_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/callback")
async def callback():
    """Handle callback from Kite Connect after login"""
    if kite_app.set_access_token():
        return {"message": "Successfully authenticated"}
    raise HTTPException(status_code=400, detail="Failed to set access token")

@router.get("/instruments")
async def get_instruments():
    """Fetch all instruments"""
    if not kite_app.access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    instruments = kite_app.get_instruments()
    if instruments is None:
        raise HTTPException(status_code=500, detail="Failed to fetch instruments")
    
    return instruments 

@router.get("/sync-instruments")
async def sync_instruments(db: Session = Depends(get_db)):
    """Fetch instruments from Kite and save to database"""
    if not kite_app.access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    instruments = kite_app.get_instruments()
    if instruments is None:
        raise HTTPException(status_code=500, detail="Failed to fetch instruments")
    
    await InstrumentRepository.save_instruments(db, instruments)
    return {"message": "Instruments synced successfully"}

@router.get("/db-instruments")
async def get_db_instruments(db: Session = Depends(get_db)):
    """Get instruments from database"""
    instruments = await InstrumentService.get_all_instruments(db)
    return instruments 