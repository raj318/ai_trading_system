import sys
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent.parent
sys.path.append(str(parent_dir))

from src import config
from src.storage.qdrant import DB
from src.retreival.services.retreivar import QdrantRetreivar

test_expected_chunk_index = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/src/test/test_chunk_set_5.json'

def main():

    model = SentenceTransformer(config.sentence_transformer)

    with open(test_expected_chunk_index, 'r', encoding='utf-8') as fd:
        test_data = json.load(fd)

    results = []
    mrr_score = None

    reciprocal_rank = 0
    sum_indexes = 0


    for test_q in test_data:

        retreiver = QdrantRetreivar()
        top_n_items = retreiver.get_reranked_top_n(test_q['question'])

        # print(f"top n items = {top_n_items}")
        reciprocal_rank = 0
        # print(f"top_n_items = {top_n_items}")
        for chunk in top_n_items:
            # print(f"chunk = {chunk}\n\n")
            found_the_chunk = False
            for index, score_point in enumerate(chunk[1]):
                print(f"score point = {score_point.payload}")

                chunk_id = score_point.payload.get('chunk_id').strip()
                print(f"chunk id i got= {chunk_id}")
                print(f"expected chunk id = {test_q['expected_chunk_ids']}")
                print()
        break



if __name__ == "__main__":
    main()