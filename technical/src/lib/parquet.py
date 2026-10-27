import pyarrow as pa
import pyarrow.parquet as pq
import config


class ParquetHandler():
    def __init__(self):
        self.db_dir = config.parquite_files_dir

    def get_complete_file_path(self, file_name):
        return f"{self.db_dir}/{file_name}"

    def get_columns_from_records(self, records):
        columns = {
            "date": [row["date"].replace(tzinfo=None) for row in records], # Strip timezone for Parquet compatibility
            "open": [float(row["open"]) for row in records],
            "high": [float(row["high"]) for row in records],
            "low": [float(row["low"]) for row in records],
            "close": [float(row["close"]) for row in records],
            "volume": [int(row["volume"]) for row in records]
        }
        return columns

    def get_metadata(self, file_path):
        print(f"file path = {file_path}")
        metadata = pq.read_metadata(file_path)
        metadata = metadata.row_group(0).column(0).statistics
        return str(metadata.min), str(metadata.max)

    def save_to_file(self, table, complete_file_path):
        pq.write_table(
                table,
                complete_file_path,
                compression='snappy',
                row_group_size=100000,
                use_dictionary=True,
                write_statistics=True
            )

    def update_to_file(self, table, file_path):
        schema = pq.read_schema(file_path)
        with pq.ParquetWriter(
                file_path,
                schema=schema,
                compression='snappy') as writer:
            writer.write_table(table)

    def save_kite_data_to_parquet_files(self, records, file_name):
        columns = self.get_columns_from_records(records)
        table = pa.Table.from_pydict(columns)
        complete_file_path = self.get_complete_file_path(file_name)
        self.save_to_file(table, complete_file_path)
        print(f"saved to parquet files {complete_file_path}")

    def update_kite_data_to_parquet_files(self, records, file_name):
        columns = self.get_columns_from_records(records)
        table = pa.Table.from_pydict(columns)
        complete_file_path = self.get_complete_file_path(file_name)
        self.update_to_file(table, complete_file_path)
        print(f"saved to parquet files {complete_file_path}")

    def get_file_last_row_time_stamp(self, file_path):
        parquet_file = pq.ParquetFile(file_path)
        last_row_group = parquet_file.num_row_groups - 1
        last_table = parquet_file.read_row_group(last_row_group, columns=["date"])
        
        # Convert just that last entry to a Python datetime object
        last_timestamp = last_table["date"].to_pylist()[-1]
        return last_timestamp.date()

    def get_last_row_timestamp(self, file_name):
        file_path = self.get_complete_file_path(file_name)
        return self.get_file_last_row_time_stamp(file_path)

