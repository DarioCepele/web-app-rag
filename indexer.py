from analyze_and_chuck import analyze_and_chunk_pdf
from blob_storage import upload_files_to_blob
from create_index import create_index, load_and_upload_documents
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv

load_dotenv()
blob_url = os.getenv("BLOB_URL")
search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
search_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
blob_connection_string = os.getenv("BLOB_CONNECTION_STRING")
container_name = os.getenv("BLOB_CONTAINER_NAME")

pdf_path = "documents/bcg-travel.pdf"
json_path = "data/chunks.json"

credential = AzureKeyCredential(search_api_key)
search_client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=credential)

if __name__ == "__main__":
    print("1. Estrazione e chunking del documento...")
    analyze_and_chunk_pdf(pdf_path, output_json_path=json_path)

    print("\n2. Upload dei chunk su Azure Blob Storage...")
    upload_files_to_blob(container_name, local_folder_path="./data")

    print("\n3. Creazione dell'indice e indicizzazione dei documenti...")
    create_index()
    load_and_upload_documents(blob_connection_string, container_name, search_client)

    print("\nPipeline completata con successo!")
