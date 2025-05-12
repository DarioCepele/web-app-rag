from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from langchain.text_splitter import RecursiveCharacterTextSplitter
from datetime import datetime, timezone
import json
import os
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings
from llm_manager import LLMClient
import fitz
import concurrent.futures

load_dotenv()

endpoint = os.getenv("DOCUMENTINTELLIGENCE_ENDPOINT")
key = os.getenv("DOCUMENTINTELLIGENCE_API_KEY")

embedding_model_endpoint = os.getenv("EMBEDDING_MODEL_ENDPOINT")
embedding_model_key = os.getenv("EMBEDDING_MODEL_KEY")
azure_deployment= os.getenv("AZURE_DEPLOYMENT")

api_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("API_VERSION")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

embedding_model = AzureOpenAIEmbeddings(
    azure_deployment=azure_deployment,
    azure_endpoint=embedding_model_endpoint,
    api_key=embedding_model_key,
)

llm = LLMClient(
    azure_deployment=azure_openai_deployment,
    azure_endpoint=azure_endpoint,
    api_version=api_version,
    api_key=api_key
)

def process_image(image_path, llm_client):
    """Analizza un'immagine PNG e restituisce la descrizione"""
    try:
        description = llm_client.analayzeImage(image_path)
        return description
    except Exception as e:
        print(f"Errore nell'elaborazione dell'immagine {image_path}: {e}")
        return None

def analyze_and_chunk_pdf(
    file_path: str,
    output_json_path: str = "data/chunks.json",
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    images_folder: str = "data/images",
    max_workers: int = 4
):
    if not os.path.exists(file_path):
        print(f"Errore: Il file {file_path} non esiste.")
        return

    print(f"Estrazione in corso da: {file_path}")
    client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    with open(file_path, "rb") as file:
        poller = client.begin_analyze_document("prebuilt-read", file)
        result = poller.result()

    full_text = result.content
    if not full_text:
        print("Nessun testo trovato nel documento.")
        return
    
    # Assicurati che la directory per le immagini esista
    os.makedirs(images_folder, exist_ok=True)
    
    # Ottimizzazione per l'estrazione e analisi delle immagini
    doc = fitz.open(file_path)
    image_tasks = []
    
    # Raccogliamo tutte le immagini
    for page_num, page in enumerate(doc):
        image_path = os.path.join(images_folder, f"page_{page_num}.png")
        pix = page.get_pixmap()
        pix.save(image_path)
        image_tasks.append((image_path, llm))
    
    # Elaborazione parallela delle immagini
    image_descriptions = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_image, *task) for task in image_tasks]
        for future in concurrent.futures.as_completed(futures):
            description = future.result()
            if description:
                image_descriptions.append(description)
    
    # Chiudi il documento PDF dopo l'uso
    doc.close()

    # Combina il testo e le descrizioni delle immagini
    full_content = full_text
    if image_descriptions:
        full_content += "\n\n" + "\n".join(image_descriptions)
    
    # Suddivisione in chunk
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = splitter.split_text(full_content)
    
    # Creazione dei documenti chunk
    document_name = os.path.basename(file_path)
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')

    chunk_documents = [
        {
            "@search.action": "upload",
            "id": f"id_{i + 1}",
            "DocumentName": document_name,
            "chunk_id": i + 1,
            "content": chunk,
            "DocumentCreationTimestamp": now,
            "embedding": embedding_model.embed_query(chunk)
        }
        for i, chunk in enumerate(chunks)
    ]

    # Salvataggio dei risultati
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(chunk_documents, f, ensure_ascii=False, indent=2)

    print(f"{len(chunks)} chunk salvati in '{output_json_path}'.")
    return chunk_documents