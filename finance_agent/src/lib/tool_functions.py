import requests
import pytz

from langchain.tools import tool
from datetime import datetime
from zoneinfo import ZoneInfo

from backtesting import backtesting
from backtesting.lib import pydantic_models

url = 'http://127.0.0.1:8005'
query_url = f'{url}/quary'


@tool
def search_fundamentals(question:str) -> str:
    """
    function to get fundamental data values like revenue, profits, ebitda values of a company
    Handles better with one simple question at a time
    """
    print("Searching for fundamentals")
    if not question:
        return "Question is emtpy!"
    data = {
        'quary': question
    }
    response = requests.post(query_url, json=data, timeout=1000)

    print(f"response = {response}")
    if response.status_code == 200:
        return response.json()
    else:
        return "No respone from RAG!"

@tool
def todays_date() -> str:
    """
    Function returns todays date
    """
    print("Getting today's date!")
    time_zone = pytz.timezone("Asia/Kolkata")
    now = datetime.now(time_zone)
    return str(now.strftime("%Y-%m-%d %H:%M:%S %Z"))

@tool
def get_current_financial_year() -> str:
    """function to get current financial year """
    print("Getting current financial year!")
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    if current_month < 4:
        start_year = current_year - 1
        end_year = current_year
    else:
        start_year = current_year
        end_year = current_year + 1

    start_str = str(start_year)[-1:]
    end_str = str(end_year)[-1:]

    return f"FY{start_str}-{end_str}"

@tool
def get_user_input(message) -> str:
    """function to get user input"""
    return input(f"\n{message}: ").strip()

@tool(args_schema=pydantic_models.StrategyConfig)
def get_backtesting_engine_results(**json_schema) -> str:
    """Passes the fully assembled JSON strategy schema to perform backtesting and return results."""
    print("Getting Backtesting engine!")
    print(f"json schema inside the tool = {json_schema}")
    back_testing =  backtesting.BackTesting()
    results = back_testing.execute(json_schema)
    return results

@tool(args_schema=pydantic_models.AllIndicatorConfig)
def get_indicator_schema(**json_schema) -> str:
    """Generates and returns the indicators JSON schema based on required technical indicators."""
    print(f"calling indicator schema")
    return json_schema

@tool(args_schema=pydantic_models.AllConditions)
def get_conditions_schema(**json_schema) -> str:
    """Generates and returns the condition rules JSON schema matching the created indicator IDs."""
    print(f"calling conditions schema")
    return json_schema

@tool(args_schema=pydantic_models.SignalConfig)
def get_signal_schema(**json_schema) -> str:
    """Generates and returns the buy/sell signals JSON schema matching the condition IDs."""
    print(f"calling signal schema")
    return json_schema

TOOL_REGISTRY = {
    'search_fundamentals': search_fundamentals,
    'todays_date': todays_date,
    'get_current_financial_year': get_current_financial_year,
    'get_user_input': get_user_input,
    'get_backtesting_engine_results': get_backtesting_engine_results,
    'get_indicator_schema': get_indicator_schema,
    'get_conditions_schema': get_conditions_schema,
    'get_signal_schema': get_signal_schema
}