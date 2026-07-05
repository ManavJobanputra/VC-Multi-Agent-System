import json
import logging
from uuid import uuid4

import torch
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

from config import PINECONE_API_KEY, PINECONE_INDEX_NAME, PINECONE_CLOUD, PINECONE_REGION

logger = logging.getLogger(__name__)

# Output size of all-MiniLM-L6-v2, the embedding model used throughout
# this app - must match the index's configured dimension exactly.
EMBEDDING_DIMENSION = 384


def _sanitize_metadata(metadata: dict) -> dict:
    """Pinecone metadata values must be string/number/bool/list-of-strings.
    Drop Nones and JSON-encode anything else (dicts/lists) so arbitrary
    payloads survive, same approach used for the prior Chroma migration."""
    sanitized = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            sanitized[key] = value
        else:
            sanitized[key] = json.dumps(value)
    return sanitized


class PineconeManager:
    """Drop-in replacement for ChromaManager - same upsert_data/search
    interface, backed by a single hosted Pinecone serverless index instead
    of an embedded on-disk Chroma store. Embedded Chroma doesn't survive
    deployment to platforms with ephemeral filesystems; Pinecone is a
    managed service reachable from anywhere.

    `collection_name` is kept as the constructor parameter name for
    compatibility with existing call sites, but now selects a Pinecone
    *namespace* within one shared index rather than a separate Chroma
    collection - namespaces are the idiomatic (and free-tier-friendly)
    way to keep multiple logical collections in Pinecone.
    """

    def __init__(self, collection_name=None):
        self.namespace = collection_name or "vc_pitches"

        self.client = Pinecone(api_key=PINECONE_API_KEY)
        if not self.client.has_index(PINECONE_INDEX_NAME):
            logger.info(f"Creating Pinecone index '{PINECONE_INDEX_NAME}'...")
            self.client.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
            )

        index_host = self.client.describe_index(PINECONE_INDEX_NAME).host
        self.index = self.client.Index(host=index_host)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2").to(self.device)
        logger.info(f"SentenceTransformer loaded on device: {self.device}")
        logger.info(f"Connected to Pinecone index '{PINECONE_INDEX_NAME}', namespace '{self.namespace}'")

    def upsert_data(self, texts: list[str], metadatas: list[dict]):
        try:
            embeddings = self.encoder.encode(texts).tolist()
            vectors = [
                {"id": str(uuid4()), "values": embedding, "metadata": _sanitize_metadata(metadata)}
                for embedding, metadata in zip(embeddings, metadatas)
            ]
            self.index.upsert(vectors=vectors, namespace=self.namespace)
            logger.info(f"Upserted {len(texts)} vectors to namespace '{self.namespace}'.")
        except Exception as e:
            logger.error(f"Error upserting data to namespace '{self.namespace}': {e}")

    def search(self, query_text: str, limit: int = 5, session_filter: str = None) -> list[dict]:
        try:
            query_vector = self.encoder.encode(query_text).tolist()
            metadata_filter = {"session_id": {"$eq": session_filter}} if session_filter else None

            results = self.index.query(
                namespace=self.namespace,
                vector=query_vector,
                top_k=limit,
                filter=metadata_filter,
                include_metadata=True,
            )
            matches = results.matches if hasattr(results, "matches") else results.get("matches", [])

            payloads = []
            for match in matches:
                metadata = getattr(match, "metadata", None) if not isinstance(match, dict) else match.get("metadata")
                score = getattr(match, "score", None) if not isinstance(match, dict) else match.get("score")
                payloads.append({"payload": metadata or {}, "score": score})

            logger.info(
                f"Found {len(payloads)} results for query: '{query_text}' "
                f"(session: {session_filter}) in namespace '{self.namespace}'"
            )
            return payloads
        except Exception as e:
            logger.error(f"Error searching namespace '{self.namespace}': {e}")
            return []
