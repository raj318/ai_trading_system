
from typing import Any, Literal
from pydantic import BaseModel, Field


# -------------------------
# Indicator configuration
# -------------------------
SupportedIndicators = Literal[
    "rsi", 
    "sma", 
    "ema", 
    "macd", 
    "bollinger_bands", 
    "atr"
]

class IndicatorInput(BaseModel):
    source: str = Field(
        description="Market data source, such as open, high, low, close or volume"
    )


class IndicatorConfig(BaseModel):
    id: str
    step_type: Literal["indicator"] = Field(
        default="indicator",
        description="Pipeline step type. Must always be 'indicator'"
    )
    name: SupportedIndicators = Field(
        description="The indicator algorithm to run, e.g. 'rsi', 'sma', 'ema'"
    )
    input: IndicatorInput
    parameters: dict[str, Any]


# -------------------------
# Condition configuration
# -------------------------

class OperandReference(BaseModel):
    reference: str = Field(
        description="ID of an indicator or another supported numeric input"
    )


class OperandValue(BaseModel):
    value: float


class ConditionConfig(BaseModel):
    id: str
    type: str = Field(
        description="Condition registry ID, such as C_CROSS_ABOVE or OP_GREATER_THAN"
    )
    operands: list[OperandReference | OperandValue]


# -------------------------
# Signal configuration
# -------------------------

class SignalInput(BaseModel):
    reference: str = Field(
        description="Reference to a condition or logical expression"
    )


class SignalParameters(BaseModel):
    action: Literal["BUY", "SELL"]


class SignalConfig(BaseModel):
    id: str
    type: str = "SIG_BASIC"
    parameters: SignalParameters
    input: SignalInput


# -------------------------
# Complete strategy
# -------------------------

class StrategyConfig(BaseModel):
    indicators: list[IndicatorConfig]
    conditions: list[ConditionConfig]
    signals: list[SignalConfig]
