from src.retreival.services import llm
from src import config
from src.storage import metadata_models
import json
import ast

class MetadataFiltering():
    def __init__(self, llm_model):
        self.llm_model = llm_model

    def get_metadata_filters(self, query):
        # print(f"metdata filter qyuery = {query}")
        catelogue = self.get_catelogue_data()
        catelogue_schema = metadata_models.build_schema(catelogue)
        llm_response = self.llm_model.get_metadata_filter_response(query, catelogue_schema)
        # print(f"llm response = {llm_response}")
        parsed_response = metadata_models.QueryIntent.model_validate_json(llm_response)
        # print(f"parsed response = {parsed_response}")
        qdrant_filters = self.get_qdrant_filters(parsed_response.filters)
        # print(f"qdrant filters = {qdrant_filters}")
        return qdrant_filters

    def get_qdrant_filters(self, filters):
        return metadata_models.get_qdrant_filter(filters)

    def get_catelogue_data(self):
        cat_file_path = self.get_catelog_file_path()
        return self.load_json(cat_file_path)
        
    def get_catelog_file_path(self):
        return f"{config.processed_docs_dir}/metadata_catelogue.json"

    def load_json(self, document_path):
        with open(document_path, 'r', encoding='utf-8') as fd:
            data = json.load(fd)
        return data

