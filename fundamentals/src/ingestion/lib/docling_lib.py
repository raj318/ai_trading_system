from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.settings import settings
from docling.chunking import HybridChunker, HierarchicalChunker
from docling_core.types.doc import DoclingDocument
from pathlib import Path
from typing import List, Dict, Any, Set
from src import config

import os
import json
from lib import utils


class PDFParser():
    def __init__(self):
        self.docling_pdf_content = None
        self.set_gpu_pipeline()
        self.initiate_pdf_convertor()
        self.catelogue_data = {}

    def set_gpu_pipeline(self):
        settings.debug.profile_pipeline_timings = True
        acc_option = AcceleratorOptions(
            device=AcceleratorDevice.MPS
        )
        self.pipeline_options = PdfPipelineOptions(
            accelerator_options = acc_option
        )
    def initiate_pdf_convertor(self):
        self.convertor = DocumentConverter(
                        format_options={
                            InputFormat.PDF: PdfFormatOption(pipeline_options=self.pipeline_options)
                        }
                    )

    def valid_document(self, document_path):
            return os.path.exists(document_path)

    def copy_pdf_content_to_json(self, document_path, json_path):
        self.convert(document_path)
        return self.dump_to_json(json_path)

    def convert(self, document_path):
        if self.valid_document(document_path):
            docling_obj = self.convertor.convert(document_path)
            self.docling_pdf_content = docling_obj.document


    def dump_to_json(self, f_path):
        if self.docling_pdf_content:
            self.docling_pdf_content.save_as_json(f_path)
            return True

    def load_docling_json_file(self, docling_json_path):
        json_data = Path(docling_json_path).read_text(encoding='utf-8')
        self.docling_pdf_content = DoclingDocument.model_validate_json(json_data)

    def get_docling_json_file(self, document_path):
        processed_dir = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/docs/processed/reliance/annual_reports'
        file_name = Path(document_path).stem
        file_name = file_name + '.json'
        return f"{processed_dir}/{file_name}"

    def docling_json_file_exists(self, docling_json_path):
        return os.path.exists(docling_json_path)

    def create_chunks(self, max_tokens=512):
        if not self.docling_pdf_content:
            print(f"Pdf document data is not extracted yet! call conver(document_path) first!")
            return None
        print(f"chunk size set {max_tokens}")
        chunker = HybridChunker(
                    max_tokens=max_tokens,
                    merge_peers=True
                )
    
        self.chunks = list(chunker.chunk(self.docling_pdf_content))

    def create_hierarcy_chunks(self, max_tokens=512):
            if not self.docling_pdf_content:
                print(f"Pdf document data is not extracted yet! call conver(document_path) first!")
                return None
            print("Using hierarchical chunking method!")
            chunker = HierarchicalChunker(
                         merge_list_items=True
                    )
        
            self.chunks = list(chunker.chunk(self.docling_pdf_content))

    def extract_text_from_chunks(self):
        self.text_chunks = []
        for chunk in self.chunks:
            self.text_chunks.append(chunk.text)

    def save_chunks(self, chunk_file_path):
        if self.chunk_data:
            with open(chunk_file_path, 'w', encoding='utf-8') as fd:
                json.dump(self.chunk_data, fd, indent=2)
            return chunk_file_path
        return None

    def retrive_chunks_from_json(self, chunk_file_path):
        with open(chunk_file_path, 'r', encoding='utf-8') as fd:
            chunk_data = json.loads(fd)
        return chunk_data

    def get_catelog_file_path(self):
        return f"{config.processed_docs_dir}/metadata_catelogue.json"

    def write_to_json(self, path, dict_content):
        # if utils.valid_document(path):
        utils.save_to_json(path, dict_content)

    def update_values_as_set_data_type(self):
        for item in config.metadata_keys_for_catalogue:
            self.catelogue_data[item] = set(self.catelogue_data[item])

    def update_values_as_list_data_type(self):
        for item in config.metadata_keys_for_catalogue:
            self.catelogue_data[item] = list(self.catelogue_data[item])

    def load_catelogue_file_path(self):
        catelogue_file_path = self.get_catelog_file_path()
        if utils.valid_document(catelogue_file_path):
            self.catelogue_data = utils.load_json(catelogue_file_path)

    def extract_text_and_metdata_from_chunks(self, document_path, doc_details):
        self.load_catelogue_file_path()
        self.update_values_as_set_data_type()
        if not self.catelogue_data:
            for item in config.metadata_keys_for_catalogue:
                self.catelogue_data[item] = set()
        self.chunk_data = []
        index = 1
        for chunk in self.chunks:

            if len(chunk.text.strip()) < 1:
                continue
                  
            headings = getattr(chunk.meta, "headings", [])
            heading_path = " > ".join(headings) if headings else "Root / No Heading"

            doc_items = getattr(chunk.meta, "doc_items", [])

            pages = set()
            element_types = set()
            bounding_boxes = []

            for item in doc_items:
                label = str(getattr(item, "label", "text"))
                element_types.add(label)

                prov_list = getattr(item, "prov", [])
                for prov in prov_list:
                    page_no = getattr(prov, "page_no", None)
                    if page_no is not None:
                        pages.add(page_no)
                    
                    bbox = getattr(prov, "bbox", None)
                    if bbox:
                        bounding_boxes.append({
                            "page_no": page_no,
                            "left": getattr(bbox, "l", 0.0),
                            "top": getattr(bbox, "t", 0.0),
                            "right": getattr(bbox, "r", 0.0),
                            "bottom": getattr(bbox, "b", 0.0)
                        })

            sorted_pages = sorted(list(pages))
            primary_page = sorted_pages[0] if sorted_pages else None

            chunk_id = f"{Path(document_path).name}_id{index:04d}"
            metadata = {
                "chunk_id": chunk_id,
                "filename": Path(document_path).name,
                "heading_path": heading_path,              
                "headings": headings,
                "page_numbers": sorted_pages,                   
                "primary_page": primary_page,                 
                "element_types": sorted(list(element_types)),          
                "has_table": "table" in [t.lower() for t in element_types],
                "has_list": "list_item" in [t.lower() for t in element_types],
                "char_count": len(chunk.text.strip()),
            }

            metadata.update({key: doc_details[key] for key in config.csv_keys_for_metadata})

            for item in config.metadata_keys_for_catalogue:
                if isinstance(metadata[item], str):
                    self.catelogue_data[item].add(metadata[item])
                elif isinstance(metadata[item], list):
                    self.catelogue_data[item].update(metadata[item])
                else:
                    self.catelogue_data[item].add(str(metadata[item]))
        
            self.chunk_data.append({'text': chunk.text, 'metadata':metadata})
            index +=1

        catelog_file_path = self.get_catelog_file_path()
        self.update_values_as_list_data_type()
        self.write_to_json(catelog_file_path, self.catelogue_data)
        print(f"file path = {catelog_file_path}")
