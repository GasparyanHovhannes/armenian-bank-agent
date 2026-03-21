from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import os

class ArmenianBankRAG:
    def __init__(self):
        self.embedder = SentenceTransformer(
            "intfloat/multilingual-e5-large"
        )
        self.client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333"))
        )
        self.collection = "armenian_banks"

    async def retrieve(self, query: str, top_k: int = 5) -> str:
        query_vector = self.embedder.encode(
            f"query: {query}"
        ).tolist()

        # Filter to only ACBA Bank which has real data
        results = self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            limit=top_k,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="bank",
                        match=MatchValue(value="ACBA Bank")
                    )
                ]
            )
        ).points

        if not results:
            return "No relevant information found."

        context_parts = []
        for r in results:
            bank = r.payload.get("bank", "Unknown bank")
            topic = r.payload.get("topic", "")
            text = r.payload.get("text", "")
            context_parts.append(f"[{bank} — {topic}]\n{text}")

        return "\n\n".join(context_parts)