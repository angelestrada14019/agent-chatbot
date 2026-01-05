"""
📞 WhatsApp Service - EvolutionAPI Integration
Maneja el envío de mensajes y archivos a través de EvolutionAPI de forma asíncrona.
"""
import base64
import mimetypes
import httpx
from typing import Dict, Any, Optional, List
from pathlib import Path

import config
from utils.logger import get_logger

logger = get_logger("WhatsAppService")

class WhatsAppService:
    """Servicio asíncrono para interactuar con EvolutionAPI"""
    
    def __init__(self):
        self.base_url = config.EVOLUTION_URL
        self.instance = config.EVOLUTION_INSTANCE
        self.api_key = config.EVOLUTION_API_KEY
        self.headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
        # Client reusable para eficiencia (SOLID: Performance)
        self.client = httpx.AsyncClient(headers=self.headers, timeout=60.0)
    
    async def send_text_message(self, phone_number: str, message: str) -> bool:
        """Envía mensaje de texto simple de forma asíncrona"""
        try:
            url = f"{self.base_url}/message/sendText/{self.instance}"
            payload = {
                "number": phone_number,
                "text": message,
                "delay": 1000,
                "linkPreview": False
            }
            
            res = await self.client.post(url, json=payload)
            return res.status_code in (200, 201)
        except Exception as e:
            logger.error(f"❌ Error enviando texto: {str(e)}")
            return False

    async def send_attachment(self, phone_number: str, file_path: str, caption: str = "") -> bool:
        """Lee un archivo local y lo envía de forma asíncrona"""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"❌ Archivo no encontrado: {file_path}")
                return False
                
            # Leer archivo de forma bloqueante (pequeños archivos de exportación)
            # Para archivos grandes se podría usar aiofiles, pero para charts/excel < 1MB está bien.
            with open(path, "rb") as f:
                data_b64 = base64.b64encode(f.read()).decode('utf-8')
            
            filename = path.name
            mimetype, _ = mimetypes.guess_type(file_path)
            mimetype = mimetype or "application/octet-stream"
            mediatype = "image" if mimetype.startswith("image/") else "document"
            
            url = f"{self.base_url}/message/sendMedia/{self.instance}"
            payload = {
                "number": phone_number,
                "mediatype": mediatype,
                "mimetype": mimetype,
                "media": data_b64,
                "fileName": filename,
                "caption": caption
            }
            
            res = await self.client.post(url, json=payload)
            return res.status_code in (200, 201)
        except Exception as e:
            logger.error(f"❌ Error enviando adjunto {file_path}: {str(e)}")
            return False

    async def send_message_with_response(self, phone_number: str, response_data: Dict[str, Any]) -> bool:
        """
        Envía la respuesta del agente (texto + archivos) de forma asíncrona.
        """
        try:
            # 1. Enviar texto principal
            text = response_data.get("response", "")
            if text:
                await self.send_text_message(phone_number, text)
            
            # 2. Enviar archivos (si hay)
            files = response_data.get("files", [])
            for file_path in files:
                await self.send_attachment(phone_number, file_path)
                
            return True
        except Exception as e:
            logger.error(f"❌ Error en send_message_with_response: {str(e)}")
            return False

    def normalize_phone_number(self, number: str) -> str:
        """Asegura formato @c.us"""
        if "@" not in number:
            return f"{number}@c.us"
        return number.replace("@s.whatsapp.net", "@c.us")

    async def fetch_media(self, message_key: Dict[str, Any]) -> Optional[str]:
        """Obtiene base64 de un mensaje de media de Evolution"""
        try:
            url = f"{self.base_url}/chat/getBase64FromMediaMessage/{self.instance}"
            payload = {"key": message_key, "convertToMp3": True}
            
            res = await self.client.post(url, json=payload)
            if res.status_code in (200, 201):
                return res.json().get("base64")
            return None
        except Exception as e:
            logger.error(f"❌ Error en fetch_media: {str(e)}")
            return None
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()
