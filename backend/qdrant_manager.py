from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import os
import torch
import logging
from uuid import uuid4
from config import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION

logger = logging.getLogger(__name__)

class QdrantManager:
    def __init__(self, collection_name=None):
        self.collection_name = collection_name or QDRANT_COLLECTION

        # Use environment variables, fallback to local instance
        primary_url = QDRANT_URL
        primary_key = QDRANT_API_KEY if QDRANT_API_KEY else None
        fallback_url = "http://localhost:6333"

        self.client, self.qdrant_url = self._init_client(primary_url, primary_key, fallback_url)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2").to(self.device)
        logger.info(f"SentenceTransformer loaded on device: {self.device}")
        self._create_collection_if_not_exists()

    def _init_client(self, primary_url: str, primary_key: str, fallback_url: str):
        try:
            client = QdrantClient(url=primary_url, api_key=primary_key)
            client.get_collections()  # Smoke test
            logger.info(f"Connected to Qdrant at {primary_url}")
            return client, primary_url
        except Exception as e:
            logger.error(f"Primary Qdrant endpoint forbidden/unavailable ({primary_url}): {e}. Falling back to local {fallback_url} (no auth).")
            client = QdrantClient(url=fallback_url)
            return client, fallback_url

    def _create_collection_if_not_exists(self):
        try:
            collections = self.client.get_collections().collections
            if self.collection_name not in [c.name for c in collections]:
                self.client.recreate_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(size=self.encoder.get_sentence_embedding_dimension(), distance=models.Distance.COSINE),
                )
                logger.info(f"Collection \'{self.collection_name}\' created.")
            else:
                logger.info(f"Collection \'{self.collection_name}\' already exists.")
        except Exception as e:
            logger.error(f"Error creating/checking collection \'{self.collection_name}\' at {self.qdrant_url}: {e}")

    def upsert_data(self, texts: list[str], metadatas: list[dict]):
        points = []
        try:
            for i, text in enumerate(texts):
                points.append(
                    models.PointStruct(
                        id=str(uuid4()),
                        vector=self.encoder.encode(text).tolist(),
                        payload=metadatas[i]
                    )
                )
            self.client.upsert(
                collection_name=self.collection_name,
                wait=True,
                points=points
            )
            logger.info(f"Upserted {len(texts)} points to \'{self.collection_name}\' at {self.qdrant_url}.")
        except Exception as e:
            logger.error(f"Error upserting data to \'{self.collection_name}\' at {self.qdrant_url}: {e}")

    def search(self, query_text: str, limit: int = 5, session_filter: str = None) -> list[dict]:
        try:
            query_vector = self.encoder.encode(query_text).tolist()
            
            # Add session filter if provided
            query_filter = None
            if session_filter:
                query_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="session_id",
                            match=models.MatchValue(value=session_filter)
                        )
                    ]
                )
            
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=query_filter
            )
            logger.info(f"Found {len(search_result)} results for query: '{query_text}' (session: {session_filter}) from {self.qdrant_url}")
            return [{"payload": hit.payload, "score": hit.score} for hit in search_result]
        except Exception as e:
            logger.error(f"Error searching collection \'{self.collection_name}\' at {self.qdrant_url}: {e}")
            return []