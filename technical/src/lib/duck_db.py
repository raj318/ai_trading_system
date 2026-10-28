import duckdb
import config


class Duck():
    def __init__(self):
        self.con = duckdb.connect()
        self.perquet_file_dir = config.parquite_files_dir

    def query(self, command):
        return self.con.query(command).to_df()

    def get_file_path(self, company):
        # supported format as of now: {company}_15_5min_financial_data
        return f"{self.perquet_file_dir}/{company}_15_5min_financial_data.parquet"

    def get_command_for_request(self, company, start_date, end_date, interval):
        file_path = self.get_file_path(company)
        command = f"""
                    SELECT 
        time_bucket(INTERVAL '{interval}', date) as timestamp_bucket,
        '{company}' as ticker,
        arg_min(open, date) as open,
        max(high) as high,
        min(low) as low,
        arg_max(close, date) as close,
        sum(volume) as volume
    FROM '{file_path}'
    WHERE date >= '{start_date}'
    AND date <= '{end_date}'
    GROUP BY timestamp_bucket, ticker
    ORDER BY timestamp_bucket ASC;
    """
        return command

    def get_data_from_db(self, command):
        return self.con.execute(command).df()

    def get_company_data(self, company, start_date, end_date, interval):
        command = self.get_command_for_request(company, start_date, end_date, interval)
        result = self.get_data_from_db(command)
        return result
    
    