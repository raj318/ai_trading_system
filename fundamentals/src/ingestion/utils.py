from pathlib import Path
import pandas as pd

import csv
import config


def load_raw_documents_to_pandas():
    return pd.read_csv(config.RAW_DOCUMENT_DETAILS)

def ingest_to_rag(documents_df):
    for document in documents_df.to_dict(orient='records'):
        print(document)

