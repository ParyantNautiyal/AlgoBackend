import pytest
import logging
from app.utils.kite_connect import KiteApp

logger = logging.getLogger(__name__)

def test_kite_initialization():
    """Test KiteApp initialization"""
    logger.info("Starting KiteApp initialization test")
    try:
        kite_app = KiteApp()
        assert kite_app.api_key is not None
        assert kite_app.api_secret is not None
        assert kite_app.kite is not None
        logger.info("KiteApp initialized successfully")
    except Exception as e:
        logger.error(f"KiteApp initialization failed: {str(e)}")
        raise

def test_get_instruments():
    """Test fetching instruments"""
    logger.info("Starting instruments fetch test")
    try:
        kite_app = KiteApp()
        instruments = kite_app.get_instruments()
        assert instruments is not None
        assert len(instruments) > 0
        logger.info(f"Successfully fetched {len(instruments)} instruments")
        
        # Check instrument structure
        instrument = instruments[0]
        required_fields = ['instrument_token', 'exchange_token', 'tradingsymbol']
        for field in required_fields:
            assert field in instrument
        logger.info("Instrument structure validation successful")
    except Exception as e:
        logger.error(f"Instrument fetch failed: {str(e)}")
        raise 