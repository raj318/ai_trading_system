schema = [{
  "id": "C_CROSS_ABOVE",
  "name": "Crosses Above",
  "description": "Detects upward crossover",
  "operands": [
    "numeric_series",
    "numeric_series"
  ],
  "output": "boolean_series"
},
{
  "id": "C_CROSS_BELOW",
  "name": "Crosses below",
  "description": "Detects downwords crossover",
  "operands": [
    "numeric_series",
    "numeric_series"
  ],
  "output": "boolean_series"
},
{
  "id": "OP_GREATER_THAN",
  "name": "Greater Than",
  "operands": [
    "numeric_series",
    "number"
  ],
  "output": "boolean_series"
},
{
  "id": "OP_LESS_THAN",
  "name": "Less Than",
  "operands": [
    "numeric_series",
    "number"
  ],
  "output": "boolean_series"
}
]