from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import base64
from utils.prompts import SYSTEM_PROMPT

class LLMClient:
    def __init__(self, azure_deployment, azure_endpoint, api_version, api_key):
        self.llm = AzureChatOpenAI(
            azure_deployment=azure_deployment,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            api_key=api_key,
            temperature=0.0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )

    def run(self, query: str, context: str) -> str:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Context:\n{context}\n\nQuery: {query}")
        ]
        return self.llm.invoke(messages).content
    
    def analayzeImage(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode("utf-8")
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe the image in detail for text search."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                ]
            }
        ]
        return self.llm.invoke(messages).content
