schema = {
  "id": "SIG_BASIC",
  "name": "Basic Trading Signal",
  "description": "Generates a trading action when its input Boolean condition is satisfied",
  "input": {
    "type": "boolean_series",
    "required": True
  },
  "parameters": {
    "action": {
      "type": "string",
      "required": True,
      "allowed_values": [
        "BUY",
        "SELL"
      ]
    }
  },
  "output": {
    "type": "signal_series",
    "possible_values": [
      "BUY",
      "SELL",
      "HOLD"
    ]
  }
}