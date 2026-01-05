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

    async def fetch_media(self, message_key: Dict[str, Any], instance_name: Optional[str] = None, message_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Obtiene base64 de un mensaje de media de Evolution (con fallback y robustez)."""
        instance = (instance_name or self.instance or "").strip()
        try:
            # 1. Normalizar instance (eliminar invisibles)
            instance = "".join(ch for ch in instance if ch.isprintable())
            url = f"{self.base_url.rstrip('/')}/chat/getBase64FromMediaMessage/{instance}"
            
            # 2. Reconstruir KEY completa
            key = message_key.copy() if message_key else {}
            if message_data and (not key.get("id") or not key.get("remoteJid")):
                candidate = message_data.get("key") or message_data.get("message", {}).get("key") or {}
                if candidate: key = {**candidate, **key}
            
            if not key.get("participant") and key.get("remoteJid"):
                key["participant"] = key.get("remoteJid")

            # 3. Preparar variantes de Payload
            message_obj = message_data.get("message") if isinstance(message_data, dict) else None
            
            payloads = [
                {"key": key},
                {"key": key, "message": message_obj},
                {"message": message_data} if message_data else None
            ]
            # Filtrar vacíos y duplicados
            payloads = [p for p in payloads if p]

            logger.info(f"💾 Recuperando media para {instance} | ID: {key.get('id')}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for idx, payload in enumerate(payloads):
                    try:
                        logger.debug(f"➡️ Intento {idx+1} con payload: {list(payload.keys())}")
                        res = await client.post(
                            url, 
                            json=payload, 
                            headers={"apikey": self.api_key, "Content-Type": "application/json"}
                        )
                        
                        if res.status_code in (200, 201):
                            data = res.json()
                            base64_data = data.get("base64") or data.get("data")
                            if base64_data:
                                logger.info(f"✅ Media obtenida con éxito (Intento {idx+1})")
                                return base64_data
                        
                        logger.warning(f"⚠️ Intento {idx+1} falló ({res.status_code}): {res.text[:100]}")
                    except Exception as e:
                        logger.error(f"❌ Error en intento {idx+1}: {e}")

            return None
        except Exception as e:
            logger.error(f"❌ Excepción crítica en fetch_media: {str(e)}")
            return None
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()
