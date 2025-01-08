import pytest
import logging
from app.services.instrument_service import InstrumentService

logger = logging.getLogger(__name__)

@pytest.fixture
def instrument_service():
    return InstrumentService()

@pytest.mark.asyncio
async def test_filter_instruments(instrument_service):
    """Test instrument filtering"""
    logger.info("Starting instrument filter test")
    try:
        instruments = await instrument_service.filter_instruments(
            exchange="NSE",
            segment="NFO",
            instrument_type="CE",
            strike=18000
        )
        logger.info(f"Found {len(instruments)} matching instruments")
        assert instruments is not None, "Should return a list"
        for instrument in instruments:
            assert 'tradingsymbol' in instrument, "Each instrument should have a tradingsymbol"
            assert 'lot_size' in instrument, "Each instrument should have a lot_size"
            logger.info(f"Validated instrument: {instrument['tradingsymbol']}")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_get_instrument_by_symbol(instrument_service):
    """Test getting instrument by symbol"""
    logger.info("Starting get_instrument_by_symbol test")
    try:
        symbol = "NIFTY24MAR18000CE"  # Adjust symbol as needed
        instrument = await instrument_service.get_instrument_by_symbol(symbol)
        logger.info(f"Retrieved instrument: {instrument}")
        if instrument:
            assert instrument['tradingsymbol'] == symbol, "Symbol should match"
            logger.info("Symbol validation successful")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise 