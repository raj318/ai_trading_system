from src import config
import uuid
import sys
from lib import utils

from qdrant_client.models import PointStruct, SparseVector
from src.storage.qdrant import DB

class db_helper():
    def __init__(self):
        self.vector_file_path = None
        self.doc_details = None
        self.db = DB(config.db_dir, config.db_collections)

    def set_doc_details(self, doc_details):
        self.doc_details = doc_details

    def set_vector_file_details(self, vector_file_path):
        self.vector_file_path = vector_file_path

    def set_doc_vector_details(self, doc_details, vector_file_path):
        self.set_doc_details(doc_details)
        self.set_vector_file_details(vector_file_path)

    def generate_points(self, doc_id_prefix, vector_data):
        return [
            PointStruct(
                            id=str(
                                uuid.uuid5(
                                    uuid.NAMESPACE_URL,
                                    vector_data[index]['metadata']['chunk_id']
                                )
                            ),
                            vector={
                                'dense': vector_data[index]['vector'],
                                'bm25': SparseVector(
                                    indices=vector_data[index]['sparse_vector']['indices'],
                                    values=vector_data[index]['sparse_vector']['values']
                                )
                            },
                            payload=vector_data[index]['metadata']
                        )
                            for index in range(len(vector_data))
            ]

    def load_vector_data(self):
        return utils.load_json(self.vector_file_path)

    def save_to_db(self, doc_id_prefix=""):
        vector_data = self.load_vector_data()
        points = self.generate_points(doc_id_prefix, vector_data)
        print(f"point payload = {points[0].payload}")
        self.db.add_vectors_metadata_to_db(config.vector_size, points)

    def delete_the_data(self):
        self.db.delete_all()
        return True
