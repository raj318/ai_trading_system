from lib.docling_lib import PDFParser
from pathlib import Path

from src import config
from lib import utils

class Parser():
    def __init__(self, doc_details):
        self.doc_details = doc_details
        self.document_path = doc_details['local_path']
        print(f"doc path = {self.document_path}")
        self.pdf = PDFParser()

    def get_json_path(self):
        company = self.doc_details['company']
        doc_type = self.doc_details['document_type']
        file_name = Path(self.document_path).stem + '.json'
        print(f"doc type = {doc_type}")
        return f"{config.processed_docs_dir}/{company}/{doc_type}/{file_name}"

    def file_already_exists(self, parsed_json):
        return utils.valid_document(parsed_json)

    def create_missing_folders(self, document_path):
        file_path = Path(document_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

    def extract_content_to_json(self, reset=False):
        if utils.valid_document(document_path=self.document_path):
            json_file_path = self.get_json_path()
            if not reset and self.file_already_exists(json_file_path):
                return json_file_path

            self.create_missing_folders(self.document_path)
            status = self.pdf.copy_pdf_content_to_json(
                    self.document_path,
                    json_file_path
                )
            if status:
                return json_file_path
        else:
            print(f"{self.document_path} does not exists")
            return None