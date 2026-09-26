import utils
from extract_docs import IngestPDF

def get_raw_document_details(documents_df):
    for document in documents_df.to_dict(orient='records'):
        yield document

def main():

    pdf_ingestion = IngestPDF()
    raw_documents = utils.load_raw_documents_to_pandas()

    for doc_details in get_raw_document_details(raw_documents):
        pdf_ingestion.add_to_db(doc_details['local_path'], doc_details)


if __name__ == "__main__":
    main()