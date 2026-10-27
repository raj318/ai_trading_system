import hashlib
from datetime import datetime
from sqlite_utils import Database
from sqlite_utils.db import NotFoundError

db_file_path = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/db/sqlite/rag_doc_status.db'

class DocStatus():
    def __init__(self, db_path, table_name='fundamentals'):
        self.db_path = db_path
        self.db = Database(self.db_path)
        self.table_name = table_name

    @staticmethod
    def get_hash_string(file_metadata_dict):
        hasher = hashlib.sha256()
        metadata_string = str(file_metadata_dict)
        hasher.update(metadata_string.encode("utf-8"))
        return hasher.hexdigest()
    
    def update_status(self, hash_string, status):
        payload = {
            "id": hash_string,
            'status': status,
            'updated_time': datetime.utcnow().isoformat()
        }

        self.db[self.table_name].upsert(payload, pk='id')

    def is_document_exists(self, hash_string):
        if self.table_name not in self.db.table_names():
            return False

        try:
            self.db[self.table_name].get(hash_string)
            return True
        except NotFoundError:
            return False

    def get_status(self, hash_string):
        if self.table_name not in self.db.table_names():
            return None
        try:
            self.db[self.table_name].get(hash_string)
            return self.db[self.table_name].get(hash_string).get('status')
        except NotFoundError:
            return None