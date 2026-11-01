import re
import json

from global_lib.llm import Model
from finance_agent.config import tools
from finance_agent.src.lib import tool_functions
from backtesting.lib import conditions_schema, indicators_schema, signal_schema

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

    return f"""You are an expert Quantitative Trading Strategy Compiler. Your single task is to convert natural language trading ideas into a strictly structured sequence of backtesting execution steps using the provided function schema.
indicator schema:
{indicators_schema.schema}
condition schema:
{conditions_schema.schema}
signal schema
{signal_schema.schema}

### Output Rules
1. Generate strictly in valid JSON matching the Backtesting Execution Schema and call respetive tool for execution.
2. Do NOT invent indicators or operators outside the provided schema reference.
3. Assign unique string IDs to each calculated indicator (e.g., "ema_fast", "rsi_14") so signal conditions can reference them as operands.
4. If the user does not specify timeframe or initial capital, apply default fallbacks (timeframe: "15m", capital: 100000).
5. output_format_instructions: "Return a JSON object containing a 'pipeline' key with ordered steps."
"""