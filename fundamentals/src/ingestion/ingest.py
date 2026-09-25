import utils
from extract_docs import ExtractPDF

def get_raw_document_details(documents_df):
    for document in documents_df.to_dict(orient='records'):
        yield document

def main():

    pdf_extractor = ExtractPDF()
    raw_documents = utils.load_raw_documents_to_pandas()

    for doc_details in get_raw_document_details(raw_documents):
        pdf_extractor.markdown(doc_details['local_path'])


if __name__ == "__main__":
    main()