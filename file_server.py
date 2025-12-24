"""
🌐 Simple File Server
Servidor Flask para servir archivos exportados (gráficos y Excel) vía URLs
"""
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from pathlib import Path
import config
from utils.logger import get_logger

app = Flask(__name__)
CORS(app)
logger = get_logger("FileServer")

# Directorio de exports
EXPORTS_DIR = Path(config.EXPORTS_DIR)


@app.route('/exports/<path:filename>')
def serve_file(filename):
    """
    Sirve archivos del directorio exports
    
    Args:
        filename: Nombre del archivo solicitado
        
    Returns:
        Archivo o error 404
    """
    try:
        logger.info(f"📥 Sirviendo archivo: {filename}")
        return send_from_directory(EXPORTS_DIR, filename)
    except Exception as e:
        logger.error(f"❌ Error al servir archivo: {str(e)}")
        return jsonify({"error": "Archivo no encontrado"}), 404


@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "EvoDataAgent File Server",
        "exports_dir": str(EXPORTS_DIR)
    })


@app.route('/')
def index():
    """Página principal con información"""
    return """
    <html>
    <head>
        <title>EvoDataAgent File Server</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            h1 { color: #1f77b4; }
            .info { background: white; padding: 20px; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>🤖 EvoDataAgent File Server</h1>
        <div class="info">
            <h2>Estado: ✅ Activo</h2>
            <p>Este servidor sirve archivos generados por EvoDataAgent:</p>
            <ul>
                <li>📊 Gráficos (PNG, HTML)</li>
                <li>📁 Archivos Excel (XLSX)</li>
            </ul>
            <p><strong>Endpoint:</strong> <code>/exports/&lt;filename&gt;</code></p>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    # Asegurar que el directorio existe
    EXPORTS_DIR.mkdir(exist_ok=True)
    
    logger.info(f"🚀 Iniciando File Server en puerto 8000")
    logger.info(f"📁 Sirviendo archivos desde: {EXPORTS_DIR}")
    
    # Iniciar servidor
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=config.DEBUG_MODE
    )
