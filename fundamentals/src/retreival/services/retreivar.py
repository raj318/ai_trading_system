from src import config

from sentence_transformers import SentenceTransformer
from src.storage.qdrant import DB
from services.llm import Model

class QdrantRetreivar():
    def __init__(self):
        self.model = SentenceTransformer(config.sentence_transformer)
        self.db = DB(config.db_dir, config.db_collections)
        self.llm_model = Model()

    def get_vector(self, text):
        return self.model.encode(text).tolist()

    def get_chunks_text(self, top_chunks):
        # print(type(top_chunks))
        chunk_text = []
        for chunk in top_chunks:
            # print(type(chunk))
            # print(chunk[1])
            for score_point in chunk[1]:
                # # print(score_point.payload)
                chunk_text.append(score_point.payload.get('text', "").strip())
        return "\n\n".join(chunk_text)

    def get_top_n_results(self, query):
        query_vector = self.get_vector(query)
        top_n_items = self.db.search(query_vector, config.top_n_results)
        
        doc_context = self.get_chunks_text(top_n_items)
        llm_response = self.llm_model.get_response(query, doc_context)
        return str(llm_response)

    def close(self):
        self.db.close()