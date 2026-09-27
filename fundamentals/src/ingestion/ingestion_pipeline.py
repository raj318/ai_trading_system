from lib import utils
from lib import status_sqlite_db, parser, chunker, embeddings, db_handler

import config

def main():

    status_db = status_sqlite_db.DocStatus(db_path=config.db_file_path,  table_name=config.status_db_table_name)

    raw_documents = utils.load_raw_documents_to_pandas(config.documents_path)

    for doc_details in utils.get_raw_document_details(raw_documents):
        doc_metadata_dict = utils.get_document_fields_for_hash(doc_details, config.csv_keys_for_metadata)
        doc_hash = status_db.get_hash_string(doc_metadata_dict)
        if status_db.is_document_exists(doc_hash):
            print(f"document exists in DB")
            doc_status = status_db.get_status(doc_hash)
            if doc_status == 'COMPLETED':
                print(f"Document processed fully")
                continue
            
        status_db.update_status(doc_hash, config.doc_status_list[0])
        print(f"updated status to {config.doc_status_list[0]}")

        parser_obj = parser.Parser(doc_details)
        doc_json = parser_obj.extract_content_to_json()
        if not doc_json:
            print(f"Parinsng {doc_details['local_path']} Failed!!!!!")
            continue
        status_db.update_status(doc_hash, config.doc_status_list[1])
        print(f"updated status to {config.doc_status_list[1]}")

        chunker_obj = chunker.PDFChunker(doc_details, doc_json) 
        doc_chunk = chunker_obj.create_and_save_chunks()
        if not doc_chunk:
            print(f"chunking {doc_details['local_path']} Failed!!")
            continue
        status_db.update_status(doc_hash, config.doc_status_list[2])
        print(f"updated status to {config.doc_status_list[2]}")

        embed_obj = embeddings.Embedder(doc_chunk, doc_details)
        vectors_file_path = embed_obj.generate_vectors()

        if not vectors_file_path:
            print(f"vectors {doc_details['local_path']} Failed!")
            continue
        status_db.update_status(doc_hash, config.doc_status_list[3])
        print(f"updated status to {config.doc_status_list[3]}")

        q_db = db_handler.db_helper(vectors_file_path, doc_details)
        q_db.save_to_db()

        status_db.update_status(doc_hash, config.doc_status_list[4])


if __name__ == "__main__":
    main()