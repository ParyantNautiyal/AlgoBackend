import logging
import time
from datetime import datetime
from statistics import mean, median
from collections import defaultdict
import random
import pandas as pd
from tradetest import OrderManager

logger = logging.getLogger(__name__)

def run_performance_test():
    """Run performance tests for OrderManager"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Performance metrics
    metrics = defaultdict(list)

    # Initialize OrderManager
    manager = OrderManager(
        api_key="009u7xstbslxsuxd",
        access_token="WRAcir4tnLS051CZ6PhCrfwnCrxa2kA8"
    )

    try:
        manager.start()

        # Simulate market opening rush (multiple orders in quick succession)
        logger.info("Simulating market opening rush...")
        opening_orders = [
            
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
            }
        ]

        # Process opening rush orders with minimal delay
        for order in opening_orders:
            start_time = time.perf_counter()
            manager.add_order(order)
            end_time = time.perf_counter()
            processing_time = (end_time - start_time) * 1000
            
            metrics['order_placement_time'].append({
                'order_id': order['order_id'],
                'trading_symbol': order['trading_symbol'],
                'order_type': order['order_type'],
                'processing_time_ms': processing_time,
                'time_of_day': 'market_opening'
            })
            
            time.sleep(0.5)  # 500ms delay between orders during rush

        # Simulate mid-day trading (more spread out orders)
        logger.info("Simulating mid-day trading...")
        mid_day_orders = [
            # {
            #     'order_id': 4,
            #     'trading_symbol': 'TCS',
            #     'quantity': 25,
            #     'order_type': 'LIMIT',
            #     'limit_price': 3450.00,
            #     'trigger_price': None,
            #     'variety': 'REGULAR',
            #     'product': 'CNC',
            #     'validity': 'DAY',
            #     'operation': 'BUY',
            #     'execution_limit': 1
            # },
            # {
            #     'order_id': 5,
            #     'trading_symbol': 'SBIN',
            #     'quantity': 200,
            #     'order_type': 'SL',
            #     'limit_price': 595.00,
            #     'trigger_price': 590.00,
            #     'variety': 'REGULAR',
            #     'product': 'MIS',
            #     'validity': 'DAY',
            #     'operation': 'SELL',
            #     'execution_limit': 1
            # }
        ]

        # Process mid-day orders with longer delays
        for order in mid_day_orders:
            start_time = time.perf_counter()
            manager.add_order(order)
            end_time = time.perf_counter()
            processing_time = (end_time - start_time) * 1000
            
            metrics['order_placement_time'].append({
                'order_id': order['order_id'],
                'trading_symbol': order['trading_symbol'],
                'order_type': order['order_type'],
                'processing_time_ms': processing_time,
                'time_of_day': 'mid_day'
            })
            
            # Random delay between 2-5 seconds during mid-day
            time.sleep(random.uniform(2, 5))

        # Simulate order modifications
        logger.info("Testing order modifications...")
        modifications = [
            # {
            #     'order_id': 1,
            #     'modifications': {
            #         'quantity': 150,
            #         'order_type': 'LIMIT',
            #         'limit_price': 2490.00
            #     }
            # },
            # {
            #     'order_id': 4,
            #     'modifications': {
            #         'quantity': 30,
            #         'limit_price': 3445.00
            #     }
            # }
        ]

        for mod in modifications:
            start_time = time.perf_counter()
            manager.modify_order(mod['order_id'], mod['modifications'])
            end_time = time.perf_counter()
            modification_time = (end_time - start_time) * 1000
            
            metrics['order_modification_time'].append({
                'order_id': mod['order_id'],
                'processing_time_ms': modification_time
            })
            
            time.sleep(random.uniform(1, 3))

        # Simulate market closing rush (square-off orders)
        logger.info("Simulating market closing rush...")
        closing_orders = [
            # {
            #     'order_id': 6,
            #     'trading_symbol': 'RELIANCE',
            #     'quantity': 100,
            #     'order_type': 'MARKET',
            #     'limit_price': None,
            #     'trigger_price': None,
            #     'variety': 'REGULAR',
            #     'product': 'MIS',
            #     'validity': 'DAY',
            #     'operation': 'SELL',  # Square off position
            #     'execution_limit': 1
            # },
            # {
            #     'order_id': 7,
            #     'trading_symbol': 'SBIN',
            #     'quantity': 200,
            #     'order_type': 'MARKET',
            #     'limit_price': None,
            #     'trigger_price': None,
            #     'variety': 'REGULAR',
            #     'product': 'MIS',
            #     'validity': 'DAY',
            #     'operation': 'BUY',  # Square off position
            #     'execution_limit': 1
            # }
        ]

        # Process closing rush orders
        for order in closing_orders:
            start_time = time.perf_counter()
            manager.add_order(order)
            end_time = time.perf_counter()
            processing_time = (end_time - start_time) * 1000
            
            metrics['order_placement_time'].append({
                'order_id': order['order_id'],
                'trading_symbol': order['trading_symbol'],
                'order_type': order['order_type'],
                'processing_time_ms': processing_time,
                'time_of_day': 'market_closing'
            })
            
            time.sleep(0.75)  # 750ms delay during closing rush

        # Generate performance report
        generate_performance_report(metrics, manager)

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)
    finally:
        manager.stop()
        logger.info("Test completed")

def generate_performance_report(metrics, manager):
    """Generate detailed performance report"""
    logger.info("\n=== Performance Report ===\n")

    # Order Placement Analysis by time of day
    placement_df = pd.DataFrame(metrics['order_placement_time'])
    
    logger.info("Order Placement Performance by Time of Day:")
    time_stats = placement_df.groupby('time_of_day')['processing_time_ms'].agg([
        'count', 'mean', 'median', 'min', 'max'
    ])
    logger.info(f"\n{time_stats}")
    
    # Overall Order Placement Analysis
    placement_times = placement_df['processing_time_ms'].tolist()
    
    logger.info("\nOverall Order Placement Performance:")
    logger.info(f"Total orders processed: {len(placement_times)}")
    logger.info(f"Average processing time: {mean(placement_times):.2f}ms")
    logger.info(f"Median processing time: {median(placement_times):.2f}ms")
    logger.info(f"Min processing time: {min(placement_times):.2f}ms")
    logger.info(f"Max processing time: {max(placement_times):.2f}ms")
    
    # Performance by order type
    logger.info("\nProcessing Time by Order Type:")
    type_stats = placement_df.groupby('order_type')['processing_time_ms'].agg(['mean', 'count'])
    logger.info(f"\n{type_stats}")

    # Modification Performance
    if metrics['order_modification_time']:
        mod_times = [m['processing_time_ms'] for m in metrics['order_modification_time']]
        logger.info("\nOrder Modification Performance:")
        logger.info(f"Total modifications: {len(mod_times)}")
        logger.info(f"Average modification time: {mean(mod_times):.2f}ms")
        logger.info(f"Median modification time: {median(mod_times):.2f}ms")

    # Cache Performance
    logger.info("\nCache Performance:")
    logger.info(f"Instrument cache size: {len(manager.instrument_cache)}")
    logger.info(f"Tick cache size: {len(manager.tick_cache)}")
    logger.info(f"Order cache size: {len(manager.order_cache)}")
    
    # Generate timestamp for report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"performance_report_{timestamp}.csv"
    
    # Save detailed metrics to CSV
    placement_df.to_csv(report_file, index=False)
    logger.info(f"\nDetailed metrics saved to {report_file}")

if __name__ == "__main__":
    run_performance_test() 