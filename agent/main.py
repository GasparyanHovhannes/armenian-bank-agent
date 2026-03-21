from dotenv import load_dotenv
load_dotenv()

import logging
import asyncio
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
You MUST respond only in Armenian.
You ONLY answer questions about: Credits, Deposits, Branch Locations.
Base ALL answers strictly on the provided context provided below.
If off-topic, politely decline in Armenian.
If the answer is not in the context, say so in Armenian.
Never use outside knowledge — only use the context.

BANK KNOWLEDGE CONTEXT:
{context}
"""

# ── Load models once at startup ────────────────────────────────
logger.info("Pre-loading models...")
_vad = silero.VAD.load()
_whisper = ArmenianWhisperSTT()
_stt = stt.StreamAdapter(stt=_whisper, vad=_vad)
_tts = openai.TTS(model="tts-1", voice="alloy")
_rag = ArmenianBankRAG()
logger.info("Models loaded.")


class RAGAgent(Agent):
    def __init__(self):
        super().__init__(instructions=SYSTEM_PROMPT.format(context="No context yet."))

    async def on_user_turn_completed(self, turn_ctx, new_message):
        user_text = new_message.text_content

        if user_text:
            logger.info(f"USER SAID: {user_text}")

            context = await _rag.retrieve(user_text)
            logger.info(f"RAG CONTEXT: {context[:200]}...")

            # Add context as a new system message at the end of chat history
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
        llm=openai.LLM(model="gpt-4o"),
        tts=_tts,
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
            "Greet the user warmly in Armenian. Tell them you are a "
            "bank support assistant and can help with questions about "
            "credits, deposits, and branch locations."
        )
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
