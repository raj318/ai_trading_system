
schema = [{
  "id": "I_EMA",
  "name": "Exponential Moving Average",
  "description": "Calculates EMA over a price series",
  "input": {
    "source": "price_series"
  },
  "parameters": {
    "period": {
      "type": "integer",
      "required": True
    }
  },
  "output": {
    "type": "numeric_series"
  }
},
{
  "id": "I_SMA",
  "name": "Simple Moving Average",
  "description": "Calculates SMA over a price series",
  "input": {
    "source": "price_series"
  },
  "parameters": {
    "period": {
      "type": "integer",
      "required": True,
      "minimum": 1
    }
  },
  "output": {
    "type": "numeric_series"
  }
},
{
  "id": "I_RSI",
  "name": "Relative Strength Index",
  "description": "Calculates RSI over a price series",
  "input": {
    "source": "price_series"
  },
  "parameters": {
    "period": {
      "type": "integer",
      "required": True,
      "minimum": 1
    }
  },
  "output": {
    "type": "numeric_series"
  }
}
]
