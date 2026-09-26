from docling.document_converter import DocumentConverter
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.settings import settings
from docling.chunking import HybridChunker
from docling_core.types.doc import DoclingDocument
from pathlib import Path
from typing import List, Dict, Any, Set
from vector_embeddings import Vembeddings

import os


class ExtractPDF():
    """class to parse the document and extract symantic content
        uses docling, supports PDF documents
    """
    def __init__(self):
        self.docling_pdf_content = None
        self.set_gpu_pipeline()
        self.initiate_pdf_convertor()

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
        if os.path.exists(document_path):
            return True
        return False

    def convert(self, document_path):
        if self.valid_document(document_path):
            self.docling_pdf_content = self.convertor.convert(document_path)
        self.print_timings()

    def print_timings(self):
        for name, timing in self.docling_pdf_content.timings.items():
            print(name, timing)

    def markdown(self, document_path):
        self.convert(document_path)
        return self.docling_pdf_content.document.export_to_markdown()

    def dump_to_json(self, f_path):
        self.convert(f_path)
        self.docling_pdf_content.document.save_as_json(f_path)

    def print_markdown(self, document_path):
        print(self.markdown(document_path))

    def get_chunks_with_metadata(self, document_path):
        self.convert(document_path)
        self.create_chunks()
        self.extract_text_from_chunks()
        self.extract_metadata_from_chunks(document_path)

        return {"text": self.text_chunks, 'metadata': self.chunk_metadata}

    def create_chunks(self, max_tokens=512):
        if not self.docling_pdf_content:
            print(f"Pdf document data is not extracted yet! call conver(document_path) first!")
            return None
        chunker = HybridChunker(
                    max_tokens=max_tokens,
                    merge_peers=True
                )
    
        self.chunks = list(chunker.chunk(self.docling_pdf_content.document))

    def extract_text_from_chunks(self):
        self.text_chunks = []
        for chunk in self.chunks:
            self.text_chunks.append(chunk.text)

    def extract_metadata_from_chunks(self, document_path):
        self.chunk_metadata = []
        index = 1
        for chunk in self.chunks:
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
                "char_count": len(chunk.text),
                "text": chunk.text
            }

            self.chunk_metadata.append(metadata)
            index +=1

    
class IngestPDF():
    def __init__(self, ):
        db_dir = '/Users/raj/Documents/personal/ai_trading_system/fundamentals/vectordb/fundamentals_db'
        db_collections = "annual_reports"
        self.pdf_extractor = ExtractPDF()
        self.db = Vembeddings(db_dir, db_collections)

    def update_document_metadata(self, data, doc_metadata):
        update_metadata = []
        for each_chunk in data['metadata']:
            for each_key in doc_metadata:
                each_chunk[f"doc_{each_key}"] = doc_metadata[each_key]
            # update_metadata.append(each_chunk)
        return data

    def add_to_db(self, document_path, document_metadata):
        data = self.pdf_extractor.get_chunks_with_metadata(document_path)
        updated_data = self.update_document_metadata(data, document_metadata)
        self.db.add_vectors_metadata_to_db(updated_data)