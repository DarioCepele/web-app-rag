from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from langchain_openai import AzureOpenAIEmbeddings
from ai_search import CognitiveSearch
from llm_manager import LLMClient

load_dotenv()

api_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("API_VERSION")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

service_endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
search_key = os.getenv("AZURE_SEARCH_API_KEY")

azure_deployment= os.getenv("AZURE_DEPLOYMENT")
embedding_model_endpoint = os.getenv("EMBEDDING_MODEL_ENDPOINT")
embedding_model_key = os.getenv("EMBEDDING_MODEL_KEY")

embedding_model = AzureOpenAIEmbeddings(
    azure_deployment=azure_deployment,
    azure_endpoint=embedding_model_endpoint,
    api_key=embedding_model_key,
)

search = CognitiveSearch(
    embedding_model=embedding_model,
    endpoint=service_endpoint,
    query_key=search_key,
    index_name=index_name
)

llm = LLMClient(
    azure_deployment=azure_openai_deployment,
    azure_endpoint=azure_endpoint,
    api_version=api_version,
    api_key=api_key
)

app = Flask(__name__)
CORS(app)

@app.route("/run_rag_query", methods=["POST"])
def run_rag_query():
    data = request.get_json()
    query = data.get("query")
    top_k = data.get("top_k", 4)
    chat_history = data.get("chat_history", "")

    if not query:
        return jsonify({"error": "Parametro 'query' mancante"}), 400

    docs = search.query_index(query=query, top_k=top_k)
    doc_context = "\n".join([doc.page_content for doc in docs]) or "Nessun contesto trovato."
    full_context = f"{chat_history}\n\nDocument context:\n{doc_context}"
    response = llm.run(query, full_context)
    return jsonify({"response": response})

@app.route("/general", methods=["POST"])
def general():
    data = request.get_json()
    query = data.get("query")
    chat_history = data.get("chat_history", "")
    full_context = f"\nPrevious conversation:\n{chat_history}"

    if not query:
        return jsonify({"error": "Parametro 'query' mancante"}), 400
    
    response = llm.general(query, full_context)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
    