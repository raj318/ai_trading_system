import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from technical.src.lib.kite_utils import (
    initialize_kite,
    get_instrument_token,
    write_order_history,
    get_live_data,
    get_multiple_live_data,
    load_config,
    get_time_period,
    get_5min_time_period,
)

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class KiteConnectAPI:
    """Class to handle all Kite Connect API operations for NSE trading"""
    
    def __init__(self):
        """
        Initialize the Kite Connect API
        
        Parameters:
        - trading_symbol: Trading symbol of the stock (required)
        
        Raises:
        - ValueError: If trading_symbol is not provided or is empty
        """
        
            
        self.kite = None
        self.order_history = []
        self.trading_symbol = None
        self.exchange = "NSE"  # Fixed to NSE
        self.connect()
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def set_symbol_exchange(self, symbol, exchange="NSE"):
        self.exchange= exchange
        self.trading_symbol = symbol

    def validate_symbol_exchange(self):
        if not self.trading_symbol or not self.exchange.strip():
            error_msg = "Trading symbol is required and cannot be empty"
            logging.error(error_msg)
            return None
    
    def connect(self) -> None:
        """Initialize connection to Kite"""
        try:
            self.kite = initialize_kite()
            if not self.kite:
                raise
            logging.info(f"Successfully connected to Kite!")
        except Exception as e:
            logging.error(f"Failed to connect to Kite: {e}")
            raise

    def get_account_details(self) -> Dict[str, Any]:
        """Get account details and other information"""
        try:
            if not self.kite:
                raise Exception("Not connected to Kite. Call connect() first.")
                
            # Get user profile
            profile = self.kite.profile()
            logging.info("User Profile retrieved successfully")
            
            # Get account balance
            balance = self.kite.margins()
            logging.info("Account balance retrieved successfully")
            
            # Get holdings for the specific stock
            holdings = self.kite.holdings()
            stock_holdings = [h for h in holdings if h['tradingsymbol'] == self.trading_symbol]
            logging.info(f"Holdings for {self.trading_symbol} retrieved successfully")
            
            # Get positions for the specific stock
            positions = self.kite.positions()
            stock_positions = [p for p in positions.get('net', []) if p['tradingsymbol'] == self.trading_symbol]
            logging.info(f"Positions for {self.trading_symbol} retrieved successfully")
            
            return {
                "profile": profile,
                "balance": balance,
                "holdings": stock_holdings,
                "positions": stock_positions
            }
        except Exception as e:
            logging.error(f"Error fetching account details: {e}")
            raise

    def get_tocken_instrument_value(self, company):
        instrument = self.kite.instruments(exchange=self.exchange)
        token = None
        for inst in instrument:
            if inst["tradingsymbol"] == company.upper() and inst['segment'] == self.exchange:
                token = inst['instrument_token']
                break
        return token

    def get_historical_data(self, company, years, interval="day"):
        inst = self.get_tocken_instrument_value(company)
        date_intervals = get_time_period(years)
        all_data = []
        for start_date, end_date in date_intervals:
            records = self.kite.historical_data(
                        instrument_token=inst,
                        from_date=start_date,
                        to_date=end_date,
                        interval="day"
                    )
            all_data.extend(records)
        return all_data

    def get_5min_historical_data_by_date(self, company, dates):
        inst = self.get_tocken_instrument_value(company)
        all_records = []
        for date in dates:
            records = self.kite.historical_data(
                            instrument_token=inst,
                            from_date=f"{date} 09:00:00",
                            to_date=f"{date} 14:00:00",
                            interval="5minute"
                        )
            all_records.extend(records)
        return all_records

    def get_5min_historical_data(self, company, years):
        inst = self.get_tocken_instrument_value(company)
        date_intervals = get_5min_time_period(years=years)
        
        all_data = []
        for start_date, end_date in date_intervals:
            # print(f"start date = {start_date}")
            records = self.kite.historical_data(
                        instrument_token=inst,
                        from_date=start_date,
                        to_date=end_date,
                        interval="5minute"
                    )
            all_data.extend(records)
        return all_data

    def place_order(self, quantity: int, order_type: str = "MARKET", 
                   product: str = "CNC", transaction_type: str = "BUY") -> str:
        """
        Place an order for the configured stock

        Parameters:
        - quantity: Number of shares to buy/sell
        - order_type: Type of order (default: "MARKET")
        - product: Product type (default: "CNC" for Cash and Carry)
        - transaction_type: Type of transaction (default: "BUY")
                
        Returns:
        Order ID of the placed order
        """
        try:
            if not self.kite:
                raise Exception("Not connected to Kite. Call connect() first.")
                
            # Get instrument token
            instrument_token = get_instrument_token(self.kite, self.trading_symbol, self.exchange)
        
            # Place the order
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=self.exchange,
                tradingsymbol=self.trading_symbol,
                transaction_type=self.kite.TRANSACTION_TYPE_BUY if transaction_type == "BUY" else self.kite.TRANSACTION_TYPE_SELL,
                quantity=quantity,
                product=product,
                order_type=order_type
            )
        
            # Store order details
            order_details = {
                'order_id': order_id,
                'trading_symbol': self.trading_symbol,
                'quantity': quantity,
                'exchange': self.exchange,
                'order_type': order_type,
                'product': product,
                'transaction_type': transaction_type,
                'timestamp': datetime.now().isoformat()
            }
            self.order_history.append(order_details)
            
            logging.info(f"Order placed successfully! Order ID: {order_id}")
            return order_id
            
        except Exception as e:
            logging.error(f"Error placing order: {e}")
            raise

    def sell_order(self, quantity: int, order_type: str = "MARKET", 
                  product: str = "CNC") -> str:
        """
        Place a sell order for the configured stock

        Parameters:
        - quantity: Number of shares to sell
        - order_type: Type of order (default: "MARKET")
        - product: Product type (default: "CNC" for Cash and Carry)
                
        Returns:
        Order ID of the placed sell order
        """
        return self.place_order(
            quantity=quantity,
            order_type=order_type,
            product=product,
            transaction_type="SELL"
        )

    def get_live_data(self) -> Dict[str, Any]:
        """
        Get live market data for the configured stock
        
        Returns:
        Dictionary containing live market data
        """
        try:
            if not self.kite:
                raise Exception("Not connected to Kite. Call connect() first.")
            return get_live_data(self.kite, self.trading_symbol, self.exchange)
        except Exception as e:
            logging.error(f"Error getting live data: {e}")
            raise
    
    def get_multiple_live_data(self, trading_symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get live market data for multiple stocks
        
        Parameters:
        - trading_symbols: List of trading symbols (e.g., ["ITC", "RELIANCE"])
        
        Returns:
        Dictionary containing live market data for each symbol
        """
        try:
            if not self.kite:
                raise Exception("Not connected to Kite. Call connect() first.")
            return get_multiple_live_data(self.kite, trading_symbols, self.exchange)
        except Exception as e:
            logging.error(f"Error getting multiple live data: {e}")
            raise
    
    def save_order_history(self) -> None:
        """Save the current order history to file"""
        try:
            if self.order_history:
                write_order_history(self.order_history)
                logging.info("Order history saved successfully")
        except Exception as e:
            logging.error(f"Error saving order history: {e}")
            raise

    def place_gtt_order(self, trading_symbol: str, exchange: str, transaction_type: str, 
                       quantity: int, price: float, trigger_price: float, 
                       order_type: str = "LIMIT", validity: str = "DAY", current_price: float = None) -> str:
        """
        Place a Good Till Triggered (GTT) order using Kite Connect API
        
        Parameters:
        - trading_symbol: Trading symbol of the stock (e.g., "ITC")
        - exchange: Exchange name (e.g., "NSE")
        - transaction_type: "BUY" or "SELL"
        - quantity: Number of shares to trade
        - price: Order price
        - trigger_price: Price at which the order should be triggered
        - order_type: Type of order (default: "LIMIT")
        - validity: Order validity (default: "DAY")
        - current_price: Current price of the stock (optional, will fetch if not provided)
        
        Returns:
        GTT trigger ID
        
        Raises:
        - Exception: If order placement fails
        """
        try:
            # Validate inputs
            if not trading_symbol or not exchange:
                raise ValueError("Trading symbol and exchange are required")
            
            if transaction_type not in ["BUY", "SELL"]:
                raise ValueError("Transaction type must be 'BUY' or 'SELL'")
            
            # Use provided current_price or fetch LTP if not provided
            if current_price is not None:
                last_price = current_price
                logging.info(f"Using provided current price for {trading_symbol}: {last_price}")
            else:
                # Get current LTP (Last Traded Price) for the stock
                try:
                    ltp_data = self.kite.ltp(f"{exchange}:{trading_symbol}")
                    last_price = ltp_data[f"{exchange}:{trading_symbol}"]["last_price"]
                    logging.info(f"Current LTP for {trading_symbol}: {last_price}")
                except Exception as e:
                    logging.warning(f"Could not fetch LTP for {trading_symbol}: {e}")
                    # Use a price that's clearly different from trigger_price
                    last_price = trigger_price + 5.0  # Add 5 rupee buffer as fallback
                    logging.info(f"Using fallback last_price: {last_price}")
            
            # Ensure last_price is different from trigger_price to avoid validation error
            if abs(last_price - trigger_price) < 0.01:  # If they're too close
                if trigger_price < last_price:
                    last_price = trigger_price + 1.0  # Add 1 rupee buffer
                else:
                    last_price = trigger_price - 1.0  # Subtract 1 rupee buffer
                logging.info(f"Adjusted last_price to {last_price} to avoid validation error")
            
            # Define the order details that will be placed when the GTT triggers
            orders_to_place = [
                {
                    "exchange": exchange,
                    "tradingsymbol": trading_symbol,
                    "transaction_type": self.kite.TRANSACTION_TYPE_BUY if transaction_type == "BUY" else self.kite.TRANSACTION_TYPE_SELL,
                    "quantity": quantity,
                    "order_type": self.kite.ORDER_TYPE_LIMIT,
                    "product": self.kite.PRODUCT_CNC,
                    "price": price
                }
            ]
            
            # Log all GTT parameters being sent
            logging.info("=== GTT ORDER PARAMETERS ===")
            logging.info(f"trigger_type: {self.kite.GTT_TYPE_SINGLE}")
            logging.info(f"tradingsymbol: {trading_symbol}")
            logging.info(f"exchange: {exchange}")
            logging.info(f"trigger_values: {[trigger_price]}")
            logging.info(f"last_price: {last_price}")
            logging.info("orders_to_place:")
            for i, order in enumerate(orders_to_place):
                logging.info(f"  Order {i+1}:")
                logging.info(f"    exchange: {order['exchange']}")
                logging.info(f"    tradingsymbol: {order['tradingsymbol']}")
                logging.info(f"    transaction_type: {order['transaction_type']}")
                logging.info(f"    quantity: {order['quantity']}")
                logging.info(f"    order_type: {order['order_type']}")
                logging.info(f"    product: {order['product']}")
                logging.info(f"    price: {order['price']}")
            logging.info("=== END GTT PARAMETERS ===")
            
            # Place GTT order using Kite API
            gtt_response = self.kite.place_gtt(
                trigger_type=self.kite.GTT_TYPE_SINGLE,  # Single-leg GTT
                tradingsymbol=trading_symbol,
                exchange=exchange,
                trigger_values=[trigger_price],
                last_price=last_price,
                orders=orders_to_place
            )
            
            trigger_id = gtt_response.get('trigger_id')
            logging.info(f"GTT order placed successfully. Trigger ID: {trigger_id}")
            logging.info(f"Full GTT response: {gtt_response}")
            logging.info(f"Details: {trading_symbol} {transaction_type} {quantity} shares @ {price} (trigger: {trigger_price})")
            
            return trigger_id
            
        except Exception as e:
            logging.error(f"Error placing GTT order: {e}")
            logging.error(f"Exception type: {type(e).__name__}")
            logging.error(f"Exception details: {str(e)}")
            raise

    def get_gtt_orders(self) -> list:
        """
        Get all GTT orders
        
        Returns:
        List of GTT orders
        """
        try:
            # Try different methods based on Kite Connect version
            gtt_orders = None
            
            # Method 1: Try get_gtts() (newer versions)
            try:
                gtt_orders = self.kite.get_gtts()
                logging.info(f"Retrieved {len(gtt_orders)} GTT orders using get_gtts()")
                return gtt_orders
            except AttributeError:
                logging.warning("get_gtts() method not available, trying gtt_orders()")
            
            # Method 2: Try gtt_orders() (older versions)
            try:
                gtt_orders = self.kite.gtt_orders()
                logging.info(f"Retrieved {len(gtt_orders)} GTT orders using gtt_orders()")
                return gtt_orders
            except AttributeError:
                logging.warning("gtt_orders() method not available, trying gtts()")
            
            # Method 3: Try gtts() (alternative naming)
            try:
                gtt_orders = self.kite.gtts()
                logging.info(f"Retrieved {len(gtt_orders)} GTT orders using gtts()")
                return gtt_orders
            except AttributeError:
                logging.error("No GTT orders method found - gtts(), gtt_orders(), or get_gtts()")
            
            # If none of the methods work, return empty list
            logging.error("GTT orders method not available in this Kite Connect version")
            return []
            
        except Exception as e:
            logging.error(f"Error getting GTT orders: {e}")
            return []

    def modify_gtt_order(self, gtt_order_id: str, trading_symbol: str, exchange: str,
                        transaction_type: str, quantity: int, price: float, 
                        trigger_price: float, order_type: str = "LIMIT", 
                        validity: str = "DAY") -> str:
        """
        Modify an existing GTT order
        
        Parameters:
        - gtt_order_id: ID of the GTT order to modify
        - trading_symbol: Trading symbol of the stock
        - exchange: Exchange name
        - transaction_type: "BUY" or "SELL"
        - quantity: Number of shares to trade
        - price: Order price
        - trigger_price: Price at which the order should be triggered
        - order_type: Type of order (default: "LIMIT")
        - validity: Order validity (default: "DAY")
        
        Returns:
        Modified GTT order ID
        """
        try:
            # Validate inputs
            if not gtt_order_id:
                raise ValueError("GTT order ID is required")
            
            if transaction_type not in ["BUY", "SELL"]:
                raise ValueError("Transaction type must be 'BUY' or 'SELL'")
            
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            
            if price <= 0:
                raise ValueError("Price must be positive")
            
            if trigger_price <= 0:
                raise ValueError("Trigger price must be positive")
            
            # Get current LTP for the stock
            try:
                ltp_data = self.kite.ltp(f"{exchange}:{trading_symbol}")
                last_price = ltp_data[f"{exchange}:{trading_symbol}"]["last_price"]
            except Exception as e:
                logging.warning(f"Could not fetch LTP for {trading_symbol}: {e}")
                last_price = price
            
            # Define the modified order details
            orders_to_place = [
                {
                    "exchange": exchange,
                    "tradingsymbol": trading_symbol,
                    "transaction_type": self.kite.TRANSACTION_TYPE_BUY if transaction_type == "BUY" else self.kite.TRANSACTION_TYPE_SELL,
                    "quantity": quantity,
                    "order_type": self.kite.ORDER_TYPE_LIMIT,
                    "product": self.kite.PRODUCT_CNC,
                    "price": price
                }
            ]
            
            # Modify GTT order
            gtt_response = self.kite.modify_gtt(
                trigger_id=gtt_order_id,
                trigger_type=self.kite.GTT_TYPE_SINGLE,
                tradingsymbol=trading_symbol,
                exchange=exchange,
                trigger_values=[trigger_price],
                last_price=last_price,
                orders=orders_to_place
            )
            
            modified_trigger_id = gtt_response.get('trigger_id')
            logging.info(f"GTT order modified successfully. Trigger ID: {modified_trigger_id}")
            return modified_trigger_id
            
        except Exception as e:
            logging.error(f"Error modifying GTT order: {e}")
            raise

    def delete_gtt_order(self, gtt_order_id: str) -> bool:
        """
        Delete a GTT order
        
        Parameters:
        - gtt_order_id: ID of the GTT order to delete
        
        Returns:
        True if deletion was successful
        """
        try:
            if not gtt_order_id:
                raise ValueError("GTT order ID is required")
            
            # Delete GTT order
            self.kite.delete_gtt(gtt_order_id)
            
            logging.info(f"GTT order {gtt_order_id} deleted successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error deleting GTT order: {e}")
            raise

    def place_gtt_order_with_stop_loss(self, trading_symbol: str, exchange: str,
                                     quantity: int, price: float, trigger_price: float,
                                     stop_loss_price: float, order_type: str = "LIMIT",
                                     validity: str = "DAY") -> str:
        """
        Place a GTT order with stop loss
        
        Parameters:
        - trading_symbol: Trading symbol of the stock
        - exchange: Exchange name
        - quantity: Number of shares to trade
        - price: Order price
        - trigger_price: Price at which the order should be triggered
        - stop_loss_price: Stop loss price
        - order_type: Type of order (default: "LIMIT")
        - validity: Order validity (default: "DAY")
        
        Returns:
        GTT order ID
        """
        try:
            # Validate inputs
            if not trading_symbol or not exchange:
                raise ValueError("Trading symbol and exchange are required")
            
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            
            if price <= 0:
                raise ValueError("Price must be positive")
            
            if trigger_price <= 0:
                raise ValueError("Trigger price must be positive")
            
            if stop_loss_price <= 0:
                raise ValueError("Stop loss price must be positive")
            
            # Place GTT order with stop loss
            gtt_order_id = self.kite.place_gtt_order(
                tradingsymbol=trading_symbol,
                exchange=exchange,
                transaction_type="SELL",  # Stop loss is typically a sell order
                quantity=quantity,
                price=stop_loss_price,
                trigger_price=trigger_price,
                order_type=order_type,
                validity=validity
            )
            
            logging.info(f"GTT order with stop loss placed successfully. Order ID: {gtt_order_id}")
            logging.info(f"Details: {trading_symbol} SELL {quantity} shares @ {stop_loss_price} (trigger: {trigger_price})")
            
            return gtt_order_id
            
        except Exception as e:
            logging.error(f"Error placing GTT order with stop loss: {e}")
            raise

    def place_regular_order(self, trading_symbol: str, exchange: str, transaction_type: str, 
                           quantity: int, price: float, order_type: str = "MARKET", 
                           product: str = "CNC", validity: str = "DAY") -> str:
        """
        Place a regular (non-GTT) order
        
        Parameters:
        - trading_symbol: Trading symbol of the stock
        - exchange: Exchange name
        - transaction_type: "BUY" or "SELL"
        - quantity: Number of shares to trade
        - price: Order price (for market orders, this is the expected price)
        - order_type: Type of order (default: "MARKET")
        - product: Product type (default: "CNC" for Cash and Carry)
        - validity: Order validity (default: "DAY")
        
        Returns:
        - str: Order ID or None if error
        """
        try:
            if not self.kite:
                raise Exception("Not connected to Kite. Call connect() first.")
            
            # Get instrument token
            instrument_token = get_instrument_token(self.kite, trading_symbol, exchange)
            
            # Place the regular order
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=exchange,
                tradingsymbol=trading_symbol,
                transaction_type=self.kite.TRANSACTION_TYPE_BUY if transaction_type == "BUY" else self.kite.TRANSACTION_TYPE_SELL,
                quantity=quantity,
                product=product,
                order_type=order_type,
                price=price if order_type == "LIMIT" else None,  # Price only for LIMIT orders
                validity=validity
            )
            
            logging.info(f"Regular order placed successfully! Order ID: {order_id}")
            logging.info(f"Details: {trading_symbol} {transaction_type} {quantity} shares @ {price} ({order_type})")
            
            return order_id
            
        except Exception as e:
            logging.error(f"Error placing regular order: {e}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a regular order
        
        Parameters:
        - order_id: The order ID to cancel
        
        Returns:
        - bool: True if order was cancelled successfully, False otherwise
        """
        try:
            if not self.kite:
                logging.error("Kite connection not established")
                return False
            
            # Cancel the order
            cancelled_order = self.kite.cancel_order(order_id=order_id)
            
            if cancelled_order:
                logging.info(f"Order {order_id} cancelled successfully")
                return True
            else:
                logging.error(f"Failed to cancel order {order_id}")
                return False
                
        except Exception as e:
            logging.error(f"Error cancelling order {order_id}: {e}")
            return False