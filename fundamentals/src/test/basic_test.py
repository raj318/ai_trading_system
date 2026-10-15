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

    for test_q in test_data[:5]:
        print(f"question = {test_q['question']}")
        retreiver = QdrantRetreivar()
        # top_n_items = retreiver.get_reranked_top_n(test_q['question'])
        response = retreiver.get_top_n_results(test_q['question'])
        print(f"expected chunk = {test_q['expected_chunk_ids']}")
        # for chunk in top_n_items:
        #     for sub_query in chunk:
        #         # print(f"sub query = {sub_query}")
        #         for index, score_point in enumerate(sub_query[1]):
        #             chunk_id = score_point.payload.get('chunk_id').strip()
        #             chunk_text = score_point.payload.get('text')
        #             print(f"index = {index}")
        #             print(f"chunk id i got= {chunk_id}")
        print(f"response = {response}")

if __name__ == "__main__":
    main()