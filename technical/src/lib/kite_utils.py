import yaml
from kiteconnect import KiteConnect
import logging
import json
from datetime import datetime, timedelta
import os
import signal
import sys
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
from kiteconnect.exceptions import TokenException

def setup_logger(name: str, stock_id: Optional[str] = None) -> logging.Logger:
    """
    Set up logger with file handler only
    
    Parameters:
    - name: Name of the module/logger
    - stock_id: Optional stock ID to include in log filename
    
    Returns:
    Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # If logger already has handlers, return it
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.DEBUG)
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.join('workdir', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create filename with date and optional stock ID
    date_str = datetime.now().strftime('%Y-%m-%d')
    if stock_id:
        filename = f"{stock_id}_{date_str}.log"
    else:
        filename = f"app_{date_str}.log"
    
    log_file = os.path.join(log_dir, filename)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(file_handler)
    
    return logger

# Create default logger for this module
logger = setup_logger(__name__)

def load_config() -> Dict[str, Any]:
    """
    Load configuration from config/config.yaml
    
    Returns:
    Dictionary containing configuration
    """
    try:
        # Try multiple possible paths for the config file
        possible_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kite_config.yaml')  # Absolute path from this file
        ]
        config_path = None
        for path in possible_paths:
            if os.path.exists(path):
                config_path = path
                break
        
        if not config_path:
            # If no path found, try to find it by searching from current directory
            current_dir = os.getcwd()
            while current_dir != os.path.dirname(current_dir):  # Stop at root directory
                test_path = os.path.join(current_dir, 'config', 'config.yaml')
                if os.path.exists(test_path):
                    config_path = test_path
                    break
                current_dir = os.path.dirname(current_dir)
        
        if not config_path:
            logger.error(f"Config file not found. Tried paths: {possible_paths}")
            logger.error(f"Current working directory: {os.getcwd()}")
            logger.error(f"Script location: {os.path.abspath(__file__)}")
            raise FileNotFoundError("Config file config/config.yaml not found in any expected location")
            
        logger.info(f"Using config file at: {config_path}")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        return config
        
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise



def get_5min_time_period(years=1):
    today = datetime.now().date()
    chunks = []
    
    current_end_date = today
    # Calculate total days to look back based on the number of years requested
    total_days_to_look_back = years * 365
    print(f"total days to look back {total_days_to_look_back}")
    days_processed = 0
    
    # Loop backward until we have covered the total number of days
    while days_processed < total_days_to_look_back:
        # Subtract 10 days for the current chunk
        current_start_date = current_end_date - timedelta(days=10)
        
        # Format dates as strings for the Kite API
        chunks.append((
            current_start_date.strftime("%Y-%m-%d"), 
            current_end_date.strftime("%Y-%m-%d")
        ))
        
        # Track our progress and move the window back for the next iteration
        days_processed += 10
        current_end_date = current_start_date - timedelta(days=1)
        
    # Reverse the list so the timeline runs chronologically from oldest to newest
    chunks.reverse()
    return chunks

def get_time_period(self, years=1):
    today = datetime.now().date()
    chunks = []
    
    current_end_date = today
    
    for year_range in range(years):
        current_start_date = current_end_date - timedelta(days=365)
        
        # Format dates as strings formatted for the Kite API (YYYY-MM-DD)
        chunks.append((
            current_start_date.strftime("%Y-%m-%d"), 
            current_end_date.strftime("%Y-%m-%d")
        ))
        
        # Move the next chunk's end date back to right before this start date
        current_end_date = current_start_date - timedelta(days=1)
        
    # Reverse the list so the timeline runs chronologically from oldest to newest
    chunks.reverse()
    return chunks

@contextmanager
def signal_handler(order_history: Optional[List[Dict[str, Any]]] = None):
    """
    Context manager to handle script termination
    
    Parameters:
    - order_history: Optional list of order details to save before exiting
    """
    def signal_handler(signum, frame):
        # Write order history before exiting
        if order_history:
            write_order_history(order_history)
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        yield
    finally:
        # Write order history before exiting
        if order_history:
            write_order_history(order_history)

def generate_access_token(kite):
    logger.error("Access token expired. Getting new token...")
    login_url = kite.login_url()
    print("Click on this URL to login:", login_url)
    request_token = input("provide access token after login: ")
    if not request_token:
        print("Did nto get input from user, exiting!")
        sys.exit(1)
    return request_token

def initialize_kite() -> KiteConnect:
    """Initialize Kite Connect with API credentials"""

    # Load configuration
    config = load_config()
    config = config['kite_connect']

    # Initialize Kite Connect
    kite = KiteConnect(api_key=config['api_key'])

    access_token = config.get('access_token')

    if access_token:
        kite.set_access_token(access_token)
        try:
            kite.profile()
            return kite

        except Exception as err:
            print(f"Access token is expired! Need to generate request token and retry")

    request_token = config.get('access_token')
    print(f"request token = {request_token}")
    if not request_token:
        request_token = generate_access_token(kite)
    # Generate session
    try:
        data = kite.generate_session(request_token, api_secret=config['api_secret'])
        # print("Generated session data:", data)
        access_token = data["access_token"]
        # Update only the access token in config file
        update_access_token(access_token)
        
        # Set access token
        kite.set_access_token(access_token)
    except TokenException as err:
        request_token = generate_access_token(kite)
        update_request_token(request_token)
        data = kite.generate_session(request_token, api_secret=config['api_secret'])
        print("Generated session data:", data)
        access_token = data["access_token"]
        # Update only the access token in config file
        update_access_token(access_token)
        
        # Set access token
        kite.set_access_token(access_token)
        return kite
    except Exception as err:
        print(f"some exception to be handled {str(err)}")
        return None

    print("test3")
    print("Successfully connected to Kite!")
    return kite
        

def get_instrument_token(kite: KiteConnect, trading_symbol: str, exchange: str = "NSE") -> int:
    """Get instrument token for a given trading symbol"""
    try:
        # Get all instruments
        instruments = kite.instruments(exchange)
        
        # Find the instrument
        for instrument in instruments:
            if instrument['tradingsymbol'] == trading_symbol:
                return instrument['instrument_token']
        
        raise Exception(f"Trading symbol {trading_symbol} not found in {exchange}")
    except Exception as e:
        logger.error(f"Error getting instrument token: {e}")
        raise

def find_latest_order_file() -> Optional[str]:
    """Find the most recent order history file in the workdir"""
    try:
        if not os.path.exists('workdir'):
            return None
            
        order_files = [f for f in os.listdir('workdir') if f.startswith('order_history_')]
        if not order_files:
            return None
            
        # Sort by filename (which includes timestamp) and get the latest
        latest_file = sorted(order_files)[-1]
        return os.path.join('workdir', latest_file)
    except Exception as e:
        logger.error(f"Error finding latest order file: {e}")
        return None

def get_latest_order_id() -> Optional[str]:
    """Get the most recent order ID from the latest order history file"""
    try:
        latest_file = find_latest_order_file()
        if not latest_file:
            return None
            
        with open(latest_file, 'r') as f:
            data = json.load(f)
            if data.get('orders'):
                return data['orders'][-1]['order_id']
        return None
    except Exception as e:
        logger.error(f"Error getting latest order ID: {e}")
        return None

def write_order_history(order_history: List[Dict[str, Any]]) -> None:
    """
    Write order history to a JSON file
    
    Parameters:
    - order_history: List of order details
    """
    try:
        # Create orders directory if it doesn't exist
        orders_dir = os.path.join('workdir', 'orders')
        os.makedirs(orders_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(orders_dir, f'orders_{timestamp}.json')
        
        # Write order history to file
        with open(filename, 'w') as file:
            json.dump(order_history, file, indent=2)
        logger.info(f"Order history written to {filename}")
    except Exception as e:
        logger.error(f"Error writing order history: {e}")
        raise

def get_live_data(kite: KiteConnect, trading_symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
    """
    Get live market data for a given stock
    
    Parameters:
    - kite: KiteConnect instance
    - trading_symbol: Trading symbol of the stock (e.g., "ITC")
    - exchange: Exchange name (default: "NSE")
    
    Returns:
    Dictionary containing live market data including:
    - Last traded price (LTP)
    - Volume
    - Buy/Sell quantities
    - Open/High/Low prices
    - Previous close
    - Change percentage
    """
    try:
        # Get instrument token
        instrument_token = get_instrument_token(kite, trading_symbol, exchange)
        
        # Get quote for the instrument
        quote = kite.quote(f"{exchange}:{trading_symbol}")
        
        if not quote:
            raise Exception(f"No quote data available for {trading_symbol}")
            
        # Extract relevant data
        instrument_data = quote[f"{exchange}:{trading_symbol}"]
        
        # Format the data
        live_data = {
            "trading_symbol": trading_symbol,
            "exchange": exchange,
            "last_traded_price": instrument_data.get("last_price", 0),
            "volume": instrument_data.get("volume", 0),
            "buy_quantity": instrument_data.get("buy_quantity", 0),
            "sell_quantity": instrument_data.get("sell_quantity", 0),
            "open_price": instrument_data.get("ohlc", {}).get("open", 0),
            "high_price": instrument_data.get("ohlc", {}).get("high", 0),
            "low_price": instrument_data.get("ohlc", {}).get("low", 0),
            "previous_close": instrument_data.get("ohlc", {}).get("close", 0),
            "change_percentage": instrument_data.get("change_percent", 0),
            "timestamp": datetime.now().isoformat()
        }
        
        # Print formatted data
        print(f"\nLive Market Data for {trading_symbol}:")
        print(f"Last Traded Price: ₹{live_data['last_traded_price']:.2f}")
        print(f"Change: {live_data['change_percentage']:.2f}%")
        print(f"Volume: {live_data['volume']:,}")
        print(f"Open: ₹{live_data['open_price']:.2f}")
        print(f"High: ₹{live_data['high_price']:.2f}")
        print(f"Low: ₹{live_data['low_price']:.2f}")
        print(f"Previous Close: ₹{live_data['previous_close']:.2f}")
        print(f"Buy Quantity: {live_data['buy_quantity']:,}")
        print(f"Sell Quantity: {live_data['sell_quantity']:,}")
        
        return live_data
        
    except Exception as e:
        logger.error(f"Error getting live data for {trading_symbol}: {e}")
        raise

def get_multiple_live_data(kite: KiteConnect, trading_symbols: List[str], exchange: str = "NSE") -> Dict[str, Dict[str, Any]]:
    """
    Get live market data for multiple stocks
    
    Parameters:
    - kite: KiteConnect instance
    - trading_symbols: List of trading symbols (e.g., ["ITC", "RELIANCE"])
    - exchange: Exchange name (default: "NSE")
    
    Returns:
    Dictionary containing live market data for each symbol
    """
    try:
        # Format instruments list
        instruments = [f"{exchange}:{symbol}" for symbol in trading_symbols]
        
        # Get quotes for all instruments
        quotes = kite.quote(instruments)
        
        if not quotes:
            raise Exception("No quote data available")
            
        # Process data for each symbol
        live_data = {}
        for symbol in trading_symbols:
            instrument_key = f"{exchange}:{symbol}"
            if instrument_key in quotes:
                instrument_data = quotes[instrument_key]
                
                live_data[symbol] = {
                    "trading_symbol": symbol,
                    "exchange": exchange,
                    "last_traded_price": instrument_data.get("last_price", 0),
                    "volume": instrument_data.get("volume", 0),
                    "buy_quantity": instrument_data.get("buy_quantity", 0),
                    "sell_quantity": instrument_data.get("sell_quantity", 0),
                    "open_price": instrument_data.get("ohlc", {}).get("open", 0),
                    "high_price": instrument_data.get("ohlc", {}).get("high", 0),
                    "low_price": instrument_data.get("ohlc", {}).get("low", 0),
                    "previous_close": instrument_data.get("ohlc", {}).get("close", 0),
                    "change_percentage": instrument_data.get("change_percent", 0),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Print formatted data for each symbol
                print(f"\nLive Market Data for {symbol}:")
                print(f"Last Traded Price: ₹{live_data[symbol]['last_traded_price']:.2f}")
                print(f"Change: {live_data[symbol]['change_percentage']:.2f}%")
                print(f"Volume: {live_data[symbol]['volume']:,}")
                print(f"Open: ₹{live_data[symbol]['open_price']:.2f}")
                print(f"High: ₹{live_data[symbol]['high_price']:.2f}")
                print(f"Low: ₹{live_data[symbol]['low_price']:.2f}")
                print(f"Previous Close: ₹{live_data[symbol]['previous_close']:.2f}")
                print(f"Buy Quantity: {live_data[symbol]['buy_quantity']:,}")
                print(f"Sell Quantity: {live_data[symbol]['sell_quantity']:,}")
        
        return live_data
        
    except Exception as e:
        logger.error(f"Error getting live data for multiple symbols: {e}")
        raise
def update_access_token(access_token: str) -> None:
    update_config(token=access_token, token_name='access_token')

def update_request_token(request_token: str) -> None:
    update_config(token=request_token, token_name='request_token')

def update_config(token: str, token_name: str)-> None:

    """Update only the access_token in config file while preserving all other values.
    
    Args:
        access_token: New access token to save
    """
    try:
        # Use the same path resolution logic as load_config
        possible_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'kite_config.yaml')  # Absolute path from this file
        ]
        
        config_path = None
        for path in possible_paths:
            if os.path.exists(path):
                config_path = path
                break
        
        if not config_path:
            # If no path found, try to find it by searching from current directory
            current_dir = os.getcwd()
            while current_dir != os.path.dirname(current_dir):  # Stop at root directory
                test_path = os.path.join(current_dir, 'config', 'config.yaml')
                if os.path.exists(test_path):
                    config_path = test_path
                    break
                current_dir = os.path.dirname(current_dir)
        
        if not config_path:
            raise FileNotFoundError("Config file config/config.yaml not found in any expected location")
        
        # Read existing config file
        with open(config_path, 'r') as f:
            existing_config = yaml.safe_load(f)
        
        # Update only the access_token in kite_connect section
        if 'kite_connect' not in existing_config:
            existing_config['kite_connect'] = {}
        existing_config['kite_connect'][token_name] = token
        
        # Save updated config while preserving other sections
        with open(config_path, 'w') as f:
            yaml.dump(existing_config, f, default_flow_style=False)
            
        # print(f"Access token updated in {config_path}")
        
    except Exception as e:
        print(f"Error updating access token: {e}")
        raise 