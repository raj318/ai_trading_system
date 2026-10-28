from datetime import datetime
from pydantic import BaseModel

def is_valid_date(date, format="%Y-%m-%d %H:%M:%S"):
    """
    Returns True if the date_string perfectly matches the format_string.
    Otherwise, returns False.
    """
    try:
        # Try to parse the string into a datetime object
        datetime.strptime(date, format)
        return True
    except ValueError:
        # Thrown if the string doesn't match the format tokens exactly
        return False


class BacktestConfig(BaseModel):
    initial_capital: float = 100_000
    position_size: int = 1
    entry_matching: str = "FIFO"