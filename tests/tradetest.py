import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
import time
from multiprocessing import Process, Pool, Manager, Queue, Event, cpu_count
from collections import defaultdict
from functools import lru_cache
from cachetools import TTLCache, LRUCache
from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
from app.database import DatabaseConnection

logger = logging.getLogger(__name__)

class OrderManager:
    def __init__(self, api_key, access_token, instruments=None):
        # Set up logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing OrderManager...")

        try:
            self.logger.debug(f"Connecting to Kite with API key: {api_key[:4]}...")
            self.kite = KiteConnect(api_key=api_key)
            self.kite.set_access_token(access_token)
            self.logger.info("KiteConnect initialized successfully")
            
            # Initialize KiteTicker
            self.logger.debug("Initializing KiteTicker...")
            self.ticker = KiteTicker(api_key, access_token)
            self.setup_ticker_callbacks()
            self.logger.info("KiteTicker initialized successfully")
            
            # Cache configurations
            self.logger.debug("Setting up caches...")
            self.instrument_cache = TTLCache(maxsize=1000, ttl=24*60*60)  # 24 hour TTL
            self.tick_cache = TTLCache(maxsize=5000, ttl=300)  # 5 minute TTL
            self.order_cache = LRUCache(maxsize=10000)  # LRU cache for orders
            self.logger.info("Caches initialized with TTL and LRU configurations")
            
            # Shared data structures using Manager
            self.logger.debug("Initializing shared data structures...")
            self.manager = Manager()
            self.orders = self.manager.dict()
            self.tick_data = self.manager.dict()
            self.orders_by_instrument = self.manager.dict()
            self.logger.info("Shared data structures initialized")
            
            # Initialize caches
            self.logger.debug("Loading initial cache data...")
            self._init_caches()
            self.logger.info("Cache initialization completed")
            
            # Queues
            self.logger.debug("Setting up message queues...")
            self.order_queue = Queue()
            self.db_queue = Queue()
            self.tick_queue = Queue()
            self.logger.info("Message queues initialized")
            
            # Track subscribed instruments
            self.logger.debug("Initializing instrument tracking...")
            self.subscribed_instruments = self.manager.list()
            if instruments:
                self.logger.info(f"Subscribing to initial instruments: {instruments}")
                self.subscribe_instruments(instruments)
            
            # Control flags
            self.logger.debug("Setting up control flags...")
            self.is_running = Event()
            self.is_running.set()
            self.connection_ready = Event()
            self.logger.info("Control flags initialized")
            
            # Initialize processes list
            self.processes = []
            self.logger.info("OrderManager initialization completed successfully")

        except Exception as e:
            self.logger.error(f"Error during OrderManager initialization: {e}", exc_info=True)
            raise

    def setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Generate log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"trading_{timestamp}.log")

        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                # Rotate file logs (10MB max size, keep 5 backup files)
                RotatingFileHandler(
                    log_file,
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5
                ),
                logging.StreamHandler()  # Also log to console
            ]
        )

        # Add performance logging
        perf_log = os.path.join(log_dir, f"performance_{timestamp}.log")
        perf_handler = RotatingFileHandler(
            perf_log,
            maxBytes=10*1024*1024,
            backupCount=3
        )
        perf_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        # Create performance logger
        perf_logger = logging.getLogger('performance')
        perf_logger.addHandler(perf_handler)
        perf_logger.setLevel(logging.INFO)

    def log_performance(self, operation: str, start_time: float, **kwargs):
        """Log performance metrics"""
        end_time = time.perf_counter()
        duration = (end_time - start_time) * 1000  # Convert to milliseconds
        
        perf_logger = logging.getLogger('performance')
        perf_logger.info(
            f"Operation: {operation}, "
            f"Duration: {duration:.2f}ms, "
            f"Details: {kwargs}"
        )

    def log_memory_usage(self):
        """Log current memory usage of caches"""
        self.logger.info(
            f"Memory Usage - "
            f"Instrument Cache: {len(self.instrument_cache)} items, "
            f"Tick Cache: {len(self.tick_cache)} items, "
            f"Order Cache: {len(self.order_cache)} items"
        )

    def log_queue_status(self):
        """Log current queue sizes"""
        self.logger.info(
            f"Queue Status - "
            f"Order Queue: {self.order_queue.qsize()} items, "
            f"DB Queue: {self.db_queue.qsize()} items, "
            f"Tick Queue: {self.tick_queue.qsize()} items"
        )

    def _init_caches(self):
        """Initialize caches with data from database"""
        try:
            with DatabaseConnection() as cursor:
                # Cache active orders
                cursor.execute("""
                    SELECT * FROM pending_orders 
                    WHERE status IN ('PENDING', 'PARTIALLY_EXECUTED')
                """)
                for order in cursor.fetchall():
                    self.order_cache[order['order_id']] = order
                
                # Cache instrument tokens
                cursor.execute("SELECT trading_symbol, instrument_token FROM instruments")
                for row in cursor.fetchall():
                    self.instrument_cache[row['trading_symbol']] = row['instrument_token']
                    
        except Exception as e:
            logger.error(f"Error initializing caches: {e}", exc_info=True)

    @lru_cache(maxsize=1000)
    def _get_instrument_token(self, trading_symbol):
        """Get instrument token with caching"""
        try:
            # Check local cache first
            if trading_symbol in self.instrument_cache:
                return self.instrument_cache[trading_symbol]
            
            # If not in cache, fetch from Kite
            token = self.kite.ltp([trading_symbol])[trading_symbol]['instrument_token']
            self.instrument_cache[trading_symbol] = token
            return token
            
        except Exception as e:
            logger.error(f"Error getting instrument token: {e}", exc_info=True)
            raise

    def _cache_tick_data(self, tick):
        """Cache tick data with TTL"""
        instrument_token = tick['instrument_token']
        self.tick_cache[instrument_token] = {
            'last_price': tick['last_price'],
            'timestamp': time.time()
        }

    def _get_cached_tick(self, instrument_token):
        """Get cached tick data if available"""
        return self.tick_cache.get(instrument_token)

    def setup_ticker_callbacks(self):
        """Setup callbacks for KiteTicker"""
        self.ticker.on_ticks = self.on_ticks
        self.ticker.on_connect = self.on_connect
        self.ticker.on_close = self.on_close
        self.ticker.on_error = self.on_error
        self.ticker.on_reconnect = self.on_reconnect
        self.ticker.on_noreconnect = self.on_noreconnect
        self.ticker.on_order_update = self.on_order_update

    def on_ticks(self, ws, ticks):
        """Callback when ticks are received"""
        try:
            for tick in ticks:
                self.tick_queue.put(tick)
                logger.debug(f"Tick received for {tick['instrument_token']}: {tick['last_price']}")
        except Exception as e:
            logger.error(f"Error processing ticks: {e}", exc_info=True)

    def on_connect(self, ws, response):
        """Callback on successful connection"""
        logger.info("Successfully connected to WebSocket")
        self.connection_ready.set()
        
        # Resubscribe to instruments
        if self.subscribed_instruments:
            self.ticker.subscribe(list(self.subscribed_instruments))
            self.ticker.set_mode(KiteTicker.MODE_FULL, list(self.subscribed_instruments))
            logger.info(f"Resubscribed to {len(self.subscribed_instruments)} instruments")

    def on_close(self, ws, code, reason):
        """Callback when connection is closed"""
        logger.warning(f"WebSocket connection closed: {code} - {reason}")
        self.connection_ready.clear()

    def on_error(self, ws, code, reason):
        """Callback when an error occurs"""
        logger.error(f"WebSocket error: {code} - {reason}")

    def on_reconnect(self, ws, attempts_count):
        """Callback when reconnecting"""
        logger.info(f"Reconnecting to WebSocket... Attempt {attempts_count}")

    def on_noreconnect(self, ws):
        """Callback when reconnection fails"""
        logger.error("Maximum reconnection attempts reached")
        self.stop()  # Consider implementing a restart mechanism here

    def on_order_update(self, ws, data):
        """Callback for order updates from Kite"""
        try:
            order_id = data.get('order_id')
            if order_id in self.orders:
                logger.info(f"Order update received: {data}")
                
                # Queue the order update for database
                self.db_queue.put((self._db_update_order_status, (order_id, data)))
                
                # Update order status in memory
                if data.get('status') in ['COMPLETE', 'REJECTED', 'CANCELLED']:
                    self._complete_order(order_id, data.get('status'))
                
        except Exception as e:
            logger.error(f"Error processing order update: {e}", exc_info=True)

    def subscribe_instruments(self, instruments):
        """Subscribe to a list of instruments"""
        try:
            if not self.connection_ready.is_set():
                logger.warning("WebSocket not connected. Will subscribe when connection is ready.")
                return

            new_instruments = [inst for inst in instruments 
                             if inst not in self.subscribed_instruments]
            
            if new_instruments:
                logger.info(f"Subscribing to instruments: {new_instruments}")
                self.ticker.subscribe(new_instruments)
                self.subscribed_instruments.extend(new_instruments)
                
                # Initialize tick data for new instruments
                for inst in new_instruments:
                    self.tick_data[inst] = {'last_price': None}
                    
        except Exception as e:
            logger.error(f"Error subscribing to instruments: {e}", exc_info=True)
            raise

    def start(self):
        """Initialize and start all components"""
        logger.info("Starting OrderManager")
        
        # Start the ticker
        self.ticker.connect(threaded=True)
        
        # Wait for connection to be ready
        if not self.connection_ready.wait(timeout=10):
            raise ConnectionError("Failed to connect to WebSocket")
        
        # Start worker processes
        self.processes.extend([
            Process(target=self._handle_incoming_orders, name="OrderHandler"),
            Process(target=self._cleanup_caches, name="CacheManager"),
            *[Process(target=self._db_worker, name=f"DBWorker-{i}") 
              for i in range(2)],
            *[Process(target=self._tick_worker, name=f"TickWorker-{i}") 
              for i in range(cpu_count() - 1)]
        ])
        
        # Start all processes
        for process in self.processes:
            process.daemon = True
            process.start()

    def stop(self):
        """Gracefully stop all components"""
        logger.info("Stopping OrderManager")
        self.is_running.clear()
        
        # Close WebSocket connection
        if self.ticker:
            self.ticker.close()
        
        # Stop all processes
        for process in self.processes:
            process.join(timeout=5)
            if process.is_alive():
                process.terminate()

    def _db_update_order_status(self, cursor, order_id, data):
        """Update order status in database"""
        cursor.execute("""
            UPDATE pending_orders 
            SET status = %s,
                last_modified = NOW(),
                exchange_order_id = %s,
                exchange_update_timestamp = %s
            WHERE order_id = %s
        """, (
            data.get('status'),
            data.get('exchange_order_id'),
            data.get('exchange_timestamp'),
            order_id
        ))

    def _db_worker(self):
        """Dedicated process for database operations"""
        logger.info(f"Starting DB worker process {Process.current_process().name}")
        while self.is_running.is_set():
            try:
                operation, args = self.db_queue.get(timeout=1)
                with DatabaseConnection() as cursor:
                    operation(cursor, *args)
            except Queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Database error: {e}", exc_info=True)

    def _tick_worker(self):
        """Dedicated process for processing tick data"""
        logger.info(f"Starting tick worker process {Process.current_process().name}")
        while self.is_running.is_set():
            try:
                tick = self.tick_queue.get(timeout=1)
                self._process_tick_data(tick)
            except Queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Tick processing error: {e}", exc_info=True)

    def _process_tick_data(self, tick):
        """Process tick data with caching"""
        try:
            instrument_token = tick['instrument_token']
            
            # Cache the tick data
            self._cache_tick_data(tick)
            
            # Update shared tick data
            self.tick_data[instrument_token] = {'last_price': tick['last_price']}
            
            # Get orders for this instrument from cache
            order_ids = self.orders_by_instrument.get(instrument_token, [])
            
            # Process each order
            for order_id in order_ids[:]:
                order = self.order_cache.get(order_id)
                if order and not order.get('triggered', False):
                    self._check_and_execute_order(order_id, order, tick)

        except Exception as e:
            logger.error(f"Error processing tick: {e}", exc_info=True)

    def _handle_incoming_orders(self):
        """Process incoming orders from the queue"""
        logger.info(f"Starting order handler process {Process.current_process().name}")
        while self.is_running.is_set():
            try:
                order = self.order_queue.get(timeout=1)
                order_id = order['order_id']
                instrument_token = order['instrument_token']
                
                # Store order
                self.orders[order_id] = order
                
                # Update orders by instrument mapping
                current_orders = self.orders_by_instrument.get(instrument_token, [])
                current_orders.append(order_id)
                self.orders_by_instrument[instrument_token] = current_orders

            except Queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error handling order: {e}", exc_info=True)

    def _db_insert_order(self, cursor, order_details):
        cursor.execute("""
            INSERT INTO pending_orders 
            (order_id, trading_symbol, instrument_token, quantity, order_type, 
             limit_price, trigger_price, variety, product, 
             validity, operation, execution_limit, executions_done, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'PENDING')
        """, (
            order_details['order_id'],
            order_details['trading_symbol'],
            order_details['instrument_token'],
            order_details['quantity'],
            order_details['order_type'],
            order_details.get('limit_price'),
            order_details.get('trigger_price'),
            order_details['variety'],
            order_details['product'],
            order_details['validity'],
            order_details['operation'],
            order_details['execution_limit'],
            order_details['executions_done']
        ))

    def add_order(self, order_details):
        """Add new order with caching"""
        try:
            # Get instrument token from cache
            instrument_token = self._get_instrument_token(order_details['trading_symbol'])
            order_details['instrument_token'] = instrument_token
            
            # Add to order cache
            self.order_cache[order_details['order_id']] = order_details
            
            # Queue DB operation
            self.db_queue.put((self._db_insert_order, (order_details,)))
            
            # Add to processing queue
            self.order_queue.put(order_details)
            
            # Subscribe if needed
            if instrument_token not in self.subscribed_instruments:
                self.subscribe_instruments([instrument_token])
                
        except Exception as e:
            logger.error(f"Error adding order: {e}", exc_info=True)
            raise

    def _check_and_execute_order(self, order_id, order, tick):
        """Check if order should be executed and process it"""
        try:
            # Check if order has reached its execution limit
            if order['executions_done'] >= order['execution_limit']:
                logger.info(f"Order {order_id} has reached its execution limit")
                self._complete_order(order_id, 'COMPLETED')
                return

            current_price = tick['last_price']
            should_execute = False

            # Check execution conditions based on order type
            if order['order_type'] == 'MARKET':
                should_execute = True
            elif order['order_type'] == 'LIMIT':
                should_execute = (
                    (order['operation'] == 'BUY' and current_price <= order['limit_price']) or
                    (order['operation'] == 'SELL' and current_price >= order['limit_price'])
                )
            elif order['order_type'] in ['SL', 'SL-M']:
                if order['operation'] == 'BUY':
                    should_execute = current_price >= order['trigger_price']
                else:  # SELL
                    should_execute = current_price <= order['trigger_price']

            if should_execute:
                logger.info(f"Executing order @ {datetime.now()} {order_id} at price {current_price} for tick @ {tick['last_traded_time'] }")
                
                # Place order with Kite
                self.kite.place_order(
                    variety=order['variety'],
                    exchange=self.kite.EXCHANGE_NSE,
                    tradingsymbol=order['trading_symbol'],
                    transaction_type=order['operation'],
                    quantity=order['quantity'],
                    product=order['product'],
                    order_type=order['order_type'],
                    validity=order['validity']
                )

                # Update execution count and database
                order['executions_done'] += 1
                with DatabaseConnection() as cursor:
                    cursor.execute("""
                        INSERT INTO order_executions 
                        (order_id, execution_price, execution_time)
                        VALUES (%s, %s, NOW())
                    """, (order_id, current_price))
                    
                    cursor.execute("""
                        UPDATE pending_orders 
                        SET executions_done = executions_done + 1,
                            last_execution_price = %s,
                            last_execution_time = NOW(),
                            status = CASE 
                                WHEN executions_done >= execution_limit THEN 'COMPLETED'
                                ELSE 'PARTIALLY_EXECUTED'
                            END
                        WHERE order_id = %s
                    """, (current_price, order_id))

                # Check if order is complete
                if order['executions_done'] >= order['execution_limit']:
                    self._complete_order(order_id, 'COMPLETED')
                else:
                    self.orders[order_id] = order  # Update order in shared dict

        except Exception as e:
            logger.error(f"Error executing order {order_id}: {e}", exc_info=True)

    def _complete_order(self, order_id, status):
        """Mark an order as complete and clean up"""
        logger.info(f"Completing order {order_id} with status: {status}")
        try:
            with DatabaseConnection() as cursor:
                cursor.execute("""
                    UPDATE pending_orders 
                    SET status = %s,
                        completion_time = NOW()
                    WHERE order_id = %s
                """, (status, order_id))
            
            if order_id in self.orders:
                del self.orders[order_id]
                
        except Exception as e:
            logger.error(f"Error completing order {order_id}: {e}", exc_info=True)

    def modify_order(self, order_id, new_details):
        """Modify existing order"""
        logger.info(f"Modifying order {order_id}: {new_details}")
        try:
            with DatabaseConnection() as cursor:
                cursor.execute("""
                    UPDATE pending_orders SET
                    trading_symbol = %s,
                    quantity = %s,
                    order_type = %s,
                    limit_price = %s,
                    trigger_price = %s,
                    variety = %s,
                    product = %s,
                    validity = %s,
                    operation = %s,
                    last_modified = NOW()
                    WHERE order_id = %s AND status = 'PENDING'
                """, (
                    new_details['trading_symbol'],
                    new_details['quantity'],
                    new_details['order_type'],
                    new_details.get('limit_price'),
                    new_details.get('trigger_price'),
                    new_details['variety'],
                    new_details['product'],
                    new_details['validity'],
                    new_details['operation'],
                    order_id
                ))
                
                if cursor.rowcount > 0:
                    self.orders[order_id].update(new_details)
                    logger.info(f"Order {order_id} modified successfully")
                else:
                    logger.warning(f"Order {order_id} not found or already executed")
                    
        except Exception as e:
            logger.error(f"Error modifying order: {e}", exc_info=True)
            raise

    def cancel_order(self, order_id):
        """Cancel existing order"""
        logger.info(f"Cancelling order {order_id}")
        try:
            with DatabaseConnection() as cursor:
                cursor.execute("""
                    UPDATE pending_orders 
                    SET status = 'CANCELLED',
                        last_modified = NOW()
                    WHERE order_id = %s AND status = 'PENDING'
                """, (order_id,))
                
                if cursor.rowcount > 0:
                    if order_id in self.orders:
                        del self.orders[order_id]
                    logger.info(f"Order {order_id} cancelled successfully")
                else:
                    logger.warning(f"Order {order_id} not found or already executed")
                    
        except Exception as e:
            logger.error(f"Error cancelling order: {e}", exc_info=True)
            raise

    def monitor_cache_stats(self):
        """Monitor cache statistics"""
        while self.is_running.is_set():
            stats = {
                'instrument_cache_size': len(self.instrument_cache),
                'tick_cache_size': len(self.tick_cache),
                'order_cache_size': len(self.order_cache),
                'instrument_cache_hits': self._get_instrument_token.cache_info().hits,
                'instrument_cache_misses': self._get_instrument_token.cache_info().misses
            }
            logger.info(f"Cache statistics: {stats}")
            time.sleep(60)

    def _cleanup_caches(self):
        """Periodic cleanup of caches"""
        while self.is_running.is_set():
            try:
                # Clear expired entries from tick cache
                self.tick_cache.expire()
                
                # Clear expired entries from instrument cache
                self.instrument_cache.expire()
                
                # Log cache statistics
                logger.debug(f"Cache stats - Orders: {len(self.order_cache)}, "
                           f"Ticks: {len(self.tick_cache)}, "
                           f"Instruments: {len(self.instrument_cache)}")
                
            except Exception as e:
                logger.error(f"Error cleaning caches: {e}", exc_info=True)
            
            time.sleep(300)  # Run cleanup every 5 minutes

    def save_logs_to_file(self, log_type="trading"):
        """Save logs to a structured file"""
        try:
            # Create logs directory if it doesn't exist
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Generate filename with timestamp and log type
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(log_dir, f"{log_type}_log_{timestamp}.txt")
            
            with open(filename, 'w') as f:
                # Write header
                f.write("="*50 + "\n")
                f.write(f"Trading System Logs - {log_type.upper()}\n")
                f.write(f"Generated at: {datetime.now()}\n")
                f.write("="*50 + "\n\n")
                
                # Write system status
                f.write("System Status:\n")
                f.write("-"*20 + "\n")
                f.write(f"Connection Ready: {self.connection_ready.is_set()}\n")
                f.write(f"Is Running: {self.is_running.is_set()}\n")
                f.write(f"Active Processes: {len(self.processes)}\n\n")
                
                # Write cache statistics
                f.write("Cache Statistics:\n")
                f.write("-"*20 + "\n")
                f.write(f"Instrument Cache Size: {len(self.instrument_cache)}\n")
                f.write(f"Tick Cache Size: {len(self.tick_cache)}\n")
                f.write(f"Order Cache Size: {len(self.order_cache)}\n\n")
                
                # Write queue statistics
                f.write("Queue Statistics:\n")
                f.write("-"*20 + "\n")
                f.write(f"Order Queue Size: {self.order_queue.qsize()}\n")
                f.write(f"DB Queue Size: {self.db_queue.qsize()}\n")
                f.write(f"Tick Queue Size: {self.tick_queue.qsize()}\n\n")
                
                # Write subscribed instruments
                f.write("Subscribed Instruments:\n")
                f.write("-"*20 + "\n")
                f.write(f"Count: {len(self.subscribed_instruments)}\n")
                f.write("Instruments: " + ", ".join(map(str, self.subscribed_instruments)) + "\n\n")
                
                # Write active orders
                f.write("Active Orders:\n")
                f.write("-"*20 + "\n")
                for order_id, order in self.orders.items():
                    f.write(f"Order ID: {order_id}\n")
                    f.write(f"Symbol: {order.get('trading_symbol')}\n")
                    f.write(f"Type: {order.get('order_type')}\n")
                    f.write(f"Status: {order.get('status')}\n")
                    f.write("-"*15 + "\n")
                
                # Write performance metrics if available
                if log_type == "performance":
                    f.write("\nPerformance Metrics:\n")
                    f.write("-"*20 + "\n")
                    # Get the performance logger and its handlers
                    perf_logger = logging.getLogger('performance')
                    for handler in perf_logger.handlers:
                        if isinstance(handler, RotatingFileHandler):
                            # Read and write performance logs
                            if os.path.exists(handler.baseFilename):
                                with open(handler.baseFilename, 'r') as perf_file:
                                    f.write(perf_file.read())
                
            self.logger.info(f"Logs saved to: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Error saving logs to file: {e}", exc_info=True)
            return None

    def save_error_logs(self):
        """Save error logs specifically"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_log_file = os.path.join("logs", f"error_log_{timestamp}.txt")
            
            with open(error_log_file, 'w') as f:
                f.write("="*50 + "\n")
                f.write("Trading System Error Logs\n")
                f.write(f"Generated at: {datetime.now()}\n")
                f.write("="*50 + "\n\n")
                
                # Get all loggers and their handlers
                for logger_name in logging.root.manager.loggerDict:
                    logger = logging.getLogger(logger_name)
                    for handler in logger.handlers:
                        if isinstance(handler, RotatingFileHandler):
                            # Read log file and filter for errors
                            if os.path.exists(handler.baseFilename):
                                with open(handler.baseFilename, 'r') as log_file:
                                    for line in log_file:
                                        if "ERROR" in line or "CRITICAL" in line:
                                            f.write(line)
                
            self.logger.info(f"Error logs saved to: {error_log_file}")
            return error_log_file
            
        except Exception as e:
            self.logger.error(f"Error saving error logs: {e}", exc_info=True)
            return None

    def cleanup_old_logs(self, days_to_keep=7):
        """Clean up old log files"""
        try:
            log_dir = "logs"
            current_time = datetime.now()
            
            for filename in os.listdir(log_dir):
                filepath = os.path.join(log_dir, filename)
                file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
                if (current_time - file_modified).days > days_to_keep:
                    os.remove(filepath)
                    self.logger.info(f"Removed old log file: {filename}")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up old logs: {e}", exc_info=True)

def test_order_manager():
    """Test function for the OrderManager"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize with test credentials
    manager = OrderManager(
        api_key="your_test_api_key",
        access_token="your_test_access_token"
    )

    try:
        manager.start()

        # Test orders with comprehensive parameters
        test_orders = [
            {
                'order_id': 1,
                'trading_symbol': 'EDELWEISS',
                'quantity': 1,
                'order_type': 'MARKET',
                'limit_price': 1,
                'trigger_price': 126.96,
                'variety': 'REGULAR',
                'product': 'CNC',
                'validity': 'DAY',
                'operation': 'BUY',
                'execution_limit': 1
            # },
            # {
            #     'order_id': 2,
            #     'trading_symbol': 'INFY',
            #     'quantity': 50,
            #     'order_type': 'SL',
            #     'limit_price': 1600.00,
            #     'trigger_price': 1590.00,
            #     'variety': 'AMO',
            #     'product': 'MIS',
            #     'validity': 'DAY',
            #     'operation': 'SELL',
            #     'execution_limit': 2
            # },
            # {
            #     'order_id': 3,
            #     'trading_symbol': 'HDFCBANK',
            #     'quantity': 75,
            #     'order_type': 'SL-M',
            #     'limit_price': None,
            #     'trigger_price': 1650.00,
            #     'variety': 'REGULAR',
            #     'product': 'NRML',
            #     'validity': 'IOC',
            #     'operation': 'BUY',
            #     'execution_limit': 1
            # }
            }
        ]

        # Add test orders with delay between each
        for order in test_orders:
            logger.info(f"Adding test order: {order['order_id']}")
            manager.add_order(order)
            time.sleep(2)  # Wait 2 seconds between orders

        # Test order modification
        modification = {
            'trading_symbol': 'EDELWEISS',
            'quantity': 1,
            'order_type': 'MARKET',
            'limit_price': 1,
            'trigger_price': 126.95,
            'variety': 'REGULAR',
            'product': 'CNC',
            'validity': 'DAY',
            'operation': 'BUY'
        }
        manager.modify_order(1, modification)
        time.sleep(2)

        # Test order cancellation
        manager.cancel_order(2)
        time.sleep(2)

        # Let the system run for a while to process orders
        logger.info("Waiting for order processing...")
        time.sleep(30)

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
    finally:
        manager.stop()
        logger.info("Test completed")

if __name__ == "__main__":
    test_order_manager()
