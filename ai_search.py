from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from langchain.docstore.document import Document
from azure.search.documents.models import VectorizedQuery
import logging

class CognitiveSearch:
    def __init__(self, embedding_model, endpoint, query_key, index_name, fields=[]):
        self.embedding_model = embedding_model
        self.index_name = index_name
        self.search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(query_key),
        )
        self.fields = fields

    def generate_embeddings(self, text: str) -> list:
        return self.embedding_model.embed_query(text)

    def query_index(
        self,
        query: str = None,
        search_text: str = None,
        top_k: int = 4,
        filter: str = None,
        order_by: str = None,
        select: str = None,
        vector_fields: str = "embedding",
        content: str = "content",
        doc_name: str = "DocumentName"
    ):
        try:
            results = self.search_client.search(
                search_text=query,
                vector_queries=[
                    VectorizedQuery(
                        vector=self.generate_embeddings(query),
                        k_nearest_neighbors=top_k,
                        fields=vector_fields,
                    )
                ],
                filter=filter,
                top=top_k,
                order_by=order_by,
                select=select,
            )

            docs = [
                Document(
                    page_content=result[content],
                    metadata={"DocumentName": result[doc_name]},
                )
                for result in results
            ]
            return docs

        except Exception as e:
            logging.error("Vector search error: %s", str(e))
            return []
