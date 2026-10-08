from src import config

from sentence_transformers import SentenceTransformer
from src.storage.qdrant import DB
from src.retreival.services.llm import Model
from src.retreival.services.reranker import Reranker

class QdrantRetreivar():
    def __init__(self):
        self.model = SentenceTransformer(config.sentence_transformer)
        self.db = DB(config.db_dir, config.db_collections)
        self.reranker = Reranker()
        self.llm_model = Model()

    def get_vector(self, text):
        return self.model.encode(text).tolist()

    def get_chunks_text(self, top_chunks):
        # print(type(top_chunks))
        chunk_text = []
        for chunk in top_chunks:
            for score_point in chunk[1]:
                chunk_text.append(score_point.payload.get('text', "").strip())
        return chunk_text

    def get_chunk_string(self, chunks):
        return "\n\n".join(chunks)

    # def get_text_list_from_chunks(self, top_n_chunks):
    #     chunk_text_list = []
    #     for chunk in top_n_chunks:
    #         for score_point in chunk[1]:
    #             chunk_text_list.append(score_point.payload.get('text', "").strip())
    #     return chunk_text_list

    def get_reranked_chunks(self, query, top_n_chunks):
        # text_list = self.get_text_list_from_chunks(top_n_chunks)
        return self.reranker.rerank(query, top_n_chunks, 5)

    def get_reranked_top_n(self, query):
        query_vector = self.get_vector(query)
        print("got query vector")
        top_n_items = self.db.search(query_vector, config.top_n_results)
        print("got top n items from db, basic")
        reranked_chunks = self.get_reranked_chunks(query, top_n_items)
        self.close()
        return reranked_chunks

    def get_top_n_results(self, query):
        reranked_chunks = self.get_reranked_top_n(query)
        doc_context = self.get_chunk_string(reranked_chunks)
        llm_response = self.llm_model.get_response(query, doc_context)
        return str(llm_response)

    def close(self):
        self.db.close()