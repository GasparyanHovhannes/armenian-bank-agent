# Armenian Bank Voice AI Agent

A voice AI customer support agent for Armenian banks built with LiveKit (open source), OpenAI Whisper STT, GPT-4o LLM, and RAG over scraped and manually curated bank data.

## Architecture & Design Decisions

### System Overview

The agent follows a classic voice AI pipeline: the user speaks in Armenian, their speech is transcribed, a RAG-augmented LLM generates an answer grounded in real bank data, and the answer is spoken back in Armenian.
```
User speaks → LiveKit (WebRTC) → Whisper STT → RAG retrieval → GPT-4o → OpenAI TTS → User hears answer
```

### Why LiveKit (open source, self-hosted)?

The project requirement specifies the open-source LiveKit framework without LiveKit Cloud. LiveKit handles real-time audio transport using WebRTC — the same protocol behind Google Meet and Zoom. Self-hosting means zero per-minute costs and full data control. The Python SDK (`livekit-agents`) provides a clean pipeline abstraction for STT, LLM, and TTS components.

### Why OpenAI Whisper API for STT?

Armenian is a low-resource language with limited ASR support. Whisper is trained on 680,000 hours of multilingual audio and explicitly supports Armenian (`hy` language code). We use the API version rather than local Whisper because it delivers significantly better accuracy on CPU hardware — local Whisper on CPU is too slow for real-time conversation.

### Why GPT-4o for LLM?

GPT-4o has the strongest Armenian language understanding among available LLMs. More importantly, it follows strict system prompt instructions reliably — critical for enforcing RAG grounding (answering only from provided context) and topic restriction (credits, deposits, branches only). Smaller models tend to ignore these constraints and hallucinate.

### Why RAG instead of fine-tuning?

RAG (Retrieval Augmented Generation) is the right choice here for three reasons. First, bank data changes frequently — deposit rates and branch hours update regularly. With RAG you update the data file and re-ingest; with fine-tuning you retrain the model. Second, RAG is transparent — you can see exactly what context the LLM used. Third, RAG scales easily to new banks — just add data, no model changes needed.

### Why multilingual-e5-large for embeddings?

This model from Intel/Microsoft is trained on 100+ languages including Armenian and produces 1024-dimensional vectors that capture semantic meaning across languages. This means a user asking "what are the loan rates?" in Armenian will match chunks about loan rates even if the chunk text is in English — critical since our bank data is in English.

### Why Qdrant for vector database?

Qdrant is open-source, self-hostable via Docker, and purpose-built for vector similarity search. It supports filtering by metadata (bank name, topic) which allows precise retrieval. ChromaDB was considered but Qdrant has better performance at scale and a cleaner Python API.

### Why OpenAI TTS?

Armenian TTS is an extremely limited field. Meta's MMS-TTS supports Armenian but requires HuggingFace authentication and produces lower quality output. OpenAI TTS (alloy voice) produces natural-sounding Armenian speech with no additional setup, leveraging the same API key already used for Whisper and GPT-4o.

### Data Pipeline

Bank knowledge is built from two sources merged together:

- `data/scraped/` — raw data scraped from bank websites using Selenium
- `data/manual/` — manually curated, verified data for accurate financial information

The merge script (`ingest/merge_data.py`) filters out low-quality scraped chunks and combines them with manual data into `data/merged/all_banks.json`, which is then embedded and stored in Qdrant.

## Banks Covered

- ACBA Bank — Credits, Deposits, Branch Locations
- Evocabank — Credits, Deposits, Branch Locations
- Ardshinbank — Credits, Deposits, Branch Locations

## Model Choice Summary

| Component | Model | Why |
|---|---|---|
| STT | OpenAI Whisper API | Best Armenian ASR, native `hy` support, fast via API |
| LLM | GPT-4o | Best Armenian reasoning, strict RAG instruction-following |
| TTS | OpenAI TTS (alloy) | Best available Armenian TTS, no extra setup |
| Embeddings | multilingual-e5-large | 100+ languages including Armenian, strong semantic search |
| Vector DB | Qdrant | Open-source, self-hostable, fast cosine similarity search |
| Transport | LiveKit OSS | Open-source WebRTC, fully self-hosted, Python SDK |

## Prerequisites

- Python 3.11+
- Docker Desktop — download from https://www.docker.com/products/docker-desktop
- OpenAI API key — you need a paid OpenAI account with at least $5 of credits. Get your key at https://platform.openai.com/api-keys and set up billing at https://platform.openai.com/settings/billing/overview
- `lk.exe` — download from https://github.com/livekit/livekit-cli/releases/latest, get `lk_windows_amd64.zip`, unzip and place `lk.exe` in the project root folder

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/GasparyanHovhannes/armenian-bank-agent.git
cd armenian-bank-agent
```

### 2. Create your `.env` file
```bash
cp .env.example .env
```
Open `.env` and replace `your_openai_api_key_here` with your real OpenAI API key from https://platform.openai.com/api-keys. Make sure your account has billing set up and at least $5 of credits at https://platform.openai.com/settings/billing/overview.

### 3. Create virtual environment and install dependencies
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Start Docker services
```bash
docker run -d --name livekit-server -p 7880:7880 -p 7881:7881 -p 7882:7882/udp -e LIVEKIT_KEYS="devkey: secret" livekit/livekit-server --dev
docker run -d --name qdrant -p 6333:6333 -v C:/qdrant_storage:/qdrant/storage qdrant/qdrant
```

### 5. Ingest bank data into Qdrant
> Merged bank data is already included in `data/merged/`. No scraping needed.
```bash
python ingest/ingest.py
```

### 6. Start the agent
```bash
python agent/main.py start
```

### 7. Generate a token
```bash
.\lk.exe token create --api-key devkey --api-secret secret --join --room test-room --identity user1
```

### 8. Connect and test
Open **https://agents-playground.livekit.io** and enter:
- **LiveKit URL**: `ws://localhost:7880`
- **Token**: paste the generated token

Speak in Armenian and ask about credits, deposits, or branch locations!

## Guardrails

The agent strictly answers only questions about:
- Credits / Loans
- Deposits
- Branch Locations

All answers are grounded exclusively in the bank knowledge base via RAG. Off-topic questions receive a polite refusal in Armenian. The agent never uses outside knowledge — only the provided bank data.

## Scalability — Adding a New Bank

The system is designed to scale to any number of banks with minimal effort. To add a new bank:

**Step 1 — Add bank data to `data/manual/all_banks.json`:**
```json
{
  "bank": "NewBank",
  "topic": "deposits",
  "url": "https://newbank.am/deposits",
  "text": "NewBank deposit rates and terms..."
},
{
  "bank": "NewBank",
  "topic": "credits",
  "url": "https://newbank.am/loans",
  "text": "NewBank loan products and rates..."
},
{
  "bank": "NewBank",
  "topic": "branches",
  "url": "https://newbank.am/branches",
  "text": "NewBank branch locations and contact info..."
}
```

**Step 2 — Re-run the merge and ingestion:**
```bash
python ingest/merge_data.py
python -c "from qdrant_client import QdrantClient; QdrantClient(host='localhost', port=6333).delete_collection('armenian_banks'); print('Deleted')"
python ingest/ingest.py
```

**Step 3 — Restart the agent.** No other code changes needed. The agent greeting automatically reads bank names from the data file, so it will mention the new bank without any manual updates.
