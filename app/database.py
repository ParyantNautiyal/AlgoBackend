from dotenv import load_dotenv
import os
from pathlib import Path
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
import logging



logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=f"{BASE_DIR}/.env")

MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DB = os.getenv('MYSQL_DB')
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306

def get_connection():
    """Create a new database connection"""
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            port=MYSQL_PORT
        )
        return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        raise

class DatabaseConnection:
    def __init__(self):
        logger.debug("Initializing DatabaseConnection")
        self.conn = get_connection()
        self.cursor = self.conn.cursor(dictionary=True)
        logger.debug("DatabaseConnection initialized successfully")

    def __enter__(self):
        logger.debug("Entering DatabaseConnection context")
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                logger.debug("No exceptions, committing transaction")
                self.conn.commit()
            else:
                logger.warning(f"Exception occurred, rolling back: {exc_type.__name__}: {exc_val}")
                self.conn.rollback()
        finally:
            logger.debug("Closing cursor and connection")
            self.cursor.close()
            self.conn.close()
            logger.debug("DatabaseConnection cleanup complete")

def get_db():
    """Database connection context manager"""
    return DatabaseConnection()

def execute_query_sync(cursor, query, params=None):
    """Execute a query and return results (synchronous version)"""
    try:
        cursor.execute(query, params or ())
        if query.strip().upper().startswith('SELECT'):
            return cursor.fetchall()
        return cursor.rowcount
    except Error as e:
        logger.error(f"Query execution error: {e}")
        logger.error(f"Query: {query}")
        logger.error(f"Parameters: {params}")
        raise

def init_db():
    """Initialize database tables"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create kite_data table
        create_kite_table = """
            CREATE TABLE IF NOT EXISTS kite_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(255),
                price FLOAT,
                timestamp DATETIME
            )
        """
        cursor.execute(create_kite_table.strip())
        conn.commit()
        
        # Create orders table with correct column names
        create_orders_table = """
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                trading_symbol VARCHAR(255),
                order_type VARCHAR(255),
                quantity INT,
                price FLOAT,
                trigger_price FLOAT,
                order_limit FLOAT,
                variety VARCHAR(255),
                validity VARCHAR(255),
                product VARCHAR(255),
                status VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        cursor.execute(create_orders_table.strip())
        conn.commit()
        
        # Create instruments table
        create_instruments_table = """
            CREATE TABLE if not exists instruments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                instrument_token INT NOT NULL,
                exchange_token INT NOT NULL,
                tradingsymbol VARCHAR(255) NOT NULL,
                name VARCHAR(255) NULL,
                last_price FLOAT,
                expiry DATETIME NULL,
                strike FLOAT,
                tick_size FLOAT,
                lot_size INT,
                instrument_type VARCHAR(50),
                segment VARCHAR(50),
                exchange VARCHAR(50)
            )
        """
        cursor.execute(create_instruments_table.strip())
        conn.commit()

        # Check for existing data
        result = execute_query_sync(cursor, "SELECT * FROM instruments")
        if not result:
            logger.info("No data found in instruments table")
            instruments = kite.instruments()
            logger.info(f"Fetched {len(instruments)} instruments from Kite")
            
            # Format data for MySQL
            values = []
            for instrument in instruments:
                # Handle expiry date
                expiry = instrument.get('expiry')
                if expiry == '' or expiry is None:
                    expiry = None
                
                values.append((
                    instrument['instrument_token'],
                    instrument['exchange_token'],
                    instrument['tradingsymbol'],
                    instrument.get('name', ''),
                    instrument.get('last_price', 0.0),
                    expiry,  # Can be None
                    instrument.get('strike', 0.0),
                    instrument.get('tick_size', 0.0),
                    instrument.get('lot_size', 0),
                    instrument.get('instrument_type', ''),
                    instrument.get('segment', ''),
                    instrument.get('exchange', '')
                ))
            
            insert_query = """
                INSERT INTO instruments (
                    instrument_token, exchange_token, tradingsymbol,
                    name, last_price, expiry, strike, tick_size, 
                    lot_size, instrument_type, segment, exchange
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            logger.info(f"Inserting {len(values)} instruments into database")
            cursor.executemany(insert_query, values)
            conn.commit()
            logger.info("Instruments inserted successfully")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    from kiteconnect import KiteConnect
    kite = KiteConnect(api_key="009u7xstbslxsuxd")
    logger.info("Starting database initialization")
    init_db()
    logger.info("Database initialization completed")

    # Use synchronous version for direct script execution   
    conn = get_connection()
    cursor = conn.cursor()
    try:
        result = execute_query_sync(cursor, "SELECT * FROM instruments")
        logger.info(f"Query result: {result}")
        if not result:
            logger.info("No data found in instruments table")
            instruments = kite.instruments()
            logger.info(f"Fetched {len(instruments)} instruments from Kite")
            
            # Format data for MySQL
            values = []
            for instrument in instruments:
                values.append((
                    instrument['instrument_token'],
                    instrument['exchange_token'],
                    instrument['tradingsymbol'],
                    instrument.get('name', None),
                    instrument.get('last_price', 0.0),
                    instrument.get('expiry', None),
                    instrument.get('strike', 0.0),
                    instrument.get('tick_size', 0.0),
                    instrument.get('lot_size', 0),
                    instrument.get('instrument_type', None),
                    instrument.get('segment', None),
                    instrument.get('exchange', None)
                ))
            
            
        insert_query = """
                INSERT INTO instruments (
                    instrument_token, exchange_token, tradingsymbol, 
                    name, last_price, expiry, strike, tick_size, 
                    lot_size, instrument_type, segment, exchange
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
        logger.info(f"Inserting {len(values)} instruments into database")
        cursor.executemany(insert_query, values)
        conn.commit()
        logger.info("Instruments inserted successfully")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

