from typing import Union

import numpy as np
import pandas as pd
import pandas_ta as ta


class TradingEngineRegistry:

    # --------------------------------------------------
    # Indicators
    # --------------------------------------------------

    @staticmethod
    def I_EMA(data: pd.Series, period: int) -> pd.Series:
        if isinstance(period, bool) or not isinstance(period, int) or period < 1:
            raise ValueError("EMA period must be a positive integer")

        return ta.ema(data, length=period)

    @staticmethod
    def I_SMA(data: pd.Series, period: int) -> pd.Series:
        if isinstance(period, bool) or not isinstance(period, int) or period < 1:
            raise ValueError("SMA period must be a positive integer")

        return ta.sma(data, length=period)

    @staticmethod
    def I_RSI(data: pd.Series, period: int) -> pd.Series:
        if isinstance(period, bool) or not isinstance(period, int) or period < 1:
            raise ValueError("RSI period must be a positive integer")

        return ta.rsi(data, length=period)

    @staticmethod
    def I_MACD(
        data: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> pd.DataFrame:
        """
        Calculates MACD using pandas-ta.
        Returns a DataFrame containing 'macd', 'signal', and 'histogram'.
        """
        macd_df = ta.macd(
            close=data,
            fast=fast_period,
            slow=slow_period,
            signal=signal_period
        )
        
        # Standardize column naming for dynamic schema referencing
        # pandas-ta names columns like MACD_12_26_9, MACDs_12_26_9, MACDh_12_26_9
        macd_df.columns = ["macd", "histogram", "signal"]
        return macd_df

    # --------------------------------------------------
    # Conditions
    # --------------------------------------------------

    @staticmethod
    def C_CROSS_ABOVE(
        s1: pd.Series,
        s2: pd.Series
    ) -> pd.Series:

        return (s1 > s2) & (s1.shift(1) <= s2.shift(1))

    @staticmethod
    def C_CROSS_BELOW(
        s1: pd.Series,
        s2: pd.Series
    ) -> pd.Series:

        return (s1 < s2) & (s1.shift(1) >= s2.shift(1))

    @staticmethod
    def C_CROSS_BELOW_VALUE(
        s1: pd.Series,
        value: Union[pd.Series, float, int]
    ) -> pd.Series:

        return s1 < value

    @staticmethod
    def C_CROSS_ABOVE_VALUE(
        s1: pd.Series,
        value: Union[pd.Series, float, int]
    ) -> pd.Series:

        return s1 > value

    @staticmethod
    def OP_GREATER_THAN(
        s1: pd.Series,
        value: Union[pd.Series, float, int]
    ) -> pd.Series:

        return s1 > value

    @staticmethod
    def OP_LESS_THAN(
        s1: pd.Series,
        value: Union[pd.Series, float, int]
    ) -> pd.Series:

        return s1 < value

    # --------------------------------------------------
    # Logical Operators
    # --------------------------------------------------

    @staticmethod
    def LOG_AND(
        s1: pd.Series,
        s2: pd.Series
    ) -> pd.Series:

        return s1.fillna(False).astype(bool) & \
               s2.fillna(False).astype(bool)

    @staticmethod
    def LOG_OR(
        s1: pd.Series,
        s2: pd.Series
    ) -> pd.Series:

        return s1.fillna(False).astype(bool) | \
               s2.fillna(False).astype(bool)

    @staticmethod
    def LOG_NOT(
        s1: pd.Series
    ) -> pd.Series:

        return ~s1.fillna(False).astype(bool)

    # --------------------------------------------------
    # Signal Generator
    # --------------------------------------------------

    @staticmethod
    def SIG_BASIC(
        condition: str,
        left: pd.Series,
        right: pd.Series,
        action: str
    ) -> pd.Series:

        condition_upper = condition.upper()
        action_upper = action.upper()

        if condition_upper not in {"AND", "OR"}:
            raise ValueError("Condition must be either AND or OR")

        if action_upper not in {"BUY", "SELL"}:
            raise ValueError("Action must be either BUY or SELL")

        left = left.fillna(False).astype(bool)
        right = right.fillna(False).astype(bool)

        if condition_upper == "AND":
            combined = left & right
        else:
            combined = left | right

        return combined.map(
            lambda triggered: action_upper if triggered else "HOLD"
        )

    # --------------------------------------------------
    # Explicit Execution Registry
    # --------------------------------------------------

    @classmethod
    def get_execution_registry(cls):

        return {
            # Indicators
            "I_EMA": cls.I_EMA,
            "I_SMA": cls.I_SMA,
            "I_RSI": cls.I_RSI,
            "I_MACD": cls.I_MACD,

            # Conditions
            "C_CROSS_ABOVE": cls.C_CROSS_ABOVE,
            "C_CROSS_BELOW": cls.C_CROSS_BELOW,
            "OP_GREATER_THAN": cls.OP_GREATER_THAN,
            "OP_LESS_THAN": cls.OP_LESS_THAN,
            "C_CROSS_BELOW_VALUE": cls.C_CROSS_BELOW_VALUE,
            "C_CROSS_ABOVE_VALUE": cls.C_CROSS_ABOVE_VALUE,

            # Logical Operators
            "LOG_AND": cls.LOG_AND,
            "LOG_OR": cls.LOG_OR,
            "LOG_NOT": cls.LOG_NOT,

            # Signals
            "SIG_BASIC": cls.SIG_BASIC,
        }

    # --------------------------------------------------
    # Dynamic Dispatcher
    # --------------------------------------------------

    @classmethod
    def execute_node(
        cls,
        schema_id: str,
        *args,
        **kwargs
    ):

        execution_registry = cls.get_execution_registry()

        function = execution_registry.get(schema_id)

        if function is None:
            raise ValueError(
                f"Unsupported schema ID: {schema_id}"
            )

        return function(*args, **kwargs)