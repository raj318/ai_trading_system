from sentence_transformers import CrossEncoder
from src import config

class Reranker():
    def __init__(self):
        self.rerank_model = CrossEncoder(config.reranker_model)

    def get_chunks_text(self, chunks):
        chunk_text_list = []
        for chunk in chunks:
            for score_point in chunk[1]:
                # print(score_point)
                chunk_text_list.append(score_point.payload.get('text', "").strip())
        return chunk_text_list

    def rerank(self, query, chunks, top_k):
        if not chunks:
            return []

        # for item in chunks:
        #     print(item)

        text_list = self.get_chunks_text(chunks)
        # print(f"text = {text_list}")

        new_pairs = [[query, item] for item in text_list]

        # print(f"new pair = {new_pairs}")
        scores = self.rerank_model.predict(new_pairs)

        sorted_pairs = [chunk_item for _, chunk_item in sorted(zip(scores, chunks), reverse=True)]

        # print(chunks)
        # print(sorted_pairs)
        return sorted_pairs[:top_k]