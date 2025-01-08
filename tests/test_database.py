import pytest
import logging
from app.database import get_db, execute_query_sync

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_database_connection():
    """Test database connection and basic query"""
    logger.info("Starting database connection test")
    with get_db() as cursor:
        try:
            query = "SELECT 1 as test"
            logger.info(f"Executing query: {query}")
            result = execute_query_sync(cursor, query)
            logger.info(f"Raw query result: {result}")
            
            assert result is not None, "Query result is None"
            assert len(result) > 0, f"Query returned empty result: {result}"
            assert result[0]['test'] == 1, f"Expected test=1, got {result}"
            logger.info("Database connection successful")
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

@pytest.mark.asyncio
async def test_execute_query():
    """Test execute_query function"""
    logger.info("Starting execute_query test")
    with get_db() as cursor:
        try:
            # Test SELECT
            query = "SELECT 1 as test"
            logger.info(f"Executing query: {query}")
            result = execute_query_sync(cursor, query)
            logger.info(f"Query result: {result}")
            
            assert len(result) == 1, f"Expected 1 row, got {len(result)} rows"
            assert 'test' in result[0], f"Column 'test' not found in result: {result[0]}"
            assert result[0]['test'] == 1, f"Expected test=1, got {result[0]['test']}"
            logger.info("SELECT query successful")

            # Test CREATE and DROP
            create_query = """
                CREATE TABLE IF NOT EXISTS test_table (
                    id INT PRIMARY KEY,
                    name VARCHAR(50)
                )
            """
            execute_query_sync(cursor, create_query)
            logger.info("CREATE TABLE successful")
            
            execute_query_sync(cursor, "DROP TABLE test_table")
            logger.info("DROP TABLE successful")
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise 