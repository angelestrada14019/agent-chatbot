"""
🎤 Message Processor Service
Procesa mensajes de texto y voz (Transcripción Whisper) de forma asíncrona.
"""
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from pathlib import Path

import config
from utils.logger import get_logger

logger = get_logger("MessageProcessor")

class MessageProcessor:
    """
    Servicio especializado en procesamiento de mensajes (Asíncrono)
    
    Responsabilidades:
    - Transcripción de voz con Whisper (Async)
    - Validación de mensajes
    - Normalización de texto
    """
    
    def __init__(self):
        """Inicializa el procesador de mensajes con cliente Async"""
        self.openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        logger.info("✅ MessageProcessor inicializado (Async)")
    
    async def process_voice_message(self, audio_file_path: str) -> str:
        """
        Convierte audio a texto usando OpenAI Whisper API (Async)
        """
        try:
            self._validate_audio_file(audio_file_path)
            logger.info("🎤 Transcribiendo audio con Whisper (Async)...")
            
            # Nota: El archivo se abre en binario. Para máxima asincronía con archivos grandes 
            # se podría usar aiofiles, pero para mensajes de voz de WhatsApp (<1MB) open() es aceptable.
            with open(audio_file_path, "rb") as audio_file:
                transcript = await self.openai_client.audio.transcriptions.create(
                    model=config.WHISPER_MODEL,
                    file=audio_file,
                    language=config.WHISPER_LANGUAGE
                )
            
            text = transcript.text
            logger.info(f"✅ Transcripción exitosa: {text[:50]}...")
            return text
        except Exception as e:
            logger.error(f"❌ Error transcribiendo audio: {str(e)}")
            return "[Error en transcripción]"

    def _validate_audio_file(self, audio_path: str) -> None:
        """Valida que el archivo exista"""
        import os
        if not os.path.exists(audio_path):
            raise ValueError(f"Archivo no encontrado: {audio_path}")
        
    def validate_text_message(self, message: str) -> bool:
        """Valida que el mensaje no esté vacío"""
        return bool(message and message.strip())
    
    def normalize_text(self, text: str) -> str:
        """Limpia el texto del usuario"""
        if not text: return ""
        return " ".join(text.split()).strip()
