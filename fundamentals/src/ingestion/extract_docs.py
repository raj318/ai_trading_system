from docling.document_converter import DocumentConverter
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat

import os

class ExtractPDF():
    """class to parse the document and extract symantic content
        uses docling, supports PDF documents
    """
    def __init__(self):
        self.set_gpu_pipeline()
        self.initiate_pdf_convertor()

    def set_gpu_pipeline(self):
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
            return self.convertor.convert(document_path)

    def markdown(self, document_path):
        result = self.convert(document_path)
        result.document.save_as_json('documen_data.json')
        return result.document.export_to_markdown()

    def print_markdown(self, document_path):
        print(self.markdown(document_path))


