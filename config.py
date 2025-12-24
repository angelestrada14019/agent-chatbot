"""
🔧 EvoDataAgent Configuration
Configuración centralizada para el agente de análisis de datos
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# ========================================
# 🗄️ DATABASE CONFIGURATION (PostgreSQL)
# ========================================
DB_TYPE = "postgresql"
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "analytics")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Connection pool settings
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

# Build connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ========================================
# 🤖 EVOLUTION API CONFIGURATION
# ========================================
EVOLUTION_URL = os.getenv("EVOLUTION_URL", "http://82.25.93.102:8080/")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "clientes")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "123456.+az154721ww")

# ========================================
# 🎤 OPENAI WHISPER API CONFIGURATION
# ========================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "whisper-1")  # OpenAI API model
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "es")  # Spanish by default

# ========================================
# 📊 VISUALIZATION SETTINGS
# ========================================
PLOT_DPI = int(os.getenv("PLOT_DPI", "150"))  # Quality for PNG exports
PLOT_STYLE = os.getenv("PLOT_STYLE", "seaborn-v0_8-darkgrid")
CHART_DEFAULT_WIDTH = int(os.getenv("CHART_DEFAULT_WIDTH", "12"))
CHART_DEFAULT_HEIGHT = int(os.getenv("CHART_DEFAULT_HEIGHT", "6"))

# Color palettes
COLOR_PALETTE_PRIMARY = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", 
                         "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]

# ========================================
# 📁 FILE PATHS
# ========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Create directories if they don't exist
for directory in [TEMP_DIR, EXPORTS_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

# ========================================
# 🔐 SECURITY SETTINGS
# ========================================
MAX_QUERY_TIMEOUT = int(os.getenv("MAX_QUERY_TIMEOUT", "30"))  # seconds
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "25"))  # WhatsApp limit
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds

# Allowed SQL keywords (whitelist approach for safety)
ALLOWED_SQL_KEYWORDS = [
    "SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER",
    "GROUP BY", "ORDER BY", "HAVING", "LIMIT", "OFFSET", "AS", "ON",
    "AND", "OR", "NOT", "IN", "LIKE", "BETWEEN", "IS", "NULL"
]

# Forbidden SQL keywords (blacklist for destructive operations)
FORBIDDEN_SQL_KEYWORDS = [
    "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE",
    "GRANT", "REVOKE", "EXEC", "EXECUTE", "CALL"
]

# ========================================
# 📝 LOGGING CONFIGURATION
# ========================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "json"  # json or text
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# ========================================
# 🌐 FILE DELIVERY SETTINGS
# ========================================
# Dual delivery: both attachments and URLs
FILE_DELIVERY_METHOD = os.getenv("FILE_DELIVERY_METHOD", "both")  # both, attachment, url
FILE_SERVER_URL = os.getenv("FILE_SERVER_URL", "http://localhost:8000/exports")  # Base URL for file downloads

# ========================================
# 🧠 AGENT BEHAVIOR
# ========================================
AGENT_NAME = "EvoDataAgent"
AGENT_VERSION = "1.0.0"
DEFAULT_LANGUAGE = "es"  # Spanish
RESPONSE_TIMEOUT = int(os.getenv("RESPONSE_TIMEOUT", "60"))  # seconds

# Intent classification confidence threshold
INTENT_CONFIDENCE_THRESHOLD = float(os.getenv("INTENT_CONFIDENCE_THRESHOLD", "0.6"))

# ========================================
# 📊 EXCEL EXPORT DEFAULTS
# ========================================
EXCEL_AUTHOR = os.getenv("EXCEL_AUTHOR", "EvoDataAgent")
EXCEL_COMPANY = os.getenv("EXCEL_COMPANY", "M.C.T. SAS")
EXCEL_DEFAULT_SHEET_NAME = "Datos"

# ========================================
# 🎨 BRANDING
# ========================================
COMPANY_NAME = "M.C.T. SAS"
COMPANY_COLOR_PRIMARY = "#1f77b4"
COMPANY_COLOR_SECONDARY = "#ff7f0e"
COMPANY_LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")

# ========================================
# 🔍 DEBUG MODE
# ========================================
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "False").lower() == "true"
