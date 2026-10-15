from src import config

from sentence_transformers import SentenceTransformer
from src.storage.qdrant import DB
from src.retreival.services.llm import Model
from src.retreival.services.reranker import Reranker
from src.retreival.services.metadata_filters import MetadataFiltering
from src.retreival.services.quary_decomposer import QDecomposer

class QdrantRetreivar():
    def __init__(self):
        self.model = SentenceTransformer(config.sentence_transformer)
        self.db = DB(config.db_dir, config.db_collections)
        self.reranker = Reranker()
        self.llm_model = Model()
        self.metadata_filter = MetadataFiltering(self.llm_model)
        self.query_decomposer = QDecomposer(self.llm_model)

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
        chunk_context = ""
        for chunk in chunks:
            for spoints in chunk[1]:
                payload = spoints.payload
                chunk_context += "\n\n" + payload['text']
        return chunk_context

    def get_reranked_chunks(self, query, top_n_chunks):
        return self.reranker.rerank(query, top_n_chunks, 5)

    def get_query_output(self, query, query_info):
        query_vector = self.get_vector(query_info.search_query)
        filters = self.metadata_filter.validate_filters(query_info.filters)
        top_n_items = self.db.search(
                        query_vector,
                        query,
                        qdrant_filters=filters,
                        top_n=config.top_n_results
                    )
        reranked_chunks = self.get_reranked_chunks(query, top_n_items)
        return reranked_chunks

    def get_reranked_top_n(self, query):
        # query_dcomp_response = self.query_decomposer.get_decomposed_query(query)
        # print(query_dcomp_response)
        # return ""
        cleaned_query_list = self.metadata_filter.get_metadata_filters(query)

        reranked_chunks = []
        if cleaned_query_list.is_multi_part:

            for sub_query in cleaned_query_list.sub_queries:
                reranked_chunks.extend(list(self.get_query_output(query, sub_query)))
        else:
            reranked_chunks = self.get_query_output(query, cleaned_query_list.sub_queries[0])
       
        self.close()
        # print(f"re ranked chunks = {reranked_chunks}")
        return reranked_chunks

    def get_top_n_results(self, query):
        reranked_chunks = self.get_reranked_top_n(query)
        doc_context = self.get_chunk_string(reranked_chunks)
        llm_response = self.llm_model.get_response(query, doc_context)
        return str(llm_response)

    def close(self):
        self.db.close()