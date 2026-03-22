# Armenian Bank Voice AI Agent

A voice AI customer support agent for Armenian banks built with LiveKit (open source), OpenAI Whisper STT, GPT-4o LLM, and RAG over scraped and manually curated bank data.

## Architecture

- **STT**: OpenAI Whisper API (Armenian language `hy`)
- **LLM**: GPT-4o with RAG grounding — answers only from bank knowledge base
- **TTS**: OpenAI TTS (`tts-1`, `alloy` voice)
- **Vector DB**: Qdrant (self-hosted via Docker)
- **Transport**: LiveKit open-source server (self-hosted via Docker)
- **Embeddings**: `intfloat/multilingual-e5-large` (multilingual, supports Armenian)

## Banks Covered

- ACBA Bank — Credits, Deposits, Branch Locations
- Evocabank — Credits, Deposits, Branch Locations
- Ardshinbank — Credits, Deposits, Branch Locations

## Model Choice Justification

| Component | Model | Why |
|---|---|---|
| STT | OpenAI Whisper API | Best Armenian ASR accuracy, native `hy` language support |
| LLM | GPT-4o | Superior Armenian reasoning, strict RAG instruction-following |
| TTS | OpenAI TTS (alloy) | Reliable Armenian speech synthesis, no setup required |
| Embeddings | multilingual-e5-large | Trained on 100+ languages including Armenian |
| Vector DB | Qdrant | Open-source, self-hostable, fast cosine similarity search |
| Transport | LiveKit OSS | Open-source WebRTC, fully self-hosted, Python SDK |

## Data Pipeline

Bank knowledge is built from two sources that are merged together:

- `data/scraped/` — raw data scraped from bank websites using Selenium
- `data/manual/` — manually curated, verified data for accurate financial information

The merge script (`ingest/merge_data.py`) filters out low-quality scraped chunks (navigation text, JavaScript errors) and combines them with the manual data into `data/merged/all_banks.json`, which is then embedded and stored in Qdrant.

## Prerequisites

- Python 3.11+
- Docker Desktop — download from https://www.docker.com/products/docker-desktop
- OpenAI API key — you need a paid OpenAI API key
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

**Step 3 — Update the agent greeting in `agent/main.py`** to mention the new bank. No other code changes needed.

The RAG system automatically handles the new bank — Qdrant stores all banks together and the embedding search finds the most relevant chunks regardless of which bank they come from.