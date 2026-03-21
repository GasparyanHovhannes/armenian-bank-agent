from openai import AsyncOpenAI
from livekit.agents import stt
from livekit.agents.types import APIConnectOptions
import numpy as np
import io
import wave

class ArmenianWhisperSTT(stt.STT):
    def __init__(self):
        super().__init__(
            capabilities=stt.STTCapabilities(
                streaming=False,
                interim_results=False
            )
        )
        self._client = AsyncOpenAI()

    async def _recognize_impl(
        self,
        buffer,
        *,
        language: str | None = "hy",
        conn_options: APIConnectOptions = APIConnectOptions()
    ) -> stt.SpeechEvent:

        audio_data = np.frombuffer(buffer.data, dtype=np.int16)

        wav_buf = io.BytesIO()
        with wave.open(wav_buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(buffer.sample_rate)
            wf.writeframes(audio_data.tobytes())
        wav_buf.seek(0)
        wav_buf.name = "audio.wav"

        transcript = await self._client.audio.transcriptions.create(
            model="whisper-1",
            file=wav_buf,
            language="hy",
            response_format="text"
        )

        text = transcript.strip() if isinstance(transcript, str) else ""

        return stt.SpeechEvent(
            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[
                stt.SpeechData(text=text, language="hy")
            ]
        )