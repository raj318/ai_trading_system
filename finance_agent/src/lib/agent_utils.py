import re
import json

from global_lib.llm import Model
from finance_agent.config import tools
from finance_agent.src.lib import tool_functions
from backtesting.lib import conditions_schema, indicators_schema, signal_schema, exec_engine_schema

model = Model()
def get_content_response(content):
    print(f"content = {content}")
    return model.get_content_response(content, tools=tools.TOOLS)

def get_tool_msg_dict(tool_str):
    data = json.loads(tool_str)
    return {
        'function_name': data.get('name'),
        'arguments': data.get('arguments', {}).get('question', "")
    }

def get_tool_msg_from_llm_response(response):
    pattern = r"<tool_call>\s*({.*?})\s*</tool_call>"
    match = re.search(pattern, response, re.DOTALL)
    if not match:
        return None
    print(f"groups = {match.groups()}")
    return match.group(1)

def response_contains_tool_calls(response):
    if 'tool_call' in response:
        return True
    return False

def execute_requested_tools(response):
    tool_json_str = get_tool_msg_from_llm_response(response)
    tool_msg_dict = get_tool_msg_dict(tool_json_str)

    # print(f"\n\ntool call details = {tool_msg_dict}\n\n")

    if tool_msg_dict['function_name'] in tool_functions.TOOL_REGISTRY:
        function = tool_functions.TOOL_REGISTRY[tool_msg_dict['function_name']]
        response = function(tool_msg_dict['arguments'])
        return response

def add_tool_result_to_message(message, results):
    result_msg = {
        'role': 'assistant',
        'content': "<tool_response>\n" + results + "\n</tool_response>"
    }
    message.append(result_msg)

def get_backtesting_schemas():

    return f"""

# Role: Trading Strategy Compiler

Convert the user's natural-language trading strategy into a valid backtesting configuration using the available tools.

Follow the tool execution order strictly.

## Step 1 — Indicators

Generate all indicators required for the user's strategy using the following schema:

{exec_engine_schema.indicators}

Call `get_indicator_schema`.

Rules:
- Include indicators required for both BUY and SELL conditions.
- Use only supported indicator types and parameters.
- Assign unique IDs.
- Do not generate conditions or signals yet.

## Step 2 — Conditions

Generate all conditions required for signal generation using the following schema:

{exec_engine_schema.conditions}

Call `get_conditions_schema` only after Step 1 completes.

Rules:
- Reference only indicator IDs returned from Step 1.
- Generate all required entry and exit conditions.
- Use the correct parameteres type.
- Use the correct condition type.
- Assign unique IDs.
- Do not generate signals yet.

## Step 3 — Signals

Generate all signals required by the user's strategy using the following schema:

{exec_engine_schema.signals}

Call `get_signal_schema` only after Step 2 completes.

Rules:
- Reference only condition IDs returned from Step 2.
- Generate BUY and SELL signals according to the user's strategy.
- Use `AND` or `OR` to combine conditions.
- Do not reference indicator IDs directly.
- Do not invent condition IDs.

## Step 4 — Backtesting

After all three generation tools complete:

- Combine indicators, conditions, and signals into the final strategy configuration.
- Set `strategy_name`.
- Set `output` to an existing signal ID.
- Validate all references.
- Call `get_backtesting_engine_results`.

## Strict Rules

1. Always check if both BUY and SELL signals are available, if not check with user.
2. Always execute in this order: Indicators → Conditions → Signals → Backtesting.
3. Call one tool at a time.
4. Never skip a step.Updat
5. Never generate missing IDs or references.
6. Never place condition definitions inside signals.
7. Never place signal definitions inside conditions.
8. Do not invent strategy logic.
9. If the strategy is ambiguous, ask the user for clarification.
"""