import logging
import time
from tests.tradetest import OrderManager
from enum import Enum

logger = logging.getLogger(__name__)

class OrderValidity(Enum):
    DAY = "DAY"
    IOC = "IOC"  # Immediate or Cancel
    GTC = "GTC"  # Good Till Cancelled

class OrderVariety(Enum):
    REGULAR = "REGULAR"
    AMO = "AMO"      # After Market Order
    CO = "CO"        # Cover Order
    OCO = "OCO"      # One Cancels Other

class ProductType(Enum):
    CNC = "CNC"      # Cash and Carry
    NRML = "NRML"    # Normal
    MIS = "MIS"      # Margin Intraday Square-off
    BO = "BO"        # Bracket Order

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"        # Stop Loss
    SL_M = "SL-M"    # Stop Loss Market

def get_order_details():
    """Get comprehensive order details from user input"""
    try:
        order = {
            'order_id': int(input("Enter order ID: ")),
            'trading_symbol': input("Enter trading symbol (e.g., RELIANCE): ").upper(),
            'quantity': int(input("Enter quantity: ")),
        }

        # Order Type Selection
        print("\nSelect Order Type:")
        for type in OrderType:
            print(f"{type.name}: {type.value}")
        order_type = input("Enter order type: ").upper()
        if order_type not in OrderType.__members__:
            raise ValueError("Invalid order type")
        order['order_type'] = OrderType[order_type].value

        # Get price details based on order type
        if order_type in ['LIMIT', 'SL']:
            order['limit_price'] = float(input("Enter limit price: "))
        if order_type in ['SL', 'SL_M']:
            order['trigger_price'] = float(input("Enter trigger price: "))

        # Variety Selection
        print("\nSelect Variety:")
        for variety in OrderVariety:
            print(f"{variety.name}: {variety.value}")
        variety = input("Enter variety: ").upper()
        if variety not in OrderVariety.__members__:
            raise ValueError("Invalid variety")
        order['variety'] = OrderVariety[variety].value

        # Product Selection
        print("\nSelect Product Type:")
        for product in ProductType:
            print(f"{product.name}: {product.value}")
        product = input("Enter product type: ").upper()
        if product not in ProductType.__members__:
            raise ValueError("Invalid product type")
        order['product'] = ProductType[product].value

        # Validity Selection
        print("\nSelect Validity:")
        for validity in OrderValidity:
            print(f"{validity.name}: {validity.value}")
        validity = input("Enter validity: ").upper()
        if validity not in OrderValidity.__members__:
            raise ValueError("Invalid validity")
        order['validity'] = OrderValidity[validity].value

        # Buy/Sell Operation
        operation = input("Enter operation (BUY/SELL): ").upper()
        if operation not in ['BUY', 'SELL']:
            raise ValueError("Operation must be BUY or SELL")
        order['operation'] = operation

        return order

    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return None

def display_order_summary(order):
    """Display a summary of the order details"""
    print("\nOrder Summary:")
    print("-" * 40)
    for key, value in order.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print("-" * 40)

def interactive_test():
    """Interactive test function for OrderManager"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    manager = OrderManager(
        api_key="your_test_api_key",
        access_token="your_test_access_token"
    )
    
    try:
        manager.start()
        logger.info("OrderManager started. Interactive test mode enabled.")
        
        while True:
            print("\nAvailable actions:")
            print("1. Place new order")
            print("2. Modify existing order")
            print("3. Cancel order")
            print("4. View active orders")
            print("5. Exit")
            
            choice = input("\nEnter your choice (1-5): ")
            
            if choice == '1':
                logger.info("Placing new order")
                order_details = get_order_details()
                if order_details:
                    display_order_summary(order_details)
                    if input("\nConfirm order placement? (y/n): ").lower() == 'y':
                        manager.add_order(order_details)
                        logger.info(f"Order placed successfully: {order_details['order_id']}")
                    
            elif choice == '2':
                logger.info("Modifying order")
                order_id = int(input("Enter order ID to modify: "))
                if order_id in manager.orders:
                    print("Enter new details:")
                    new_details = get_order_details()
                    if new_details:
                        display_order_summary(new_details)
                        if input("\nConfirm order modification? (y/n): ").lower() == 'y':
                            manager.modify_order(order_id, new_details)
                            logger.info(f"Order {order_id} modified successfully")
                else:
                    logger.warning(f"Order {order_id} not found")
                    
            elif choice == '3':
                logger.info("Cancelling order")
                order_id = int(input("Enter order ID to cancel: "))
                if order_id in manager.orders:
                    if input("\nConfirm order cancellation? (y/n): ").lower() == 'y':
                        manager.cancel_order(order_id)
                        logger.info(f"Order {order_id} cancelled successfully")
                else:
                    logger.warning(f"Order {order_id} not found")

            elif choice == '4':
                logger.info("Viewing active orders")
                if manager.orders:
                    print("\nActive Orders:")
                    for order_id, details in manager.orders.items():
                        print(f"\nOrder ID: {order_id}")
                        display_order_summary(details)
                else:
                    print("No active orders")
                    
            elif choice == '5':
                logger.info("Exiting interactive test")
                break
                
            else:
                logger.warning("Invalid choice. Please enter 1-5")
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Error during interactive test: {e}", exc_info=True)
    finally:
        manager.stop()
        logger.info("OrderManager stopped. Test completed.")

if __name__ == "__main__":
    interactive_test() 