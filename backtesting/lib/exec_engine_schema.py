indicators = {
  "strategy_name": "string",
  "indicators": [
    {
      "id": "string",
      "type": "I_EMA | I_SMA | I_RSI",
      "input": "string", # close, open, high, low
      "parameters": {
        "period": "integer greater than zero"
      }
    },
    {
        "id": "string",
        "type": "I_MACD",
        "input": "string", # close, open, high, low
        "parameters": {
            "fast": "integer greater than zero",
            "slow": "integer greater than zero",
            "signal": "integer greater than zero",
        }
    }
  ],
}
conditions = {
  "conditions": [
    {
      "id": "string",
      "type": "C_CROSS_ABOVE | C_CROSS_BELOW",
      "parameters": {
        "left": "string", # pd.series
        "right": "should be an indicator id" # pd.series
      }
    },
    {
          "id": "string",
          "type": "OP_GREATER_THAN | OP_LESS_THAN | C_CROSS_BELOW_VALUE | C_CROSS_ABOVE_VALUE",
          "parameters": {
            "left": "string", # pd.series
            "right": "integer greated than zero" # number only
          }
        }
  ],
}
signals= {
  "signals": [
    {
      "id": "string",
      "type": "SIG_BASIC",
      "parameters": {
        "left": "string", # pd.series
        "right": "string", # pd.series
        "condition":  "AND | OR",
        "action": "BUY | SELL"
      }
    }
  ],
  "output": "string reference to the final signal series"
}
