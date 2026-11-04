
from typing import Any, Literal, Union, Annotated
from pydantic import BaseModel, Field, ConfigDict

class StrictConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

class PeriodParameters(StrictConfig):
    period: int = Field(gt=0)

class MacdParameters(StrictConfig):
    fast: int = Field(gt=0)
    slow: int = Field(gt=0)
    signal: int = Field(gt=0)

class IndicatorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: Literal["I_EMA", "I_SMA", "I_RSI"]
    input: str
    parameters: PeriodParameters

class MACDIndicatorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: Literal["I_MACD"]
    input: str
    parameters: MacdParameters

IndicatorUnion = Union[IndicatorConfig, MACDIndicatorConfig]
IndicatorItem = Annotated[
    IndicatorUnion,
    Field(discriminator="type")
]
class AllIndicatorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_name: str
    indicators: list[IndicatorItem]

class ComparisonParameters(StrictConfig):
    left: str
    right: str 

class ValueComparisonParameters(StrictConfig):
    left: str
    right: int

class ConditionTwoSeriesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: Literal[
        "C_CROSS_ABOVE",
        "C_CROSS_BELOW"
    ]
    parameters: ComparisonParameters

class ConditionOneSeriesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: Literal[
        "OP_GREATER_THAN",
        "OP_LESS_THAN",
        "C_CROSS_ABOVE_VALUE",
        "C_CROSS_BELOW_VALUE"
    ]
    parameters: ValueComparisonParameters

ConditionConfig = Annotated[
    Union[ConditionTwoSeriesConfig, ConditionOneSeriesConfig],
    Field(discriminator="type")
]
class AllConditions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    strategy_name: str
    conditions: list[ConditionConfig]

class BasicSignalParameters(StrictConfig):
    left: str
    right: str
    condition: Literal['AND', 'OR']
    action: Literal["BUY", "SELL"]

class SignalConfig(BaseModel):

    id: str
    type: Literal["SIG_BASIC"]
    parameters: BasicSignalParameters


class StrategyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy_name: str
    indicators: list[IndicatorItem]
    conditions: list[ConditionConfig]
    signals: list[SignalConfig]
    output: str
