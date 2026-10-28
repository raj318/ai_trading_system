import sys
from pathlib import Path

current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent.parent
print(f"parent dir = {parent_dir}")
sys.path.append(str(parent_dir))

from technical.src.lib import duck_db
from technical.src.lib import parquet
from technical.src.lib import utils

db = duck_db.Duck()


def get_market_data(company, start_date, end_date, interval='5 minutes'):
    if utils.is_valid_date(start_date) and utils.is_valid_date(end_date):
        data = db.get_company_data(
                company,
                start_date=start_date,
                end_date=end_date,
                interval=interval
                )
        return data
    else:
        print(f"One of the dates is not in right format {start_date} or {end_date}")

def get_data_range(company):
    file_path = db.get_file_path(company)
    perquet = parquet.ParquetHandler()
    return perquet.get_metadata(file_path)

def get_latest_timestamp(company):
    _, end = get_data_range(company)
    return end

if __name__ == "__main__":
    data = get_market_data('reliance', interval='30 minutes', start_date='2026-10-22 00:00:00', end_date='2026-10-22 23:59:59')
    print(f" metadata = {get_latest_timestamp('reliance')}")
    print(data)