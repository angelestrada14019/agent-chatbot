"""
🤖 EvoDataAgent - OpenAI Agents SDK
Orquestador principal basado en el SDK oficial de OpenAI Agents.
Cumplimiento 100% con SOLID y Clean Code.
"""
import uuid
import os
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel

from agents import Agent, Runner
from agents.mcp import MCPServerSse, MCPServerSseParams
import config
from utils.logger import get_logger
from utils.whisper_util import transcribe_audio
from agents.memory import SQLiteSession

# Herramientas Core (Visualización y Reportes)
from tools.visualizer import generate_chart
from tools.excel_generator import generate_excel_report
from tools.calculator import calculate_expression

logger = get_logger("EvoDataAgent")

class EvoDataAgent:
    """
    Agente experto en Análisis de Datos de M.C.T. SAS.
    Implementación nativa con OpenAI Agents SDK.
    """
    
    def __init__(self):
        # 🔌 Configuración Dinámica de MCP (Standard SDK)
        self.mcp_server = MCPServerSse(
            name="mcp_database",
            params=MCPServerSseParams(
                url=config.MCP_SERVER_URL,
                timeout=30.0
            )
        )

        # Definición del Agente Nativo
        self.agent = Agent(
            name=config.AGENT_NAME,
            instructions=(
                f"Eres {config.AGENT_NAME}, el analista de datos oficial de M.C.T. SAS. "
                "Tu misión es proporcionar insights profesionales sobre cualquier base de datos conectada vía MCP. "
                "\n\nESTRATEGIA:"
                "\n1. Explora las herramientas disponibles en el servidor MCP para entender qué datos puedes consultar (ventas, stock, clientes, etc.)."
                "\n2. Ejecuta consultas SQL SELECT precisas según la necesidad del usuario."
                "\n3. Genera gráficas o excels según la solicitud del usuario usando tus herramientas locales."
                "\n4. Sé profesional y estructurado en español."
            ),
            model=config.CHAT_MODEL,
            mcp_servers=[self.mcp_server],
            tools=[
                generate_chart, 
                generate_excel_report, 
                calculate_expression
            ]
        )
        # Memoria persistente basada en SQLite
        self.sessions: Dict[str, SQLiteSession] = {}
        
        # TTS Service para respuestas de voz
        from services.tts_service import get_tts_service
        self.tts = get_tts_service()
        
        logger.info(f" Agente '{config.AGENT_NAME}' inicializado con soporte de Memoria{' + TTS' if self.tts.enabled else ''}")

    async def _ensure_mcp_connected(self):
        """
        Garantiza que la conexión MCP esté activa antes de procesar.
        Maneja reconexión y fallback inteligente de hosts de forma robusta.
        """
        try:
            # Obtener URL de forma segura (soporta dict o Pydantic object)
            params = self.mcp_server.params
            current_url = getattr(params, "url", None) or (params.get("url") if isinstance(params, dict) else None)
            
            logger.info(f"📡 Verificando conexión MCP a {current_url}...")
            await self.mcp_server.connect()
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"⚠️ Primer intento de conexión falló: {error_msg}")
            
            # Fallback inteligente: Si falla 'mcp-simulator', intentar 'localhost'
            params = self.mcp_server.params
            current_url = getattr(params, "url", None) or (params.get("url") if isinstance(params, dict) else None)
            
            if current_url and "mcp-simulator" in current_url:
                logger.info("🔄 Detectado entorno local con configuración Docker. Intentando fallback a localhost...")
                new_url = current_url.replace("mcp-simulator", "localhost")
                
                # Actualizar URL de forma agnóstica
                if isinstance(params, dict):
                    params["url"] = new_url
                else:
                    setattr(params, "url", new_url)
                
                try:
                    logger.info(f"📡 Reintentando conexión a {new_url}...")
                    await self.mcp_server.connect()
                    logger.info(f"✅ Conexión exitosa usando fallback: {new_url}")
                    return
                except Exception as e2:
                    logger.error(f"❌ Falló también el fallback a localhost: {e2}")
            
            # Si el error sugiere que ya está conectado, lo ignoramos
            if "already connected" in error_msg.lower() or "connection is active" in error_msg.lower():
                 logger.debug("Info: Ya estaba conectado.")
            else:
                 logger.error(f"❌ Error crítico conectando a MCP: {e}")

    async def process_message(
        self,
        message: str,
        phone_number: str = "user",
        is_voice: bool = False,
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa el mensaje usando el Runner del SDK.
        No usa MessageProcessor (Redundante); usa Whisper directamente si es voz.
        """
        request_id = str(uuid.uuid4())
        attachments = []
        
        try:
            # 0. Asegurar Conexión MCP (Fix: Server not initialized)
            await self._ensure_mcp_connected()

            # 0.1 Capturar archivos existentes ANTES de procesar (método robusto)
            exports_dir = Path(config.EXPORTS_DIR)
            files_before: Dict[str, float] = {}
            if exports_dir.exists():
                for f in exports_dir.iterdir():
                    if f.is_file():
                        files_before[f.name] = f.stat().st_mtime
            
            timestamp_before = time.time()

            # 1. Voz a Texto (Si aplica)
            if is_voice and audio_path:
                message = await transcribe_audio(audio_path)
            
            if not message or not message.strip():
                return {"success": False, "error": "Mensaje vacío", "request_id": request_id}

            logger.info(f"📩 [{phone_number}] -> {message[:50]}...")
            
            # 2. Obtener o crear sesión para el usuario (Memoria)
            if phone_number not in self.sessions:
                db_path = f"logs/memory_{phone_number}.db"
                self.sessions[phone_number] = SQLiteSession(session_id=phone_number, db_path=db_path)
            
            session = self.sessions[phone_number]

            # 3. Ejecutar Runner del SDK con Memoria
            result = await Runner.run(self.agent, message, session=session)
            
            # 4. Detectar archivos NUEVOS en exports (método robusto)
            # Comparar archivos antes y después - detecta cualquier archivo nuevo o modificado
            if exports_dir.exists():
                for file_path in exports_dir.iterdir():
                    if file_path.is_file():
                        file_name = file_path.name
                        file_mtime = file_path.stat().st_mtime
                        
                        # Archivo nuevo o modificado después de timestamp_before
                        is_new = file_name not in files_before
                        is_modified = file_mtime > timestamp_before
                        
                        if is_new or is_modified:
                            # Solo incluir archivos típicos de exportación
                            if file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.xlsx', '.csv', '.pdf']:
                                attachments.append(str(file_path))
                                logger.info(f"📎 Archivo detectado: {file_path}")
            
            # Log si no se detectaron archivos pero hay texto sobre archivos generados
            if not attachments:
                output_text = result.final_output or ""
                if any(kw in output_text.lower() for kw in ["chart", "excel", "gráfica", "grafica", "reporte", "archivo"]):
                    logger.warning("⚠️ El agente menciona archivos pero no se detectaron en exports/")

            return {
                "success": True,
                "response": result.final_output,
                "files": attachments,
                "voice_note": await self._generate_voice_response(result.final_output, is_voice),
                "request_id": request_id
            }

        except Exception as e:
            from utils.logger import log_error_with_context
            log_error_with_context(logger, e, {"phone_number": phone_number, "request_id": request_id})
            return {"success": False, "error": str(e), "request_id": request_id}
    
    async def _generate_voice_response(self, text: str, user_sent_voice: bool) -> Optional[str]:
        """
        Genera nota de voz si está habilitado y es apropiado.
        
        Args:
            text: Respuesta del agente en texto
            user_sent_voice: Si el usuario envió un mensaje de voz
        
        Returns:
            Path del archivo de audio generado, o None si no se generó
        """
        if not self.tts.should_use_voice(text, user_sent_voice):
            return None
        
        try:
            # Limitar longitud para evitar audios muy largos
            response_text = text
            if len(response_text) > config.VOICE_RESPONSE_MAX_CHARS:
                response_text = response_text[:config.VOICE_RESPONSE_MAX_CHARS] + "..."
            
            # Generar audio
            voice_path = Path(config.TEMP_DIR) / f"response_{uuid.uuid4().hex}.mp3"
            
            success = await self.tts.text_to_speech(response_text, str(voice_path))
            if success:
                logger.info(f"🎵 Nota de voz generada: {voice_path}")
                return str(voice_path)
            else:
                return None
        except Exception as e:
            logger.error(f"❌ Error generando nota de voz: {e}")
            return None