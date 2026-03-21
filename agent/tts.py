from livekit.plugins import openai as livekit_openai

def ArmenianMMS_TTS():
    return livekit_openai.TTS(
        model="tts-1",
        voice="alloy"
    )