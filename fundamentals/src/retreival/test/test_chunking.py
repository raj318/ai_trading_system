import sys
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent.parent
sys.path.append(str(parent_dir))

from retreival import config
from storage.qdrant import DB

test_expected_chunk_index = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/src/retreival/test/test_chunk_set_1.json'

def main():

    model = SentenceTransformer(config.sentence_transformer)
    db = DB(config.db_dir, config.db_collections)

    with open(test_expected_chunk_index, 'r', encoding='utf-8') as fd:
        test_data = json.load(fd)

    for recall_index in [1, 3, 5, 10, 20]:
        results = []
        recall_score = None

        total_score = 0
        ind_score = 0



        for test_q in test_data:
            test_result = {}
            test_result['test_id'] = test_q['id']
            test_result['question'] = test_q['question']
            test_result['expected_chunk_id'] = test_q['expected_chunk_ids']
            test_result['retreived_chunk_index']= []

            
            qvector = model.encode(test_q['question']).tolist()
            top_n_items = db.search(qvector, recall_index)

            total_score += len(test_q['expected_chunk_ids'])
            
            for chunk in top_n_items:
                
                found_the_chunk = 0
                for index, score_point in enumerate(chunk[1]):
                    chunk_id = score_point.payload.get('chunk_id').strip()

                    if chunk_id in test_q['expected_chunk_ids']:
                        test_result['retreived_chunk_index'].append(index)
                        # print(f"found expected chunk id {test_q['expected_chunk_ids']} at {index}")
                        ind_score += 1
                        found_the_chunk = 1
                        break
                if found_the_chunk:
                    break
            
            results.append(test_result)

        recall_score = ind_score/total_score
        print(f"recall@{recall_index}= {recall_score}")

    db.close()
                # print(score_point.payload.get('text', '').strip() + "\n\n")
    

if __name__ == "__main__":
    main()

