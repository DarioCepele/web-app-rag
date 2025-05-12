import os
import json
import requests
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchField,
    VectorSearch, HnswAlgorithmConfiguration, HnswParameters,
    VectorSearchAlgorithmKind, VectorSearchAlgorithmMetric, VectorSearchProfile, SearchFieldDataType
)
from azure.storage.blob import BlobServiceClient

load_dotenv()
search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
search_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")

credential = AzureKeyCredential(search_api_key)
index_client = SearchIndexClient(endpoint=search_endpoint, credential=credential)
search_client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=credential)

vector_search = VectorSearch(
    algorithms=[
        HnswAlgorithmConfiguration(
            name="myHnsw",
            kind=VectorSearchAlgorithmKind.HNSW,
            parameters=HnswParameters(
                m=4,
                ef_construction=400,
                ef_search=500,
                metric=VectorSearchAlgorithmMetric.COSINE,
            )
        )
    ],
    profiles=[
        VectorSearchProfile(
            name="myHnswProfile",
            algorithm_configuration_name="myHnsw",
        )
    ]
)

fields = [
    SimpleField(name="id", type="Edm.String", key=True),
    SearchableField(name="DocumentName", type="Edm.String", sortable=True, filterable=True),
    SimpleField(name="chunk_id", type="Edm.Int32", filterable=True),
    SearchableField(name="content", type="Edm.String", analyzer_name="en.microsoft"),
    SearchableField(name="DocumentCreationTimestamp", type="Edm.DateTimeOffset", filterable=True, sortable=True),
    SearchField(
        name="embedding",
        type="Collection(Edm.Single)",
        searchable=True,
        hidden=False,
        vector_search_dimensions=1536,
        vector_search_profile_name="myHnswProfile" 
    )
]

def create_index():
    try:
        index_client.delete_index(index_name)
        print(f"Indice {index_name} eliminato")
    except:
        pass
    
    index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)
    index_client.create_index(index)
    print(f"Indice {index_name} creato con successo")

def load_and_upload_documents(blob_connection_string, container_name, search_client, batch_size=1000):
    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    blobs = container_client.list_blobs()
    json_blobs = [blob for blob in blobs if blob.name.endswith('.json')]

    print(f"Trovati {len(json_blobs)} file JSON nel container")

    for blob in json_blobs:
        blob_client = container_client.get_blob_client(blob.name)
        response = blob_client.download_blob()
        chunks = json.loads(response.readall())
        print(f"Caricati {len(chunks)} documenti da {blob.name}")

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            result = search_client.upload_documents(documents=batch)
            print(f"Caricati {len(result)} documenti nel batch {i // batch_size + 1}")
