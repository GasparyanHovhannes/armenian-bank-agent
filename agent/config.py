import os

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "secret")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = "armenian_banks"

# CPU mode — no GPU
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE = "int8"
WHISPER_MODEL = "large-v3"

# Armenian ISO code
LANGUAGE = "hy"