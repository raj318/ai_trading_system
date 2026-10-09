

RAW_DOCUMENT_DETAILS = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/docs/raw/documents.csv'

documents_path = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/docs/raw/documents.csv'
processed_docs_dir = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/docs/processed'
db_file_path = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/db/sqlite/rag_doc_status.db'
catelogue_path = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/docs/processed/metadata_catelogue.json'
csv_keys_for_metadata = ['company', 'document_type', 'title', 'period']
csv_keys_for_hashing = ['document_id', 'company', 'document_type', 'title', 'period']
metadata_keys_for_catalogue = ['company', 'document_type', 'period']
status_db_table_name = 'fundamentals'
document_status = {
    'unprocessed': "UNPROCESSED",
    'parsed': 'PARSED',
    'chunked': 'CHUNKED',
    'vectoried': 'VECTORED',
    'completed': 'COMPLETED'
}
doc_status_list = ['UNPROCESSED', 'PARSED', 'CHUNKED', 'VECTORIED', 'COMPLETED']

chunk_size = 512

sentence_transformer = "sentence-transformers/all-MiniLM-L6-v2"
reranker_model = 'cross-encoder/ms-marco-MiniLM-L-6-v2'
vector_size = 384 # if seneten-transofmer model is changes vector size needs to be updated accordingly


db_dir = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/db/vectordb/fundamentals_db'
db_collections = "annual_reports"

top_n_results = 10


LLM_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"

metadata_filter_prompt = f"""You are an intent parser for a financial vector database.
Convert the user question into a clean search query and structured metadata filters.

Catalog Context (Valid values currently in DB):"""

metadata_filter_rule_prompt = """Rules:
1. Strip filter/metadata terms (e.g. company names, years, categories) from `search_query` so vector search remains focused purely on semantic context.
2. Only populate filter fields if they match or strongly map to the allowed catalog values above. Leave unmentioned fields as null.
"""

CONTEXT = {
    'role': 'system',
    'content': "You are a precise financial analysis assistant. "
                "Answer the user's question relying strictly on "
                "the provided context below. "
                "If the context does not contain the answer, "
                "say 'Information not found in document.' "
                "Do not invent facts."
}
USER_QUARY = {
    "role": "user",
    "content": ""
}
