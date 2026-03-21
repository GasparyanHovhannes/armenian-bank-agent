# Armenian Bank Voice AI Agent

A voice AI customer support agent for Armenian banks built with LiveKit (open source), OpenAI Whisper STT, GPT-4o LLM, and RAG over scraped bank data.

## Architecture

- **STT**: OpenAI Whisper API (Armenian language `hy`)
- **LLM**: GPT-4o with RAG grounding — answers only from scraped bank data
- **TTS**: OpenAI TTS (`tts-1`, `alloy` voice)
- **Vector DB**: Qdrant (self-hosted via Docker)
- **Transport**: LiveKit open-source server (self-hosted via Docker)
- **Embeddings**: `intfloat/multilingual-e5-large` (multilingual, supports Armenian)

## Banks Covered

- ACBA Bank — Credits, Deposits, Branch Locations

## Model Choice Justification

| Component | Model | Why |
|---|---|---|
| STT | OpenAI Whisper API | Best Armenian ASR accuracy, native `hy` language support |
| LLM | GPT-4o | Superior Armenian reasoning, strict RAG instruction-following |
| TTS | OpenAI TTS (alloy) | Reliable Armenian speech synthesis, no setup required |
| Embeddings | multilingual-e5-large | Trained on 100+ languages including Armenian |
| Vector DB | Qdrant | Open-source, self-hostable, fast cosine similarity search |
| Transport | LiveKit OSS | Open-source WebRTC, fully self-hosted, Python SDK |

## Prerequisites

- Python 3.11+
- Docker Desktop — download from https://www.docker.com/products/docker-desktop
- OpenAI API key — you need a paid OpenAI API key.
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
> Scraped data is already included in `data/scraped/`. No scraping needed.
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

All answers are grounded exclusively in scraped ACBA Bank data via RAG. Off-topic questions receive a polite refusal in Armenian.