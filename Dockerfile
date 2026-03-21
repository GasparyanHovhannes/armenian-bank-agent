FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg libsndfile1 git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ ./agent/

# Pre-download models so they're baked into the image
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('large-v3', device='cpu', compute_type='int8')"
RUN python -c "from transformers import VitsModel, AutoTokenizer; VitsModel.from_pretrained('facebook/mms-tts-hye'); AutoTokenizer.from_pretrained('facebook/mms-tts-hye')"

CMD ["python", "agent/main.py", "start"]