from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
from lib.docling_lib import PDFParser
from pathlib import Path

from src import config
from lib import utils

class EmbToVect():
    def __init__(self, sentence_transformer):
        self.sentence_model_name = sentence_transformer
        self.model = SentenceTransformer(self.sentence_model_name)
        self.sparse_model = SparseTextEmbedding(model_name='Qdrant/bm25')

    def get_vectors(self, chunk):
        return self.model.encode(chunk).tolist()

    def get_vector_size(self):
        return self.model.get_embedding_dimension()

class Embedder():
    def __init__(self, chunks_file_path, doc_details):
        self.chunks_file_path = chunks_file_path
        self.doc_details = doc_details
        self.pdf = PDFParser()
        self.text_to_vectors = EmbToVect(config.sentence_transformer)

    def get_embedding_vector_file_path(self):
        company = self.doc_details['company']
        doc_type = self.doc_details['document_type']
        document_path = self.doc_details['local_path']
        file_name = Path(document_path).stem + 'embeddings.json'
        return f"{config.processed_docs_dir}/{company}/{doc_type}/{file_name}"

    def load_chunks(self):
        return utils.load_json(self.chunks_file_path)

    def extract_text_from_chunks(self, chunks):
        text_list = []
        for chunk in chunks:
            text_list.append(chunk['text'])
        return text_list

    def get_embeddings(self, text_list):
        return self.text_to_vectors.get_vectors(text_list)

    def replace_text_with_vectors(self, chunks, text_embeddings, sparse_vectors):
        for chunk, vector, sparse_vec in zip(chunks, text_embeddings, sparse_vectors):
            chunk['vector'] = vector
            chunk['metadata']['text'] = chunk['text']
            chunk['sparse_vector'] = sparse_vec
        return chunks

    def save_embeddings(self, file_path, embeddings):
        utils.save_to_json(file_path, embeddings)

    def set_vector_size_in_config(self):
        v_size = self.text_to_vectors.get_vector_size()
        config.vector_size= v_size

    def get_vectors_from_text(self, text_list):
        raw_sparse_emb = list(self.text_to_vectors.sparse_model.embed(text_list))
        return [{
                'indices': emb.indices.tolist(),
                'values': emb.values.tolist()
                }
                for emb in raw_sparse_emb
            ]

    def generate_vectors(self, reset=False):
        embed_file_path = self.get_embedding_vector_file_path()
        self.set_vector_size_in_config()
        if not reset and utils.valid_document(embed_file_path):
            return embed_file_path
        chunks = self.load_chunks()
        text_list = self.extract_text_from_chunks(chunks)
        text_embeddings = self.get_embeddings(text_list)
        sparse_vectors = self.get_vectors_from_text(text_list)
        embedding_chunks = self.replace_text_with_vectors(chunks, text_embeddings, sparse_vectors)
        self.save_embeddings(embed_file_path, embedding_chunks)
        return embed_file_path