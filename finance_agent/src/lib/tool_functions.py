import requests

from langchain.tools import tool
from datetime import datetime
from zoneinfo import ZoneInfo

url = 'http://127.0.0.1:8005'
query_url = f'{url}/quary'


@tool
def search_fundamentals(question:str) -> str:
    """
    function to get fundamental data values like revenue, profits, ebitda values of a company
    """
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
    time_zone = pytz.timezone("Asia/Kolkata")
    date_time = datetime.now(tz)
    return str(dt.strftime("%Y-%m-%d %H:%M:%S %Z"))

@tool
def get_current_financial_year() -> str:
    """function to get current financial year """
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    if current_month < 4:
        start_year = current_year - 1
        end_year = current_year
    else:
        start_year = current_year
        end_year = current_year + 1

    start_str = str(start_year)[-2:]
    end_str = str(end_year)[-2:]

    return f"FY{start_str}-{end_str}"

TOOL_REGISTRY = {
    'search_fundamentals': search_fundamentals,
    'todays_date': todays_date,
    'get_current_financial_year': get_current_financial_year
}