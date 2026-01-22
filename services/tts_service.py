"""
🎙️ TTS Service - Text-to-Speech con ElevenLabs
Genera notas de voz naturales en español para respuestas del agente.
"""
import httpx
import logging
from pathlib import Path
from typing import Optional
import config

logger = logging.getLogger("TTSService")


class ElevenLabsTTS:
    """
    Servicio de Text-to-Speech usando ElevenLabs API.
    
    Genera audio de alta calidad en múltiples idiomas, optimizado para español.
    """
    
    def __init__(self):
        self.api_key = getattr(config, 'ELEVENLABS_API_KEY', None)
        self.voice_id = getattr(config, 'ELEVENLABS_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')  # Rachel
        self.base_url = "https://api.elevenlabs.io/v1"
        self.enabled = getattr(config, 'ENABLE_VOICE_RESPONSES', False)
        
        if self.enabled and not self.api_key:
            logger.warning("⚠️ ENABLE_VOICE_RESPONSES=true pero falta ELEVENLABS_API_KEY")
            self.enabled = False
        
        if self.enabled:
            logger.info(f"🎤 ElevenLabs TTS habilitado (Voice: {self.voice_id})")
    
    async def text_to_speech(
        self, 
        text: str, 
        output_path: str,
        model_id: str = "eleven_multilingual_v2"
    ) -> bool:
        """
        Convierte texto a audio usando ElevenLabs.
        
        Args:
            text: Texto a convertir (preferiblemente español)
            output_path: Ruta donde guardar el archivo de audio (.mp3)
            model_id: Modelo de ElevenLabs a usar
        
        Returns:
            True si se generó exitosamente, False en caso contrario
        """
        if not self.enabled:
            logger.debug("TTS deshabilitado, saltando generación de voz")
            return False
        
        if not text or len(text.strip()) == 0:
            logger.warning("Texto vacío, no se puede generar audio")
            return False
        
        try:
            url = f"{self.base_url}/text-to-speech/{self.voice_id}"
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Configuración optimizada para español
            payload = {
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": 0.5,        # Balance entre consistencia y expresividad
                    "similarity_boost": 0.75, # Mantener características de la voz
                    "style": 0.0,            # Sin estilo adicional (neutro)
                    "use_speaker_boost": True # Mejorar claridad
                }
            }
            
            logger.info(f"🎙️ Generando audio ({len(text)} chars)...")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    # Guardar audio
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    
                    file_size = len(response.content)
                    logger.info(f"✅ Audio generado: {output_path} ({file_size} bytes)")
                    return True
                else:
                    error_msg = response.text
                    logger.error(f"❌ Error ElevenLabs ({response.status_code}): {error_msg}")
                    return False
        
        except httpx.TimeoutException:
            logger.error("⏱️ Timeout generando audio (>30s)")
            return False
        except Exception as e:
            logger.error(f"❌ Error generando TTS: {str(e)}")
            return False
    
    def should_use_voice(self, text: str, user_sent_voice: bool = False) -> bool:
        """
        Determina si se debe usar voz para responder.
        
        Args:
            text: Texto de la respuesta
            user_sent_voice: Si el usuario envió un mensaje de voz
        
        Returns:
            True si se debe generar audio, False en caso contrario
        """
        if not self.enabled:
            return False
        
        # Solo responder con voz si el usuario envió voz (espejo)
        if not user_sent_voice:
            return False
        
        # Evitar TTS para textos muy largos (costo + tiempo)
        max_chars = getattr(config, 'VOICE_RESPONSE_MAX_CHARS', 500)
        if len(text) > max_chars:
            logger.info(f"Texto muy largo ({len(text)} > {max_chars}), no usar TTS")
            return False
        
        return True


# Singleton global
_tts_instance: Optional[ElevenLabsTTS] = None

def get_tts_service() -> ElevenLabsTTS:
    """Factory para obtener instancia del servicio TTS (singleton)"""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = ElevenLabsTTS()
    return _tts_instance
