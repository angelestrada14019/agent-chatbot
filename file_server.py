"""
🌐 File Server for EvoDataAgent (FastAPI)
Sirve archivos exports (gráficos y Excel) vía HTTP
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List
import config
from utils.logger import get_logger

logger = get_logger("FileServer")

# Directorio de exports
EXPORTS_DIR = Path(config.EXPORTS_DIR)

# Crear aplicación FastAPI
app = FastAPI(
    title="EvoDataAgent File Server",
    description="Servidor de archivos para gráficos y reportes Excel",
    version=config.AGENT_VERSION,
    docs_url="/docs"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Info"])
async def root():
    """Información del servidor de archivos"""
    return {
        "name": "EvoDataAgent File Server",
        "version": config.AGENT_VERSION,
        "status": "running",
        "exports_directory": str(EXPORTS_DIR),
        "docs": "/docs"
    }


@app.get("/exports/{filename}", tags=["Files"])
async def download_file(filename: str) -> FileResponse:
    """
    Descarga un archivo del directorio de exports
    
    - **filename**: Nombre del archivo (ej: chart_abc123.png o export_xyz.xlsx)
    
    Returns FileResponse con el archivo solicitado
    """
    file_path = EXPORTS_DIR / filename
    
    # Verificar que el archivo existe
    if not file_path.exists():
        logger.warning(f"⚠️ Archivo no encontrado: {filename}")
        raise HTTPException(status_code=404, detail=f"Archivo '{filename}' no encontrado")
    
    # Verificar que es un archivo (no directorio)
    if not file_path.is_file():
        logger.warning(f"⚠️ Ruta no es un archivo: {filename}")
        raise HTTPException(status_code=400, detail="La ruta especificada no es un archivo")
    
    logger.info(f"📥 Sirviendo archivo: {filename}")
    
    # Determinar media_type según extensión
    media_type = "application/octet-stream"
    if filename.endswith('.png'):
        media_type = "image/png"
    elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
        media_type = "image/jpeg"
    elif filename.endswith('.xlsx'):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif filename.endswith('.pdf'):
        media_type = "application/pdf"
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type
    )


@app.get("/exports", tags=["Files"])
async def list_files() -> List[str]:
    """
    Lista todos los archivos disponibles en el directorio de exports
    
    Útil para debugging y verificación
    """
    if not EXPORTS_DIR.exists():
        return []
    
    files = [f.name for f in EXPORTS_DIR.iterdir() if f.is_file()]
    logger.info(f"📋 Listado de archivos solicitado: {len(files)} archivos")
    
    return files


@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Health check endpoint"""
    exports_exists = EXPORTS_DIR.exists()
    
    return {
        "status": "healthy" if exports_exists else "degraded",
        "exports_directory": str(EXPORTS_DIR),
        "directory_exists": exports_exists,
        "version": config.AGENT_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    
    # Asegurar que el directorio existe
    EXPORTS_DIR.mkdir(exist_ok=True)
    
    logger.info(f"🚀 Iniciando File Server (FastAPI) en puerto {config.FILE_SERVER_PORT}")
    logger.info(f"📁 Sirviendo archivos desde: {EXPORTS_DIR}")
    logger.info(f"📚 Docs: http://localhost:{config.FILE_SERVER_PORT}/docs")
    
    # Iniciar servidor
    uvicorn.run(
        "file_server:app",
        host="0.0.0.0",
        port=config.FILE_SERVER_PORT,
        reload=config.DEBUG_MODE,
        log_level="info"
    )
