# 🤖 EvoDataAgent

**Agente inteligente de análisis y automatización** integrado con EvolutionAPI y PostgreSQL. Procesa mensajes de texto/voz, ejecuta consultas SQL, genera visualizaciones, realiza cálculos estadísticos y exporta datos a Excel.

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-green.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-Whisper-orange.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-teal.svg)

---

## 🎯 Características

- 🎤 **Procesamiento de voz**: Transcripción automática con OpenAI Whisper API
- 🗄️ **Conexión PostgreSQL**: Consultas seguras con validación anti-SQL injection
- 📊 **Visualizaciones profesionales**: Gráficos con matplotlib, plotly y seaborn
- 🧮 **Cálculos estadísticos**: Métricas, correlaciones, outliers, agregaciones
- 📁 **Exportación Excel**: Archivos formateados con estilos corporativos
- 💬 **Integración WhatsApp**: Envío de mensajes y archivos via EvolutionAPI
- 🔄 **Dual delivery**: Archivos como adjuntos Y URLs de descarga
- 🧠 **Clasificación de intenciones**: Strategy Pattern para procesamiento inteligente
- ⚡ **FastAPI Async**: Procesamiento asíncrono con background tasks
- 📚 **Documentación automática**: Swagger UI en `/docs`

---

## 📋 Requisitos Previos

- Python 3.12 o superior
- PostgreSQL instalado y corriendo
- Cuenta de OpenAI con API key
- Instancia de EvolutionAPI configurada

---

## 🚀 Instalación

### 1. Clonar o descargar el proyecto

```bash
cd e:\mct\project\chatbot
```

### 2. Crear entorno virtual

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y edita con tus credenciales:

```bash
copy .env.example .env
```

Edita `.env` con tus valores:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=analytics
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña

# OpenAI
OPENAI_API_KEY=sk-tu-api-key-aqui

# EvolutionAPI
EVOLUTION_URL=http://82.25.93.102:8080/
EVOLUTION_INSTANCE=clientes
EVOLUTION_API_KEY=123456.+az154721ww

# Server Ports
WEBHOOK_SERVER_PORT=5000
FILE_SERVER_PORT=8000
```

---

## 📊 Arquitectura Refactorizada (SOLID)

```
evodata_agent.py          # 🤖 Orquestador principal (refactorizado)
├── services/             # 📦 Capa de servicios (SRP)
│   ├── message_processor.py   # 🎤 Procesamiento texto/voz
│   ├── whatsapp_service.py    # 💬 Comunicación WhatsApp
│   └── intent_router.py       # 🎯 Routing de intenciones (Strategy)
├── tools/                # 🛠️ Herramientas (implementan Tool interface)
│   ├── base.py          # 🔧 Tool interface + ToolResult  
│   ├── mcp_connector.py  # 🗄️ PostgreSQL connector
│   ├── visualizer.py     # 📈 Generador de gráficos
│   ├── excel_generator.py # 📁 Exportador Excel
│   └── calculator.py     # 🧮 Cálculos estadísticos (NUEVO)
├── utils/
│   ├── logger.py         # 📝 Sistema de logging
│   └── response_formatter.py # 📤 Formateador de respuestas
├── config.py             # ⚙️ Configuración centralizada
├── webhook_server.py     # 📡 Webhook FastAPI para EvolutionAPI
├── file_server.py        # 🌐 Servidor FastAPI de archivos
└── examples/
    └── example_queries.py # 📚 Ejemplos de uso
```

---

## 💻 Uso Básico

### Iniciar Servidores

```bash
# Terminal 1: Webhook server (recibe mensajes de EvolutionAPI)
python webhook_server.py
# Servidor en http://localhost:5000
# Docs en http://localhost:5000/docs

# Terminal 2: File server (sirve archivos generados)
python file_server.py
# Servidor en http://localhost:8000
# Docs en http://localhost:8000/docs
```

### Configurar Webhook en EvolutionAPI

Apunta tu instancia de EvolutionAPI a:
```
URL: http://tu-ip:5000/webhook/evolution
Eventos: messages.upsert
```

---

## 🛠️ Herramientas del Agente

### Tool 1: MCP Database Connector

```python
from tools.mcp_connector import get_connector

db = get_connector()

# Ejecutar consulta
result = db.execute_query(
    sql="SELECT * FROM ventas WHERE fecha >= :fecha",
    params={"fecha": "2024-01-01"}
)

# Llamar procedimiento almacenado
result = db.call_stored_procedure(
    procedure_name="calcular_ventas_mes",
    params={"mes": 12, "año": 2024}
)
```

### Tool 2: Visualizer

```python
from tools.visualizer import get_visualizer
import pandas as pd

viz = get_visualizer()

# Gráfico de barras
chart = viz.create_bar_chart(
    data=df,
    x_column="categoria",
    y_column="ventas",
    title="Ventas por Categoría"
)

# Gráfico interactivo con Plotly
chart = viz.create_interactive_plotly(
    data=df,
    chart_type="bar",
    x_column="mes",
    y_column="ventas"
)
```

### Tool 3: Excel Generator

```python
from tools.excel_generator import get_excel_generator

excel = get_excel_generator()

# Excel simple
result = excel.create_excel_from_data(
    data=df,
    filename="reporte_ventas",
    apply_styling=True
)

# Excel multi-hoja
result = excel.create_multi_sheet_excel(
    sheets_data={
        "Ventas": ventas_df,
        "Productos": productos_df,
        "Resumen": resumen_df
    }
)
```

### Tool 4: Calculator (NUEVO) 🧮

```python
from tools.calculator import get_calculator
import pandas as pd

calc = get_calculator()

# Métricas estadísticas
result = calc.execute("metrics", 
    data=df,
    columns=["ventas", "cantidad"],
    metrics=["sum", "mean", "std"]
)

# Tasa de crecimiento
result = calc.execute("growth_rate",
    data=df,
    value_column="ventas",
    period_column="mes",
    periods=1
)

# Promedio móvil
result = calc.execute("moving_average",
    data=df,
    column="ventas",
    window=3,
    ma_type="simple"
)

# Detectar outliers
result = calc.execute("outliers",
    data=df,
    column="ventas",
    method="iqr",
    threshold=1.5
)

# Correlación
result = calc.execute("correlation",
    data=df,
    columns=["ventas", "precio", "cantidad"],
    method="pearson"
)

# Agregaciones por grupo
result = calc.execute("aggregates",
    data=df,
    group_by="categoria",
    agg_column="ventas",
    agg_functions=["sum", "mean", "count"]
)
```

---

## 💬 Integración con WhatsApp

### Enviar Mensaje via Servicio

```python
from services.whatsapp_service import WhatsAppService

whatsapp = WhatsAppService()

# Enviar texto
whatsapp.send_text_message(
    phone_number="573124488445@c.us",
    text="Hola desde EvoDataAgent"
)

# Enviar archivo
whatsapp.send_attachment(
    phone_number="573124488445@c.us",
    file_data=base64_data,
    filename="reporte.xlsx",
    caption="Reporte de ventas"
)
```

### Webhook Automático (Ya Configurado)

El `webhook_server.py` maneja automáticamente:
- ✅ Mensajes de texto
- ✅ Mensajes de voz (transcribe con Whisper)
- ✅ Comandos especiales (hola, ayuda)
- ✅ Procesamiento en background (no bloquea)
- ✅ Respuestas automáticas

---

## 🌐 API Endpoints (FastAPI)

### Webhook Server (Puerto 5000)

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/webhook/evolution` | POST | Recibe webhooks de EvolutionAPI |
| `/health` | GET | Health check con estado de DB |
| `/stats` | GET | Estadísticas del agente |
| `/docs` | GET | Documentación Swagger UI |
| `/redoc` | GET | Documentación ReDoc |

### File Server (Puerto 8000)

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/exports/{filename}` | GET | Descarga archivo generado |
| `/exports` | GET | Lista todos los archivos |
| `/health` | GET | Health check |
| `/docs` | GET | Documentación Swagger UI |

---

## 🧪 Ejemplos Completos

Ejecuta los ejemplos incluidos:

```bash
python examples/example_queries.py
```

Incluye ejemplos de:
1. ✅ Consulta simple a DB
2. ✅ Visualización de datos
3. ✅ Exportación a Excel
4. ✅ Procesamiento de voz
5. ✅ Uso directo de tools
6. ✅ Excel multi-hoja
7. ✅ Integración WhatsApp completa
8. ✅ **NUEVO**: Cálculos estadísticos

---

## 🔒 Seguridad

El agente implementa múltiples capas de seguridad:

- ✅ **SQL Injection Prevention**: Queries parametrizadas obligatorias
- ✅ **Whitelist/Blacklist**: Solo permite SELECT, bloquea DROP/DELETE/etc
- ✅ **Timeouts**: Límites de tiempo en consultas
- ✅ **Validación de entrada**: Sanitización de inputs del usuario
- ✅ **Connection pooling**: Gestión segura de conexiones
- ✅ **Audio validation**: Formato y tamaño de archivos de voz
- ✅ **Type validation**: Pydantic models en FastAPI

---

## 📝 Logs

Los logs se guardan en `/logs` con rotación automática:

```
logs/
├── EvoDataAgent.log      # Log principal
├── MCPConnector.log      # Logs de DB
├── Visualizer.log        # Logs de gráficos
├── ExcelGenerator.log    # Logs de Excel
├── Calculator.log        # Logs de cálculos
├── MessageProcessor.log   # Logs de voz
└── WhatsAppService.log    # Logs de WhatsApp
```

---

## 🎨 Patrones de Diseño Implementados

- ✅ **Singleton**: Tools (una instancia compartida)
- ✅ **Strategy**: IntentRouter (clasificación pluggable)
- ✅ **Template Method**: Tool base class
- ✅ **Dependency Injection**: FastAPI dependencies
- ✅ **Service Layer**: Separación de responsabilidades (SRP)

---

## 🐛 Troubleshooting

### Error: "No module named 'scipy'"

```bash
pip install scipy
```

### Error: "Could not connect to PostgreSQL"

Verifica que PostgreSQL esté corriendo:
```bash
# Windows
net start postgresql-x64-14
```

### Error: "OpenAI API key not found"

Asegúrate de tener `OPENAI_API_KEY` en tu `.env`.

### Webhook no recibe mensajes

1. Verifica que el servidor esté corriendo: `http://localhost:5000/health`
2. Configura la URL pública en EvolutionAPI
3. Verifica los logs: `logs/WebhookServer.log`

---

## 📚 Documentación Completa

### Services

- `MessageProcessor`: Transcripción de voz y validación
- `WhatsAppService`: Comunicación con EvolutionAPI
- `IntentRouter`: Clasificación y routing de mensajes

### Tools (implementan `Tool` interface)

- `MCPConnector`: PostgreSQL database operations
- `Visualizer`: Chart generation (matplotlib + plotly)
- `ExcelGenerator`: Professional Excel export
- `Calculator`: Statistical calculations (NUEVO)

Todas las tools retornan `ToolResult`:
```python
@dataclass
class ToolResult:
    status: ToolStatus  # SUCCESS, ERROR, TIMEOUT
    data: Any
    error: Optional[str]
    metadata: Dict[str, Any]
```

---

## 🤝 Contribuir

Para agregar funcionalidades:

1. Para nueva tool: Hereda de `Tool` base class
2. Para nuevo servicio: Crea en `/services`
3. Para nueva estrategia de intent: Implementa `IntentStrategy`
4. Agrega ejemplos en `/examples`
5. Actualiza tests en `/tests`

---

## 📄 Licencia

Este proyecto es propiedad de **M.C.T. SAS** - 2024

---

## 🔄 Versiones

- **v2.0.0** (2026-01-02): Refactorización SOLID
  - Arquitectura por capas (services)
  - Tool interface common
  - Calculator tool agregado
  - Strategy Pattern para intents
  - FastAPI async/background tasks
  - Audio validation mejorada
  
- **v1.0.0** (2024-12-23): Release inicial
  - PostgreSQL integration
  - OpenAI Whisper support
  - Dual delivery (attachment + URL)
  - 3 tools completos

---

¡Listo para usar! 🚀  
**Documentación interactiva**: http://localhost:5000/docs
