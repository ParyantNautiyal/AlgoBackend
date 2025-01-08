from ..repositories.instrument_repository import InstrumentRepository
from ..utils.kite_connect import KiteApp
from ..database import get_db, execute_query_sync
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class InstrumentService:
    def __init__(self):
        self.repository = InstrumentRepository()
        self.kite_app = KiteApp()

    async def sync_instruments(self):
        """Fetch instruments from Kite and save to database"""
        try:
            instruments = self.kite_app.get_instruments()
            if not instruments:
                raise Exception("Failed to fetch instruments from Kite")

            with get_db() as cursor:
                await self.repository.save_instruments(cursor, instruments)
            return len(instruments)
        except Exception as e:
            logger.error(f"Error syncing instruments: {str(e)}")
            raise

    async def get_all_instruments(self):
        """Get all instruments from database"""
        with get_db() as cursor:
            result = execute_query_sync(cursor, "SELECT * FROM instruments")
            logger.info(f"Retrieved {len(result)} instruments")
            return result

    async def get_instrument_by_symbol(self, symbol: str):
        """Get instrument by symbol"""
        with get_db() as cursor:
            query = "SELECT * FROM instruments WHERE tradingsymbol = %s"
            result = execute_query_sync(cursor, query, (symbol,))
            return result[0] if result else None

    async def filter_instruments(self, exchange: str, segment: str, 
                               instrument_type: str, strike: float = None, 
                               expiry: str = None):
        """Filter instruments based on criteria"""
        with get_db() as cursor:
            query = """
            SELECT tradingsymbol, lot_size 
            FROM instruments 
            WHERE exchange = %s 
            AND segment = %s 
            AND instrument_type = %s
            """
            params = [exchange, segment, instrument_type]

            if strike:
                query += " AND strike = %s"
                params.append(strike)
            
            if expiry:
                query += " AND DATE(expiry) = DATE(%s)"
                params.append(expiry)

            return execute_query_sync(cursor, query, tuple(params)) 