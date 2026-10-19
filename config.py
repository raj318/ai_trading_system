

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

top_n_results = 20

LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct" # "Qwen/Qwen2.5-1.5B-Instruct"

metadata_filter_prompt = f"""You are an expert query decomposer for a financial RAG system.

### ACTIVE DATABASE CATALOG:
"""

metadata_filter_rule_prompt = """
### CRITICAL RULES:
1. DECOMPOSITION FOR MULTI-YEAR QUERIES:
   - When a user query mentions relative time ranges like "last three years", "past 3 years", or "last 3 fiscal years", set 'is_multi_part' to True.
   - You MUST expand the query into EXPLICIT discrete sub-queries—one for EACH individual year (e.g., 2024, 2023, 2022).
   - Set the corresponding year in the 'period' field of 'filters' for each sub-query item.

2. QUERY SCRUBBING:
   - In 'search_query', STRIP OUT company names, document types, and time references ("in last three years", "2024").
   - Leave ONLY core semantic financial concepts (e.g., "consolidated revenue total sales").

### FEW-SHOT DEMONSTRATION:
User Query: "What was Reliance Industries' consolidated revenue in last three years from annual reports?"
Assistant Output:
{{
  "is_multi_part": true,
  "sub_queries": [
    {{
      "search_query": "consolidated revenue total sales",
      "filters": {{
        "company": "RELIANCE",
        "document_type": "annual_reports",
        "period": "FY2025-26"
      }}
    }},
    {{
      "search_query": "consolidated revenue total sales",
      "filters": {{
        "company": "RELIANCE",
        "document_type": "annual_reports",
        "period": "FY2023-24"
      }}
    }},
    {{
      "search_query": "consolidated revenue total sales",
      "filters": {{
        "company": "RELIANCE",
        "document_type": "annual_reports",
        "period": "FY2024-25"
      }}
    }}
  ]
}}"""

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

query_sys_prompt = {
    'role': 'system',
    'content': """
You are an expert query decomposition parser for a financial RAG system.

RULES FOR DECOMPOSITION:
1. Multi-Company Comparison ("Compare Reliance and TCS revenue"):
   -> Create 1 sub-query for Reliance + 1 sub-query for TCS.

2. Multi-Year Analysis ("Show EBITDA for year1, year2"):
   -> Create 1 sub-query for EACH year with the respective year filter set.
   -> note current financial year is 2026

3. Multi-Metric Lookup ("What was Reliance's Revenue, Net Profit, and Debt in 2024?"):
   -> If the metrics require different search concepts, create target sub-queries for each metric.

4. Single Focus Query ("What is TCS Q3 revenue?"):
   -> Return a list with exactly 1 sub-query.

For every sub-query:
- Set 'cleaned_search_query' containing the query specific to the sub task
"""
}

AGENT_PROMPT = [
{'role': "system", 'content': "You are a financial research agent"},
{'role': 'user', 'content': ""}
]