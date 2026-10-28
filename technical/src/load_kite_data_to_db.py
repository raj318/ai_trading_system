from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import datetime

import sys

current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent.parent
print(f"parent dir = {parent_dir}")
sys.path.append(str(parent_dir))

from technical.src.lib import kite_connect
from technical.src.lib import parquet
import config

class LoadData():
    def __init__(self, trading_api):
        self.api = trading_api()
        self.parquet = parquet.ParquetHandler()

    def connect_api(self):
        self.api.connect()

    def download_company_data(self, company, years):
        # print(self.api.get_account_details())
        # records = self.api.get_historical_data(company, years)
        records = self.api.get_5min_historical_data(company, years)
        return records

    def download_data_by_dates(self, company, dates):
        records = self.api.get_5min_historical_data_by_date(company, dates)
        return records

    def get_csv_file_path(self, company, years, interval):
        return f"{config.tech_hist_data_dir}/{company}_{years}_{interval}_financial_data.csv"

    def get_parquet_file_name(self, company, years=15, interval='5min'):
        return f"{company}_{years}_{interval}_financial_data.parquet"

    def save_to_csv(self, company, years, data, interval=""):
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
        file_path = self.get_csv_file_path(company, years, interval)
        print(f"file path to store extracted data = {file_path}")
        df.to_csv(file_path, index=False)

    def plot_kite_data(self, records, instrument_name):
        df = pd.DataFrame(records)
    
        # 2. Ensure date is in a clean datetime format for plotting
        # df['date'] = pd.to_datetime(df['date'])
        df.sort_values('date', inplace=True)
        
        # 3. Create an interactive candlestick chart with a range selector
        fig = go.Figure(data=[go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=instrument_name
        )])
        fig.update_layout(
        title=f"15-Year Historical Data Validation: {instrument_name}",
        yaxis_title="Price (INR)",
        xaxis_title="Timeline",
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(count=5, label="5y", step="year", stepmode="backward"),
                    dict(step="all") # Shows all 15 years
                ])
            ),
            rangeslider=dict(visible=True), # Timeline slider at the bottom
            type="date"
            )
        )
    
        # Open the interactive graph in your web browser
        fig.show()

    def save_to_parquet(self, company, years, records, interval=""):
        file_name = self.get_parquet_file_name(company, years, interval)
        self.parquet.save_kite_data_to_parquet_files(records, file_name)

    def update_to_parquet(self, file_name, records):
        self.parquet.update_kite_data_to_parquet_files(records, file_name)

    def download_data(self, company, years=1):
        self.connect_api()
        print(f"years = {years}")
        records = self.download_company_data(company, years=years)
        self.save_to_csv(company, years, records, interval='day')
        self.save_to_parquet(company, years, records, interval='5min')
        # self.plot_kite_data(records, company)

    def get_dates_to_sync(self, time_stamp):
        today = datetime.date.today()
        start_date = time_stamp + datetime.timedelta(days=1)
        missing_dates = []
        current_date = start_date

        while current_date <=today:
            missing_dates.append(current_date.strftime("%Y-%m-%d"))
            current_date += datetime.timedelta(days=1)
        return missing_dates

    def sync_to_latest(self, company):
        file_name = self.get_parquet_file_name(company)
        time_stamp = self.parquet.get_last_row_timestamp(file_name)
        print(type(time_stamp))
        dates_to_sync = self.get_dates_to_sync(time_stamp)
        print(dates_to_sync)
        records = self.download_data_by_dates(company, dates_to_sync)
        self.update_to_parquet(file_name, records)


def main():
    # load kite
    # get historical data for a company given
    # create sql DB
    # load the data
    # validate the data
    company = 'reliance'
    data_downloader = LoadData(kite_connect.KiteConnectAPI)
    # data_downloader.sync_to_latest(company=company)
    data_downloader.download_data(company=company, years=15)

if __name__ == "__main__":
    main()