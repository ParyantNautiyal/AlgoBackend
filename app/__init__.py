# Empty init file 
from dotenv import load_dotenv
import os
from pathlib import Path
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
import logging  
logger = logging.getLogger(__name__)
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
        print(f"Error connecting to MySQL: {e}")
        raise
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
        
    create_kite_table = """
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                trading_symbol VARCHAR(255),
                order_type VARCHAR(255),
                quantity INT,
                trigger_price FLOAT,
                order_limit FLOAT,
                variety VARCHAR(255),
                validity VARCHAR(255),
                product VARCHAR(255),
                status VARCHAR(255),
                created_at DATETIME
            )
        """
    cursor.execute(create_kite_table.strip())
    conn.commit()
        
        # Create instruments table
    create_instruments_table = """
            CREATE TABLE IF NOT EXISTS instruments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                instrument_token INT NOT NULL,
                exchange_token INT NOT NULL,
                tradingsymbol VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                last_price FLOAT,
                expiry DATETIME,
                strike FLOAT,
                tick_size FLOAT,
                lot_size INT,
                instrument_type VARCHAR(50),
                segment VARCHAR(50),
                exchange VARCHAR(50),
                UNIQUE KEY unique_symbol (tradingsymbol)
            )
        """
    cursor.execute(create_instruments_table.strip())
    conn.commit()

    logger.info("Database initialized")
        
except Error as e:
    logger.error(f"Error initializing database: {e}")
    raise
finally:
    cursor.close()
    conn.close()