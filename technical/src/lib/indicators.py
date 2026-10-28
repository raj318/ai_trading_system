import pandas as pd
import pandas_ta as ta

class Indicators():
    def __init__(self):
        pass

    def calculate_ema(self, close: pd.Series, length: int = 20) -> pd.Series:
        """function to calculate dyamic EMA"""
        ema_series = ta.ema(close, length=length)
        ema_series.name = f"EMA_{length}"
        return ema_series

    def calculate_sma(self, close: pd.Series, length: int = 50) -> pd.Series:
        """Calculates the Simple Moving Average (SMA) for a given series."""
        sma_series = ta.sma(close, length=length)
        sma_series.name = f"SMA_{length}"
        return sma_series

    def calculate_rsi(self, close: pd.Series, length: int = 14) -> pd.Series:
        """Calculates the Relative Strength Index (RSI)."""
        rsi_series = ta.rsi(close, length=length)
        rsi_series.name = f"RSI_{length}"
        return rsi_series

    def calculate_macd(
        self,
        close: pd.Series, 
        fast: int = 12, 
        slow: int = 26, 
        signal: int = 9
    ) -> pd.DataFrame:
        """Calculates Moving Average Convergence Divergence (MACD)."""
        macd_df = ta.macd(close, fast=fast, slow=slow, signal=signal)
        # Standardize column names across versions
        macd_df.columns = ["MACD", "MACD_Hist", "MACD_Signal"]
        return macd_df[["MACD", "MACD_Signal", "MACD_Hist"]]

    def calculate_atr(
        self,
        high: pd.Series, 
        low: pd.Series, 
        close: pd.Series, 
        length: int = 14
    ) -> pd.Series:
        """Calculates Average True Range (ATR) for volatility measuring."""
        atr_series = ta.atr(high=high, low=low, close=close, length=length)
        atr_series.name = f"ATR_{length}"
        return atr_series