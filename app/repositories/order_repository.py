from typing import List, Optional
from ..database import get_db, execute_query_sync

class OrderRepository:
    @staticmethod
    async def create_order(cursor, order_data: dict) -> int:
        query = """
        INSERT INTO orders (symbol, order_type, quantity, price, status)
        VALUES (%(symbol)s, %(order_type)s, %(quantity)s, %(price)s, %(status)s)
        """
        return execute_query_sync(cursor, query, order_data)

    @staticmethod
    async def get_orders(cursor) -> List[dict]:
        query = "SELECT * FROM orders ORDER BY created_at DESC"
        return execute_query_sync(cursor, query)

    @staticmethod
    async def get_order_by_id(cursor, order_id: int) -> Optional[dict]:
        query = "SELECT * FROM orders WHERE id = %s"
        result = execute_query_sync(cursor, query, (order_id,))
        return result[0] if result else None 