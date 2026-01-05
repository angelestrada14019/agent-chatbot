"""
🎤 Whisper Utility
Utilidad ligera para transcripción de audio usando OpenAI Whisper.
"""
from openai import AsyncOpenAI
import config
from utils.logger import get_logger

logger = get_logger("WhisperUtil")

async def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe un archivo de audio de forma asíncrona.
    """
    client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    try:
        import os
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio no encontrado: {audio_path}")
            
        logger.info(f"🎤 Transcribiendo {audio_path}...")
        with open(audio_path, "rb") as f:
            transcript = await client.audio.transcriptions.create(
                model=config.WHISPER_MODEL,
                file=f,
                language=config.WHISPER_LANGUAGE
            )
        return transcript.text
    except Exception as e:
        logger.error(f"❌ Error en transcripción: {str(e)}")
        return "[Error en transcripción]"
