import json
import os
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct
)
from sentence_transformers import SentenceTransformer
import uuid

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = "armenian_banks"
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
VECTOR_SIZE = 1024  # multilingual-e5-large output size
DATA_PATH = "data/scraped/all_banks.json"


def setup_collection(client: QdrantClient):
    """Create the Qdrant collection if it doesn't exist."""
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME in existing:
        print(f"Collection '{COLLECTION_NAME}' already exists — skipping creation.")
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE
        )
    )
    print(f"Created collection '{COLLECTION_NAME}'")


def ingest(data_path: str = DATA_PATH):
    print("Loading embedding model...")
    embedder = SentenceTransformer(EMBEDDING_MODEL)

    print("Connecting to Qdrant...")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    setup_collection(client)

    print(f"Loading scraped data from {data_path}...")
    with open(data_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Embedding and ingesting {len(chunks)} chunks...")
    batch_size = 32
    points = []

    for i, chunk in enumerate(chunks):
        # e5 models need "passage:" prefix for documents
        text_to_embed = f"passage: {chunk['text']}"
        vector = embedder.encode(text_to_embed).tolist()

        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "bank": chunk["bank"],
                "topic": chunk["topic"],
                "url": chunk["url"],
                "text": chunk["text"],
            }
        ))

        # Upload in batches of 32
        if len(points) >= batch_size:
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            points = []
            print(f"  Uploaded {i + 1}/{len(chunks)} chunks...")

    # Upload any remaining
    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)

    print(f"\nIngestion complete. {len(chunks)} chunks stored in Qdrant.")


if __name__ == "__main__":
    ingest()