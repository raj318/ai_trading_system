from lib.docling_lib import PDFParser

from src import config
from lib import utils
from pathlib import Path

class PDFChunker():
    def __init__(self, doc_details, json_file):
        self.json_file = json_file
        self.doc_details = doc_details
        self.pdfparser = PDFParser()

    def get_chunk_file_path(self):
        company = self.doc_details['company']
        doc_type = self.doc_details['document_type']
        document_path = self.doc_details['local_path']
        file_name = Path(document_path).stem + 'chunker.json'
        return f"{config.processed_docs_dir}/{company}/{doc_type}/{file_name}"

    def create_chunks(self):
        self.pdfparser.load_docling_json_file(self.json_file)
        self.pdfparser.create_chunks(max_tokens=config.chunk_size)
        self.pdfparser.extract_text_and_metdata_from_chunks(self.doc_details['local_path'], self.doc_details)

    def save_chunks(self):
        self.create_chunks()
        chunk_file_path = self.get_chunk_file_path()
        return self.pdfparser.save_chunks(chunk_file_path)

    def create_and_save_chunks(self, reset=False):
        chunker_file = self.get_chunk_file_path()
        if not reset and utils.valid_document(chunker_file):
            return chunker_file
        return self.save_chunks()
