from src import config

from sentence_transformers import SentenceTransformer
from src.storage.qdrant import DB
from src.retreival.services.llm import Model
from src.retreival.services.reranker import Reranker
from src.retreival.services.metadata_filters import MetadataFiltering

class QdrantRetreivar():
    def __init__(self):
        self.model = SentenceTransformer(config.sentence_transformer)
        self.db = DB(config.db_dir, config.db_collections)
        self.reranker = Reranker()
        self.llm_model = Model()
        self.metadata_filter = MetadataFiltering(self.llm_model)

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

    def get_reranked_chunks(self, query, top_n_chunks):
        return self.reranker.rerank(query, top_n_chunks, 20)

    def get_reranked_top_n(self, query):
        qdrant_filters = self.metadata_filter.get_metadata_filters(query)
        print(f"query = {query}")
        query_vector = self.get_vector(query)
        print(f"qdrant_filters = {qdrant_filters}")
        top_n_items = self.db.search(query_vector, qdrant_filters=qdrant_filters, top_n=config.top_n_results)
        # print(f"got main chunks = {top_n_items}")
        reranked_chunks = self.get_reranked_chunks(query, top_n_items)
        # print(f"reranked chunks = {reranked_chunks}")
        self.close()
        
        return reranked_chunks

    def get_top_n_results(self, query):
        reranked_chunks = self.get_reranked_top_n(query)
        doc_context = self.get_chunk_string(reranked_chunks)
        llm_response = self.llm_model.get_response(query, doc_context)
        return str(llm_response)

    def close(self):
        self.db.close()