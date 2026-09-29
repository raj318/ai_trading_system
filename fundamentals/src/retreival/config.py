sentence_transformer = "sentence-transformers/all-MiniLM-L6-v2"
vector_size = 384 # if seneten-transofmer model is changes vector size needs to be updated accordingly

db_dir = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/db/vectordb/fundamentals_db'
db_collections = "annual_reports"
top_n_results = 10


LLM_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"

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