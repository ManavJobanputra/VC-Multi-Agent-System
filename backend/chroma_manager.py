import json
import logging
from uuid import uuid4

import chromadb
import torch
from sentence_transformers import SentenceTransformer

from config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION

logger = logging.getLogger(__name__)


def _sanitize_metadata(metadata: dict) -> dict:
    """Chroma metadata values must be str/int/float/bool. Drop Nones and
    JSON-encode anything else (dicts/lists) so arbitrary payloads survive."""
    sanitized = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
        else:
            sanitized[key] = json.dumps(value)
    return sanitized


class ChromaManager:
    def __init__(self, collection_name=None):
        self.collection_name = collection_name or CHROMA_COLLECTION

        self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2").to(self.device)
        logger.info(f"SentenceTransformer loaded on device: {self.device}")
        logger.info(f"Connected to Chroma collection '{self.collection_name}' at {CHROMA_PERSIST_DIR}")

    def upsert_data(self, texts: list[str], metadatas: list[dict]):
        try:
            ids = [str(uuid4()) for _ in texts]
            embeddings = self.encoder.encode(texts).tolist()
            sanitized_metadatas = [_sanitize_metadata(m) for m in metadatas]
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=sanitized_metadatas,
                documents=texts,
            )
            logger.info(f"Upserted {len(texts)} points to '{self.collection_name}'.")
        except Exception as e:
            logger.error(f"Error upserting data to '{self.collection_name}': {e}")

    def search(self, query_text: str, limit: int = 5, session_filter: str = None) -> list[dict]:
        try:
            query_embedding = self.encoder.encode(query_text).tolist()
            where = {"session_id": session_filter} if session_filter else None

            count = self.collection.count()
            if count == 0:
                return []

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(limit, count),
                where=where,
            )

            metadatas = (results.get("metadatas") or [[]])[0]
            distances = (results.get("distances") or [[]])[0]

            logger.info(
                f"Found {len(metadatas)} results for query: '{query_text}' "
                f"(session: {session_filter}) in '{self.collection_name}'"
            )
            return [
                {"payload": metadata, "score": 1 - distance}
                for metadata, distance in zip(metadatas, distances)
            ]
        except Exception as e:
            logger.error(f"Error searching collection '{self.collection_name}': {e}")
            return []
