
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, FilterSelector, Filter

class DB():
    def __init__(self, db_file, collection_name):
        self.db_file = db_file # '/Users/raj/Documents/personal/ai_trading_system/fundamentals/db/vectordb/fundamentals_db'
        self.collection_name = collection_name
        self.create_db_instance()
        print("db instance is opened!")

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

    def delete_all(self):
        self.qdrant.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(filter=Filter())
        )

    def add_to_db(self, points):
        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=points
        )

    def add_vectors_metadata_to_db(self, vector_size, points):
        self.create_collection(vector_size)
        print(f"created collection in qdrant")
        self.add_to_db(points)
        print(f"updated data based with points generated")

    def search(self, query_vector, qdrant_filters=None, top_n=None):
        return self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=qdrant_filters,
            limit=top_n,
            with_payload=True
        )

    def close(self):
        print("db is trying to get closed!")
        if self.qdrant:
            self.qdrant.close()
            print("db is closed!")

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("closing at the exit!")
        self.close()
        