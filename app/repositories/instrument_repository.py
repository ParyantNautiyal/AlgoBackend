from typing import List, Dict, Any
from ..database import execute_query_sync
import logging

logger = logging.getLogger(__name__)

class InstrumentRepository:
    @staticmethod
    async def save_instruments(cursor, instruments: List[Dict[Any, Any]]):
        """Save or update instruments in database"""
        query = """
        INSERT INTO instruments (
            instrument_token, exchange_token, tradingsymbol, name, 
            last_price, expiry, strike, tick_size, lot_size, 
            instrument_type, segment, exchange
        ) VALUES (
            %(instrument_token)s, %(exchange_token)s, %(tradingsymbol)s, 
            %(name)s, %(last_price)s, %(expiry)s, %(strike)s, 
            %(tick_size)s, %(lot_size)s, %(instrument_type)s, 
            %(segment)s, %(exchange)s
        ) ON DUPLICATE KEY UPDATE
            last_price = VALUES(last_price),
            expiry = VALUES(expiry),
            strike = VALUES(strike),
            tick_size = VALUES(tick_size),
            lot_size = VALUES(lot_size)
        """
        
        for instrument in instruments:
            execute_query_sync(cursor, query, instrument)

    @staticmethod
    async def get_all_instruments(cursor) -> List[dict]:
        """Get all instruments from database"""
        query = "SELECT * FROM instruments"
        return execute_query_sync(cursor, query)

    @staticmethod
    async def get_instrument_by_symbol(cursor, symbol: str) -> dict:
        """Get instrument by symbol"""
        logger.info(f"{__name__} testing get_instrument_by_symbol")
        query = "SELECT * FROM instruments WHERE tradingsymbol = %s"
        result = execute_query_sync(cursor, query, (symbol,))
        logger.info(f" Testing get_instrument_by_symbol -> result : {result}")
        return result[0] if result else None 

    @staticmethod
    async def execute_custom_query(cursor, query: str, params: tuple) -> List[dict]:
        """Execute custom query with parameters"""
        return execute_query_sync(cursor, query, params) 