from pathlib import Path
import pandas as pd

import os
import csv
import json

def load_raw_documents_to_pandas(documents_details_csv):
    return pd.read_csv(documents_details_csv)

def get_raw_document_details(documents_df):
    for document in documents_df.to_dict(orient='records'):
        yield document

def get_document_fields_for_hash(doc_details, keys_to_pick):
    return {
        key: doc_details[key] for key in keys_to_pick if key in doc_details.keys()
    }

def valid_document(document_path):
    return os.path.exists(document_path)

def load_json(document_path):
    with open(document_path, 'r', encoding='utf-8') as fd:
        data = json.load(fd)
    return data

def save_to_json(file_path, data):
    print(f"utils = {file_path}")
    if data:
        with open(file_path, 'w', encoding='utf-8') as fd:
            json.dump(data, fd, indent=2)
        return file_path
    return None