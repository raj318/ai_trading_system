from pathlib import Path
import sys


current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent.parent
print(parent_dir)
sys.path.append(str(parent_dir))

from sentence_transformers import SentenceTransformer
from storage.qdrant import DB
from ingestion import config

model = SentenceTransformer(config.sentence_transformer)
db = DB(config.db_dir, config.db_collections)


def get_a_chunk():
    records = db.qdrant.retrieve(
        collection_name=config.db_collections,
        ids=["16ceaacd-455f-469f-a300-17abcea550b2"],
        with_payload=True,  # Set to True to get your stored metadata/text
        with_vectors=False  # Set to True if you also need the raw embedding array
    )
    return records

def main():
    records = get_a_chunk()
    for record in records:
        print(f"ID: {record.id}")
        print(f"Payload: {record.payload}")
        print(record)
        # Example if text is at the root of the payload dictionary
        # print(record.payload)
        

if __name__ == "__main__":
    main()
    db.close()