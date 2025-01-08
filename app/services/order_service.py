from typing import Dict, Any
from ..repositories.order_repository import OrderRepository
from ..schemas.order import OrderCreate
from ..database import get_db, execute_query_sync
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class OrderService:
    def __init__(self):
        self.repository = OrderRepository()

    @staticmethod
    async def create_order(order_data: OrderCreate) -> int:
        """Create a new order"""
        # Convert Pydantic model to dict and format datetime
        order_dict = order_data.model_dump()
        order_dict['created_at'] = order_dict['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Creating order with processed data: {order_dict}")

        query = """
        INSERT INTO orders (
            trading_symbol, order_type, quantity, 
            trigger_price, order_limit, variety, 
            validity, product, status, created_at
        ) VALUES (
            %(trading_symbol)s, %(order_type)s, %(quantity)s, 
            %(trigger_price)s, %(order_limit)s, %(variety)s, 
            %(validity)s, %(product)s, %(status)s, NOW()
        )
        """
        with get_db() as cursor:
            try:
                result = execute_query_sync(cursor, query, order_dict)
                logger.info(f"Order created with result: {result}")
                # Get the last inserted ID
                cursor.execute("SELECT LAST_INSERT_ID()")
                order_id = cursor.fetchone()['LAST_INSERT_ID()']
                return order_id
            except Exception as e:
                logger.error(f"Failed to create order: {str(e)}")
                logger.error(f"Query parameters: {order_dict}")
                raise

    async def get_all_orders(self):
        with get_db() as cursor:
            return await self.repository.get_orders(cursor)

    @staticmethod
    async def get_order(order_id: int) -> Dict[str, Any]:
        """Get order by ID"""
        query = "SELECT * FROM orders WHERE id = %s"
        with get_db() as cursor:
            result = execute_query_sync(cursor, query, (order_id,))
            return result[0] if result else None 