import sys
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent.parent
sys.path.append(str(parent_dir))

from src import config
from src.storage.qdrant import DB

test_expected_chunk_index = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/src/test/test_chunk_set_1.json'

def main():

    model = SentenceTransformer(config.sentence_transformer)

    with open(test_expected_chunk_index, 'r', encoding='utf-8') as fd:
        test_data = json.load(fd)

    results = []
    mrr_score = None

    reciprocal_rank = 0
    sum_indexes = 0


    for test_q in test_data:

        retreiver =QdrantRetreivar()
        top_n_items = retreiver.get_reranked_top_n(test_q['question'])

        reciprocal_rank = 0
        for chunk in top_n_items:
            
            found_the_chunk = False
            for index, score_point in enumerate(chunk[1]):
                chunk_id = score_point.payload.get('chunk_id').strip()

                if chunk_id in test_q['expected_chunk_ids']:
                    reciprocal_rank = 1/(index + 1)
                    found_the_chunk = True
                    break
            if found_the_chunk:
                break
        sum_indexes += reciprocal_rank

    mrr_score = sum_indexes/len(test_data)
    print(f"\nMRR score = {mrr_score}\n")    

if __name__ == "__main__":
    main()