"""
🎤 Message Processor Service
Procesa mensajes de texto y voz
"""
from typing import Dict, Any, Optional
from openai import OpenAI
from pathlib import Path

import config
from utils.logger import get_logger

logger = get_logger("MessageProcessor")


class MessageProcessor:
    """
    Servicio especializado en procesamiento de mensajes
    
    Responsabilidades:
    - Transcripción de voz con Whisper
    - Validación de mensajes
    - Normalización de texto
    """
    
    def __init__(self):
        """Inicializa el procesador de mensajes"""
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        logger.info("✅ MessageProcessor inicializado")
    
    def process_voice_message(self, audio_file_path: str) -> str:
        """
        Convierte audio a texto usando OpenAI Whisper API
        
        Args:
            audio_file_path: Path del archivo de audio
            
        Returns:
            str: Texto transcrito
            
        Raises:
            ValueError: Si el formato o tamaño no es válido
            Exception: Si falla la transcripción
        """
        try:
            # Validar archivo
            self._validate_audio_file(audio_file_path)
            
            logger.info("🎤 Procesando mensaje de voz...")
            
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.openai_client.audio.transcriptions.create(
                    model=config.WHISPER_MODEL,
                    file=audio_file,
                    language=config.WHISPER_LANGUAGE
                )
            
            text = transcript.text
            logger.info(f"✅ Audio transcrito: {text[:100]}...")
            return text
        
        except ValueError as e:
            logger.error(f"❌ Validación de audio falló: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ Error al transcribir audio: {str(e)}")
            raise
    
    def _validate_audio_file(self, audio_path: str) -> None:
        """
        Valida formato y tamaño del archivo de audio
        
        Args:
            audio_path: Path del archivo
            
        Raises:
            ValueError: Si el archivo no es válido
        """
        import os
        
        # Validar que existe
        if not os.path.exists(audio_path):
            raise ValueError(f"Archivo de audio no encontrado: {audio_path}")
        
        # Validar formato
        SUPPORTED_FORMATS = ['.ogg', '.mp3', '.wav', '.m4a', '.mp4', '.mpga', '.webm']
        file_ext = Path(audio_path).suffix.lower()
        
        if file_ext not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Formato de audio '{file_ext}' no soportado. "
                f"Formatos válidos: {', '.join(SUPPORTED_FORMATS)}"
            )
        
        # Validar tamaño (límite OpenAI: 25MB)
        MAX_SIZE_MB = 25
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        
        if file_size_mb > MAX_SIZE_MB:
            raise ValueError(
                f"Archivo muy grande: {file_size_mb:.1f}MB. "
                f"Máximo permitido: {MAX_SIZE_MB}MB"
            )
        
        logger.debug(f"✅ Audio validado: {file_ext}, {file_size_mb:.1f}MB")
    
    def validate_text_message(self, message: str) -> bool:
        """
        Valida que el mensaje de texto no esté vacío
        
        Args:
            message: Mensaje a validar
            
        Returns:
            bool: True si es válido
        """
        return bool(message and message.strip())
    
    async def get_chat_completion(self, message: str, system_prompt: Optional[str] = None) -> str:
        """
        Obtiene una respuesta de chat de OpenAI GPT (Async)
        
        Args:
            message: Mensaje del usuario
            system_prompt: Prompt de sistema opcional
            
        Returns:
            str: Respuesta generada
        """
        try:
            if not system_prompt:
                system_prompt = (
                    f"Eres {config.AGENT_NAME}, un asistente experto en análisis de datos. "
                    "Responde de forma profesional, amable y concisa. "
                    "Ayuda al usuario a entender sus datos y cómo usar las herramientas disponibles."
                )
            
            # OpenAI Python SDK ≥ 1.0 supports async, but the sync client can be used with a thread pool 
            # or just use the OpenAI client normally if it doesn't block much (for few tokens).
            # Better to use the sync client with a thread for now if we don't want to change the whole init.
            # Actually, let's use the standard call as it's common in this codebase.
            
            logger.info(f"🤖 Solicitando respuesta a OpenAI ({config.CHAT_MODEL})...")
            
            response = self.openai_client.chat.completions.create(
                model=config.CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7
            )
            
            reply = response.choices[0].message.content
            logger.info("✅ Respuesta de IA generada")
            return reply
            
        except Exception as e:
            logger.error(f"❌ Error en chat completion: {str(e)}")
            return "Lo siento, tuve un problema al procesar tu solicitud con la IA. ¿Podrías intentar de nuevo?"

    async def get_intent_classification(self, message: str) -> str:
        """
        Clasifica la intención del usuario usando GPT (Async)
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            str: Intención (query, visualization, export, analysis, calculation, chat)
        """
        try:
            system_prompt = (
                "Clasifica el mensaje del usuario en una de las siguientes intenciones. "
                "Responde ÚNICAMENTE con la palabra clave de la intención:\n"
                "- query: Consultas simples de datos (ej: 'ver ventas', 'productos')\n"
                "- visualization: Solicitud de gráficos (ej: 'grafica las ventas', 'haz un gráfico')\n"
                "- export: Exportación a Excel (ej: 'descarga en excel', 'genera reporte')\n"
                "- analysis: Análisis completo (ej: 'analiza las ventas del trimestre con gráfica y excel')\n"
                "- calculation: Cálculos matemáticos (ej: 'suma esto', 'promedio')\n"
                "- chat: Saludos, agradecimientos o conversación general (ej: 'hola', 'gracias', 'qué puedes hacer')\n"
                "\nResponde solo con el nombre de la intención."
            )
            
            logger.info(f"🎯 Clasificando intención con IA...")
            
            response = self.openai_client.chat.completions.create(
                model=config.CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0, # Determinístico
                max_tokens=10
            )
            
            intent = response.choices[0].message.content.lower().strip()
            # Validar que sea una de las permitidas
            valid_intents = ["query", "visualization", "export", "analysis", "calculation", "chat"]
            
            if intent not in valid_intents:
                logger.warning(f"⚠️ IA devolvió intención inválida: {intent}. Usando fallback 'chat'.")
                return "chat"
                
            logger.info(f"🎯 Intención detectada: {intent}")
            return intent
            
        except Exception as e:
            logger.error(f"❌ Error en clasificación de intención: {str(e)}")
            return "chat" # Fallback a chat

    def normalize_text(self, text: str) -> str:
        """
        Normaliza texto del usuario
        
        Args:
            text: Texto a normalizar
            
        Returns:
            str: Texto normalizado
        """
        if not text: return ""
        # Eliminar espacios extra
        normalized = " ".join(text.split())
        
        # Eliminar caracteres especiales problemáticos
        normalized = normalized.replace('\r\n', ' ').replace('\n', ' ')
        
        return normalized.strip()
