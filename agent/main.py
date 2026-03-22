from dotenv import load_dotenv
load_dotenv()

import logging
from livekit.agents import (
    AgentSession, Agent, JobContext,
    WorkerOptions, cli, AutoSubscribe
)
from livekit.agents import stt, llm
from livekit.plugins import silero, openai
from stt import ArmenianWhisperSTT
from rag import ArmenianBankRAG

logger = logging.getLogger("armenian-bank-agent")

SYSTEM_PROMPT = """
Դուք հայկական բանկերի հաճախորդների սպասարկման օգնականն եք։
You MUST respond only in Armenian language.
You ONLY answer questions about: Credits, Deposits, Branch Locations.
Base ALL answers strictly on the provided context below.
If off-topic, politely decline in Armenian.
If not in context, say so in Armenian.

IMPORTANT FORMATTING RULES FOR VOICE:
- Always write numbers as Armenian words, not digits
- For decimal numbers use "ամբողջ" not "կետ". Example: "երեք ամբողջ հինգ տոկոս"
- Write AMD amounts as words: "հիսուն հազար դրամ" instead of "50,000 AMD"
- Write USD amounts as words: "հարյուր դոլար" instead of "100 USD"
- Write EUR amounts as words: "հարյուր եվրո" instead of "100 EUR"
- Never use symbols like %, $, €, AMD or digits in your response
- Keep responses concise and natural for spoken conversation
- Speak as if talking to a customer on the phone

CONTEXT:
{context}
"""

# ── Load models once at startup ────────────────────────────────
logger.info("Pre-loading models...")
_vad = silero.VAD.load()
_whisper = ArmenianWhisperSTT()
_stt = stt.StreamAdapter(stt=_whisper, vad=_vad)
_tts = openai.TTS(model="tts-1", voice="alloy")
_rag = ArmenianBankRAG()
_llm = openai.LLM(model="gpt-4o")
logger.info("Models loaded.")


class RAGAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions=SYSTEM_PROMPT.format(context="No context yet.")
        )

    async def on_user_turn_completed(self, turn_ctx, new_message):
        user_text = new_message.text_content
        if user_text:
            logger.info(f"USER SAID: {user_text}")
            context = await _rag.retrieve(user_text)
            logger.info(f"RAG CONTEXT: {context[:200]}...")
            turn_ctx.add_message(
                role="system",
                content=SYSTEM_PROMPT.format(context=context)
            )
        await super().on_user_turn_completed(turn_ctx, new_message)


async def entrypoint(ctx: JobContext):
    logger.info("Armenian bank agent starting...")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    session = AgentSession(
        vad=_vad,
        stt=_stt,
        llm=_llm,
        tts=_tts,
        min_endpointing_delay=1.5,
    )

    @session.on("agent_speech_committed")
    def on_reply(msg):
        logger.info(f"AGENT REPLIED: {msg.content}")

    await session.start(
        room=ctx.room,
        agent=RAGAgent(),
    )

    await session.generate_reply(
        instructions=(
            "Greet the user warmly in Armenian. Tell them you are an Armenian "
            "bank support assistant and can help with questions about "
            "credits, deposits, and branch locations for ACBA Bank, "
            "Evocabank, and Ardshinbank."
        )
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))