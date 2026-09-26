import uuid
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from qdrant_client.models import Distance, PointStruct, VectorParams

class Vembeddings():
    def __init__(self, db_file, collection_name):
        self.db_file = db_file # '/Users/raj/Documents/personal/ai_trading_system/fundamentals/vectordb/fundamentals_db'
        self.collection_name = collection_name
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.create_db_instance()

    def get_vectors(self, chunk):
        return self.model.encode(chunk).tolist()

    def create_db_instance(self):
        self.qdrant = QdrantClient(path=self.db_file)

    def create_collection(self, vector_size):
        if not self.qdrant.collection_exists(self.collection_name):
            self.qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                                    size=vector_size,
                                    distance=Distance.COSINE
                                )
                )

    def get_points(self, vectors, metadata):
        points = [
             PointStruct(id=str(uuid.uuid4()), vector=vectors[index], payload=metadata[index]) for index in range(len(vectors))
        ]
        return points

    def get_vector_size(self):
        text = 'dummy text'
        embedding = self.get_vectors(text)
        return embedding.shape[0]

    def add_to_db(self, points):
        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=points
        )

    def add_vectors_metadata_to_db(self, chunks):
        vectors = self.get_vectors(chunks['text'])
        vector_size = self.get_vector_size()
        points = self.get_points(vectors, chunks['metadata'])

        self.create_collection(vector_size)
        self.add_to_db(points)