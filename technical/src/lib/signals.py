import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from technical.src.lib.indicators import calculate_ema, calculate_rsi, calculate_macd

class SignalEvidence(BaseModel):
    """Supporting evidence and metadata for a generated signal."""
    strategy_name: str
    price: float
    indicators: Dict[str, float] = Field(description="Key indicator values at signal bar")
    reasoning: str = Field(description="Human/LLM readable explanation of triggered rules")

class TimestampedSignal(BaseModel):
    """Structured, timestamped signal output."""
    timestamp: str
    symbol: Optional[str] = None
    signal: int = Field(description="1 for BUY, -1 for SELL, 0 for HOLD")
    action: str = Field(description="BUY, SELL, or HOLD")
    evidence: SignalEvidence

def check_crossover(series_a: pd.Series, series_b: pd.Series) -> pd.Series:
    """Returns True on the exact bar where Series A crosses ABOVE Series B."""
    return (series_a > series_b) & (series_a.shift(1) <= series_b.shift(1))


def check_crossunder(series_a: pd.Series, series_b: pd.Series) -> pd.Series:
    """Returns True on the exact bar where Series A crosses BELOW Series B."""
    return (series_a < series_b) & (series_a.shift(1) >= series_b.shift(1))


def check_above_threshold(series: pd.Series, threshold: float) -> pd.Series:
    """Returns True where series value is strictly greater than threshold."""
    return series > threshold


def check_below_threshold(series: pd.Series, threshold: float) -> pd.Series:
    """Returns True where series value is strictly less than threshold."""
    return series < threshold


def combine_conditions_to_signals(
    buy_conditions: List[pd.Series], 
    sell_conditions: List[pd.Series]
) -> pd.Series:
    """
    Combines boolean Buy and Sell conditions into a single signal series of identical length.
    
    Returns:
        pd.Series: 1 for BUY, -1 for SELL, 0 for HOLD/NEUTRAL.
    """
    # 1. Logical AND for all Buy conditions
    combined_buy = buy_conditions[0]
    for cond in buy_conditions[1:]:
        combined_buy = combined_buy & cond

    # 2. Logical OR for all Sell conditions
    combined_sell = sell_conditions[0]
    for cond in sell_conditions[1:]:
        combined_sell = combined_sell | cond

    # 3. Create index-matched Series initialized to 0
    signals = pd.Series(0, index=buy_conditions[0].index, name="signal", dtype=int)

    # 4. Apply Buy and Sell signals
    signals.loc[combined_buy] = 1
    signals.loc[combined_sell] = -1
    
    # 5. Handle Conflict (If both Buy and Sell trigger on the same bar, set to 0)
    conflict = combined_buy & combined_sell
    signals.loc[conflict] = 0

    return signals

def _extract_evidence_signals(
    df: pd.DataFrame,
    strategy_name: str,
    symbol: str,
    indicator_cols: List[str],
    reasoning_fn
) -> List[TimestampedSignal]:
    """Helper engine that packages active signal rows into structured Pydantic models."""
    active_df = df[df['signal'] != 0]
    signals: List[TimestampedSignal] = []

    for idx, row in active_df.iterrows():
        ts_str = idx.strftime("%Y-%m-%d %H:%M:%S") if isinstance(idx, pd.Timestamp) else str(idx)
        sig_val = int(row['signal'])
        action = "BUY" if sig_val == 1 else "SELL"

        # Build indicators snapshot dictionary
        indicators_snapshot = {col: round(float(row[col]), 2) for col in indicator_cols if col in row}
        
        # Generate reasoning text
        reasoning = reasoning_fn(sig_val, row)

        evidence = SignalEvidence(
            strategy_name=strategy_name,
            price=round(float(row['close']), 2),
            indicators=indicators_snapshot,
            reasoning=reasoning
        )

        signals.append(
            TimestampedSignal(
                timestamp=ts_str,
                symbol=symbol,
                signal=sig_val,
                action=action,
                evidence=evidence
            )
        )

    return signals

def generate_ma_crossover_signals(
    df: pd.DataFrame,
    symbol: str = "TICKER",
    fast_len: int = 20,
    slow_len: int = 50
) -> List[TimestampedSignal]:
    """Generates timestamped signals for MA Crossover Strategy."""
    df = df.copy()
    fast_col = f"EMA_{fast_len}"
    slow_col = f"EMA_{slow_len}"

    df[fast_col] = calculate_ema(df['close'], length=fast_len)
    df[slow_col] = calculate_ema(df['close'], length=slow_len)

    buy_mask = check_crossover(df[fast_col], df[slow_col])
    sell_mask = check_crossunder(df[fast_col], df[slow_col])

    df['signal'] = 0
    df.loc[buy_mask, 'signal'] = 1
    df.loc[sell_mask, 'signal'] = -1

    def reasoning_builder(sig_val, row):
        if sig_val == 1:
            return f"Golden Cross: {fast_col} ({row[fast_col]:.2f}) crossed ABOVE {slow_col} ({row[slow_col]:.2f})."
        return f"Death Cross: {fast_col} ({row[fast_col]:.2f}) crossed BELOW {slow_col} ({row[slow_col]:.2f})."

    return _extract_evidence_signals(
        df, "MA Crossover", symbol, [fast_col, slow_col], reasoning_builder
    )


def generate_rsi_mean_reversion_signals(
    df: pd.DataFrame,
    symbol: str = "TICKER",
    rsi_len: int = 14,
    oversold: float = 30.0,
    overbought: float = 70.0
) -> List[TimestampedSignal]:
    """Generates timestamped signals for RSI Mean-Reversion Strategy."""
    df = df.copy()
    rsi_col = f"RSI_{rsi_len}"
    df[rsi_col] = calculate_rsi(df['close'], length=rsi_len)

    buy_mask = check_crossover(df[rsi_col], pd.Series(oversold, index=df.index))
    sell_mask = check_crossunder(df[rsi_col], pd.Series(overbought, index=df.index))

    df['signal'] = 0
    df.loc[buy_mask, 'signal'] = 1
    df.loc[sell_mask, 'signal'] = -1

    def reasoning_builder(sig_val, row):
        if sig_val == 1:
            return f"Oversold Recovery: {rsi_col} ({row[rsi_col]:.2f}) crossed back ABOVE oversold threshold ({oversold})."
        return f"Overbought Reversal: {rsi_col} ({row[rsi_col]:.2f}) crossed back BELOW overbought threshold ({overbought})."

    return _extract_evidence_signals(
        df, "RSI Mean Reversion", symbol, [rsi_col], reasoning_builder
    )

def generate_atr_breakout_signals(
    df: pd.DataFrame,
    symbol: str = "TICKER",
    ema_len: int = 20,
    atr_len: int = 14,
    atr_mult: float = 1.5
) -> List[TimestampedSignal]:
    """Generates timestamped signals for ATR Volatility Breakout Strategy."""
    df = df.copy()
    ema_col = f"EMA_{ema_len}"
    atr_col = f"ATR_{atr_len}"

    df[ema_col] = calculate_ema(df['close'], length=ema_len)
    df[atr_col] = calculate_atr(df['high'], df['low'], df['close'], length=atr_len)

    breakout_level = df[ema_col] + (df[atr_col] * atr_mult)
    df['Breakout_Threshold'] = breakout_level

    buy_mask = check_crossover(df['close'], breakout_level)
    sell_mask = check_crossunder(df['close'], df[ema_col])

    df['signal'] = 0
    df.loc[buy_mask, 'signal'] = 1
    df.loc[sell_mask, 'signal'] = -1

    def reasoning_builder(sig_val, row):
        if sig_val == 1:
            return f"Volatility Breakout: Price ({row['close']:.2f}) broke ABOVE {ema_col} + {atr_mult}x {atr_col} threshold ({row['Breakout_Threshold']:.2f})."
        return f"Breakout Exit: Price ({row['close']:.2f}) dropped back BELOW trailing {ema_col} ({row[ema_col]:.2f})."

    return _extract_evidence_signals(
        df, "ATR Volatility Breakout", symbol, [ema_col, atr_col, "Breakout_Threshold"], reasoning_builder
    )

def generate_confluence_signals_with_evidence(
    df: pd.DataFrame,
    symbol: str = "RELIANCE",
    fast_len: int = 20,
    slow_len: int = 50,
    rsi_len: int = 14
) -> List[TimestampedSignal]:
    """
    Generates structured, timestamped signals with full numerical evidence.
    Expects df with DateTimeIndex or a 'timestamp' column and 'close'.
    """
    df = df.copy()
    
    # 1. Compute Indicators
    df['EMA_20'] = calculate_ema(df['close'], length=fast_len)
    df['EMA_50'] = calculate_ema(df['close'], length=slow_len)
    df['RSI_14'] = calculate_rsi(df['close'], length=rsi_len)
    
    macd_df = calculate_macd(df['close'])
    df['MACD'] = macd_df['MACD']
    df['MACD_Signal'] = macd_df['MACD_Signal']
    df['MACD_Hist'] = macd_df['MACD_Hist']

    # 2. Evaluate Boolean Conditions
    uptrend = df['EMA_20'] > df['EMA_50']
    macd_positive = df['MACD_Hist'] > 0
    rsi_cross_50 = check_crossover(df['RSI_14'], pd.Series(50.0, index=df.index))
    
    downtrend_cross = check_crossunder(df['EMA_20'], df['EMA_50'])
    rsi_overbought = df['RSI_14'] > 70.0

    buy_mask = uptrend & macd_positive & rsi_cross_50
    sell_mask = downtrend_cross | rsi_overbought

    # 3. Vectorized Signal Mapping
    df['signal'] = 0
    df.loc[buy_mask, 'signal'] = 1
    df.loc[sell_mask, 'signal'] = -1

    # Filter only active signal rows (skip HOLD/0 to save tokens, or keep all if needed)
    active_signals_df = df[df['signal'] != 0]

    structured_signals: List[TimestampedSignal] = []

    # 4. Extract Structured Evidence per Signal
    for idx, row in active_signals_df.iterrows():
        # Handle index timestamp formatting
        ts_str = idx.strftime("%Y-%m-%d %H:%M:%S") if isinstance(idx, pd.Timestamp) else str(idx)
        
        signal_val = int(row['signal'])
        action = "BUY" if signal_val == 1 else "SELL"
        
        # Build contextual reasoning string
        if signal_val == 1:
            reasoning = (
                f"Uptrend confirmed (EMA_{fast_len} {row['EMA_20']:.2f} > EMA_{slow_len} {row['EMA_50']:.2f}), "
                f"MACD Histogram positive ({row['MACD_Hist']:.2f}), and RSI crossed above 50 ({row['RSI_14']:.2f})."
            )
        else:
            reasoning = (
                f"Exit triggered: RSI overbought ({row['RSI_14']:.2f} > 70) or "
                f"EMA Bearish Crossunder (EMA_{fast_len}: {row['EMA_20']:.2f}, EMA_{slow_len}: {row['EMA_50']:.2f})."
            )

        evidence = SignalEvidence(
            strategy_name="Multi-Indicator Confluence",
            price=float(row['close']),
            indicators={
                f"EMA_{fast_len}": round(float(row['EMA_20']), 2),
                f"EMA_{slow_len}": round(float(row['EMA_50']), 2),
                "RSI_14": round(float(row['RSI_14']), 2),
                "MACD": round(float(row['MACD']), 2),
                "MACD_Signal": round(float(row['MACD_Signal']), 2),
                "MACD_Hist": round(float(row['MACD_Hist']), 2)
            },
            reasoning=reasoning
        )

        structured_signals.append(
            TimestampedSignal(
                timestamp=ts_str,
                symbol=symbol,
                signal=signal_val,
                action=action,
                evidence=evidence
            )
        )

    return structured_signals