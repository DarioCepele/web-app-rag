import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

load_dotenv()

blob_string = os.getenv("BLOB_CONNECTION_STRING")

def upload_files_to_blob(container_name, local_folder_path="./data"):
    # account_url = os.getenv("BLOB_ACCOUNT_URL")
    
    blob_service_client = BlobServiceClient.from_connection_string(blob_string)
    container_client = blob_service_client.get_container_client(container_name)

    container_client = blob_service_client.get_container_client(container_name)
    try:
        container_client.get_container_properties()
    except Exception:
        print(f"Il container '{container_name}' non esiste. Lo creo.")
        container_client.create_container()

    for root, dirs, files in os.walk(local_folder_path):
        for filename in files:
            local_file_path = os.path.join(root, filename)
            blob_name = filename
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)

            print(f"Carico: {filename}")
            with open(local_file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)

    print("Upload completato")