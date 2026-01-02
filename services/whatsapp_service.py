"""
💬 WhatsApp Service
Gestiona toda la comunicación con WhatsApp vía EvolutionAPI
"""
from typing import Dict, Any, Optional
import requests
import mimetypes

import config
from utils.logger import get_logger

logger = get_logger("WhatsAppService")


class WhatsAppService:
    """
    Servicio especializado en comunicación WhatsApp
    
    Responsabilidades:
    - Envío de mensajes de texto
    - Envío de archivos adjuntos
    - Normalización de números de teléfono
    """
    
    def __init__(self):
        """Inicializa el servicio de WhatsApp"""
        self.base_url = config.EVOLUTION_URL
        self.instance = config.EVOLUTION_INSTANCE
        self.api_key = config.EVOLUTION_API_KEY
        
        self.headers = {
            "Content-Type": "application/json",
            "apikey": self.api_key
        }
        
        logger.info("✅ WhatsAppService inicializado")
    
    def send_text_message(self, phone_number: str, text: str) -> bool:
        """
        Envía mensaje de texto por WhatsApp
        
        Args:
            phone_number: Número de destino (formato: 573124488445@c.us)
            text: Texto del mensaje
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            url = f"{self.base_url}/message/sendText/{self.instance}"
            
            payload = {
                "number": phone_number,
                "options": {"delay": 1000, "presence": "composing"},
                "text": text
            }
            
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            
            if response.status_code not in (200, 201):
                logger.error(
                    "❌ Error al enviar mensaje",
                    status_code=response.status_code,
                    response=response.text
                )
                return False
            
            logger.info(f"✅ Mensaje enviado a {phone_number}")
            return True
        
        except requests.exceptions.Timeout:
            logger.error("⏱️ Timeout al enviar mensaje")
            return False
        except Exception as e:
            logger.error(f"❌ Error al enviar WhatsApp: {str(e)}")
            return False
    
    def send_attachment(
        self,
        phone_number: str,
        file_data: str,
        filename: str,
        caption: str = "",
        file_type: str = "document"
    ) -> bool:
        """
        Envía archivo adjunto por WhatsApp
        
        Args:
            phone_number: Número de destino
            file_data: Datos del archivo en base64
            filename: Nombre del archivo
            caption: Texto que acompaña el archivo
            file_type: Tipo ('image' o 'document')
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Determinar mimetype
            mimetype, _ = mimetypes.guess_type(filename)
            if not mimetype:
                # Defaults según tipo
                if file_type == "image":
                    mimetype = "image/png"
                elif filename.endswith('.xlsx'):
                    mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                elif filename.endswith('.pdf'):
                    mimetype = "application/pdf"
                else:
                    mimetype = "application/octet-stream"
            
            # Determinar mediatype para WhatsApp
            mediatype = "image" if file_type == "image" else "document"
            
            # Endpoint correcto
            url = f"{self.base_url}/message/sendMedia/{self.instance}"
            
            # Payload correcto
            payload = {
                "number": phone_number,
                "mediatype": mediatype,
                "mimetype": mimetype,
                "media": file_data,  # Key 'media' no 'base64'
                "fileName": filename,
                "caption": caption,
                "delay": 1000,
                "linkPreview": False
            }
            
            response = requests.post(url, json=payload, headers=self.headers, timeout=60)
            
            if response.status_code not in (200, 201):
                logger.error(
                    "❌ Error al enviar adjunto",
                    status_code=response.status_code,
                    response=response.text[:200]
                )
                return False
            
            logger.info(f"✅ Adjunto enviado: {filename}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error al enviar adjunto: {str(e)}")
            return False
    
    def send_message_with_response(
        self,
        phone_number: str,
        response_data: Dict[str, Any]
    ) -> bool:
        """
        Envía respuesta completa (texto + adjuntos si los hay)
        
        Args:
            phone_number: Número de destino
            response_data: Dict con response_type, content, attachments
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Enviar mensaje de texto
            text_sent = self.send_text_message(phone_number, response_data["content"])
            
            if not text_sent:
                return False
            
            # Enviar adjuntos si los hay
            if response_data.get("attachments"):
                for attachment in response_data["attachments"]:
                    self.send_attachment(
                        phone_number=phone_number,
                        file_data=attachment["data"],
                        filename=attachment["filename"],
                        caption=attachment.get("caption", ""),
                        file_type=attachment.get("type", "document")
                    )
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Error al enviar respuesta completa: {str(e)}")
            return False
    
    @staticmethod
    def normalize_phone_number(number: str) -> str:
        """
        Normaliza número de teléfono al formato de EvolutionAPI
        
        Args:
            number: Número en cualquier formato
            
        Returns:
            str: Número normalizado (formato @c.us)
        """
        # Si viene con @s.whatsapp.net, convertir a @c.us
        if '@s.whatsapp.net' in number:
            number = number.replace('@s.whatsapp.net', '@c.us')
        
        # Si no tiene @, agregarlo
        if '@' not in number:
            number = f"{number}@c.us"
        
        return number
