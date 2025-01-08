import pytest
import logging
from app.repositories.instrument_repository import InstrumentRepository
from app.database import get_db

logger = logging.getLogger(__name__)

@pytest.fixture
def sample_instrument():
    return {
        'instrument_token': 12345,
        'exchange_token': 1234,
        'tradingsymbol': 'TEST1234',
        'name': 'Test Instrument',
        'last_price': 100.0,
        'expiry': '2024-03-28',
        'strike': 18000.0,
        'tick_size': 0.05,
        'lot_size': 50,
        'instrument_type': 'CE',
        'segment': 'NFO',
        'exchange': 'NSE'
    }

@pytest.mark.asyncio
async def test_save_and_get_instrument(sample_instrument):
    """Test saving and retrieving an instrument"""
    logger.info("Starting instrument save and retrieve test")
    logger.info(f"Test instrument data: {sample_instrument}")

    with get_db() as cursor:
        try:
            # Save instrument
            logger.info("Attempting to save instrument...")
            await InstrumentRepository.save_instruments(cursor, [sample_instrument])
            logger.info("Instrument saved successfully")
            
            # Retrieve and verify
            logger.info(f"Retrieving instrument with symbol: {sample_instrument['tradingsymbol']}")
            result = await InstrumentRepository.get_instrument_by_symbol(
                cursor, sample_instrument['tradingsymbol']
            )
            
            assert result is not None, "Retrieved instrument should not be None"
            assert result['tradingsymbol'] == sample_instrument['tradingsymbol'], "Tradingsymbol mismatch"
            logger.info("Instrument retrieved and verified successfully")
            logger.info(f"Retrieved instrument: {result}")

        except Exception as e:
            logger.error(f"Test failed: {str(e)}")
            logger.exception("Detailed error information:")
            raise 