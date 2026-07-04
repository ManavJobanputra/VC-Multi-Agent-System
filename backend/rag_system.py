from chroma_manager import ChromaManager
from mistral_client import MistralClient
from typing import List, Dict


class RAGSystem:
    def __init__(self, chroma_manager: ChromaManager, mistral_client: MistralClient):
        self.chroma_manager = chroma_manager
        self.mistral_client = mistral_client

    def retrieve_and_generate(self, query: str, conversation_history: List[Dict]) -> str:
        # Retrieve relevant documents from Chroma
        retrieved_docs = self.chroma_manager.search(query)

        context = ""
        if retrieved_docs:
            context = "\n\nRelevant Context:\n" + "\n".join([doc['payload'].get('content', '') for doc in retrieved_docs])

        # Combine conversation history, query, and retrieved context
        messages = conversation_history + [
            {"role": "user", "content": query + context}
        ]

        # Generate response using OpenRouter
        response = self.mistral_client.call_openrouter_api(messages)
        return response


