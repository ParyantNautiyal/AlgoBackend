import datetime
import pytest
import logging
from app.services.order_service import OrderService
from app.schemas.order import OrderCreate

logger = logging.getLogger(__name__)

@pytest.fixture
def order_service():
    return OrderService()

@pytest.mark.asyncio
async def test_create_order(order_service):
    """Test order creation"""
    logger.info("Starting order creation test")
    try:
        order_data = OrderCreate(
            symbol="NIFTY24MAR18000CE",
            order_type="MARKET",
            quantity=50,
            price=None,
            status="PENDING",
            created_at=datetime.datetime.now()
        )
        logger.info(f"Creating order for {order_data.symbol}")
        try:
            order_id = await order_service.create_order(order_data.model_dump())
            logger.info(f"Order created with ID: {order_id}")
            assert isinstance(order_id, int), "Order ID should be an integer"
        except Exception as e:
            logger.error(f"Order creation failed in test_create_order: {str(e)}")
            raise

        # Verify order
        order = await order_service.get_order(order_id)
        assert order is not None, "Order should exist"
        assert order['symbol'] == order_data.symbol, "Symbol should match"
        logger.info("Order verification successful")
    except Exception as e:
        logger.error(f"Order creation failed: {str(e)}")
        raise 

