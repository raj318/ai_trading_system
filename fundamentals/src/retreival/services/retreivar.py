import config

from sentence_transformers import SentenceTransformer
from storage.qdrant import DB

class QdrantRetreivar():
    def __init__(self):
        self.model = SentenceTransformer(config.sentence_transformer)
        self.db = DB(config.db_dir, config.db_collections)

    def get_vector(self, text):
        return self.model.encode(text).tolist()

    def print_retreived_data(self, top_chunks):
        # print(type(top_chunks))
        for chunk in top_chunks:
            # print(type(chunk))
            # print(chunk[1])
            for score_point in chunk[1]:
                # print(score_point.id)
                # print(score_point.score)
                # print(score_point.payload)
                text = score_point.payload.get('text', "").strip()
                if text:
                    print(f"text = {score_point.payload.get('text', "")}")


    def get_top_n_results(self, query):
        query_vector = self.get_vector(query)
        top_n_items = self.db.search(query_vector, config.top_n_results)
        
        self.print_retreived_data(top_n_items)
        return "successful"

    def close(self):
        self.db.close()