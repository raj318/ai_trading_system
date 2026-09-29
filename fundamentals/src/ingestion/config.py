

RAW_DOCUMENT_DETAILS = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/docs/raw/documents.csv'

documents_path = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/docs/raw/documents.csv'
processed_docs_dir = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/docs/processed'
db_file_path = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/db/sqlite/rag_doc_status.db'
csv_keys_for_metadata = ['document_id', 'company', 'document_type', 'title', 'period']
status_db_table_name = 'fundamentals'
document_status = {
    'unprocessed': "UNPROCESSED",
    'parsed': 'PARSED',
    'chunked': 'CHUNKED',
    'vectoried': 'VECTORED',
    'completed': 'COMPLETED'
}
doc_status_list = ['UNPROCESSED', 'PARSED', 'CHUNKED', 'VECTORIED', 'COMPLETED']

sentence_transformer = "sentence-transformers/all-MiniLM-L6-v2"
vector_size = 384 # if seneten-transofmer model is changes vector size needs to be updated accordingly

db_dir = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/db/vectordb/fundamentals_db'
db_collections = "annual_reports"
