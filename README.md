# 🤖 EvoDataAgent

**Agente inteligente de análisis y automatización** integrado con EvolutionAPI y PostgreSQL. Procesa mensajes de texto/voz, ejecuta consultas SQL, genera visualizaciones y exporta datos a Excel.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-green.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-Whisper-orange.svg)

---

## 🎯 Características

- 🎤 **Procesamiento de voz**: Transcripción automática con OpenAI Whisper API
- 🗄️ **Conexión PostgreSQL**: Consultas seguras con validación anti-SQL injection
- 📊 **Visualizaciones profesionales**: Gráficos con matplotlib, plotly y seaborn
- 📁 **Exportación Excel**: Archivos formateados con estilos corporativos
- 💬 **Integración WhatsApp**: Envío de mensajes y archivos via EvolutionAPI
- 🔄 **Dual delivery**: Archivos como adjuntos Y URLs de descarga
- 🧠 **Clasificación de intenciones**: Procesamiento inteligente de lenguaje natural

---

## 📋 Requisitos Previos

- Python 3.11 o superior
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
```

---

## 📊 Arquitectura

```
evodata_agent.py          # 🤖 Orquestador principal
├── tools/
│   ├── mcp_connector.py  # 🗄️ Tool 1: PostgreSQL connector
│   ├── visualizer.py     # 📈 Tool 2: Generador de gráficos
│   └── excel_generator.py # 📁 Tool 3: Exportador Excel
├── utils/
│   ├── logger.py         # 📝 Sistema de logging
│   └── response_formatter.py # 📤 Formateador de respuestas
├── config.py             # ⚙️ Configuración centralizada
├── file_server.py        # 🌐 Servidor de archivos
└── examples/
    └── example_queries.py # 📚 Ejemplos de uso
```

---

## 💻 Uso Básico

### Ejemplo 1: Consulta Simple

```python
from evodata_agent import EvoDataAgent

agent = EvoDataAgent()
response = agent.process_message("Muéstrame las ventas de este mes")
print(response["content"])
```

### Ejemplo 2: Generar Gráfico

```python
response = agent.process_message("Dame un gráfico de ventas por categoría")
# El gráfico se guarda y se puede enviar por WhatsApp
```

### Ejemplo 3: Exportar Excel

```python
response = agent.process_message("Exporta las ventas del trimestre a Excel")
# Excel generado en /exports con formato profesional
```

### Ejemplo 4: Mensaje de Voz

```python
response = agent.process_message(
    "",
    is_voice=True,
    audio_path="ruta/al/audio.ogg"
)
# Transcribe automáticamente y procesa
```

---

## 🛠️ Uso Avanzado: Herramientas Directas

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

---

## 💬 Integración con WhatsApp

### Enviar Mensaje

```python
agent = EvoDataAgent()

# Procesar y enviar
response = agent.process_message("Muéstrame ventas de hoy")
agent.send_whatsapp_message("573124488445@c.us", response)
```

### Webhook (Recibir Mensajes)

Crea un endpoint que reciba webhooks de EvolutionAPI:

```python
from flask import Flask, request
from evodata_agent import EvoDataAgent

app = Flask(__name__)
agent = EvoDataAgent()

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    message = data['message']
    number = data['number']
    
    # Procesar
    response = agent.process_message(message)
    
    # Responder
    agent.send_whatsapp_message(number, response)
    
    return {"status": "ok"}
```

---

## 🌐 Servidor de Archivos

Para servir archivos vía URLs (modo dual delivery):

```bash
python file_server.py
```

Esto iniciará un servidor en `http://localhost:8000` que servirá:
- Gráficos: `http://localhost:8000/exports/bar_chart_20241223_193000.png`
- Excel: `http://localhost:8000/exports/export_12345.xlsx`

---

## 🧪 Ejemplos Completos

Ejecuta los ejemplos incluidos:

```bash
python examples/example_queries.py
```

Incluye 7 ejemplos:
1. ✅ Consulta simple
2. ✅ Visualización
3. ✅ Exportación Excel
4. ✅ Procesamiento de voz
5. ✅ Uso directo de tools
6. ✅ Excel multi-hoja
7. ✅ Integración WhatsApp completa

---

## 🔒 Seguridad

El agente implementa múltiples capas de seguridad:

- ✅ **SQL Injection Prevention**: Queries parametrizadas obligatorias
- ✅ **Whitelist/Blacklist**: Solo permite SELECT, bloquea DROP/DELETE/etc
- ✅ **Timeouts**: Límites de tiempo en consultas
- ✅ **Validación de entrada**: Sanitización de inputs del usuario
- ✅ **Connection pooling**: Gestión segura de conexiones

---

## 📝 Logs

Los logs se guardan en `/logs` con rotación automática:

```
logs/
├── EvoDataAgent.log      # Log principal
├── MCPConnector.log      # Logs de DB
├── Visualizer.log        # Logs de gráficos
└── ExcelGenerator.log    # Logs de Excel
```

Formato JSON para fácil parsing:
```json
{
  "asctime": "2024-12-23 19:30:00",
  "name": "EvoDataAgent",
  "levelname": "INFO",
  "message": "Nueva solicitud recibida",
  "request_id": "abc-123",
  "user_number": "573124488445@c.us"
}
```

---

## 🎨 Personalización

### Cambiar colores corporativos

Edita `config.py`:

```python
COMPANY_COLOR_PRIMARY = "#1f77b4"  # Tu color
COMPANY_COLOR_SECONDARY = "#ff7f0e"
```

### Agregar nuevos tipos de gráficos

Extiende `tools/visualizer.py`:

```python
def create_my_custom_chart(self, data, ...):
    # Tu implementación
    pass
```

### Personalizar estilos Excel

Modifica `tools/excel_generator.py` en `_apply_professional_styling()`.

---

## 🐛 Troubleshooting

### Error: "No module named 'psycopg2'"

```bash
pip install psycopg2-binary
```

### Error: "Could not connect to PostgreSQL"

Verifica que PostgreSQL esté corriendo:
```bash
# Windows
net start postgresql-x64-14
```

### Error: "OpenAI API key not found"

Asegúrate de tener `OPENAI_API_KEY` en tu `.env`.

### Gráficos no se generan

Instala kaleido para Plotly:
```bash
pip install kaleido
```

---

## 📚 Documentación de APIs

### EvoDataAgent

- `process_message(message, is_voice, audio_path)`: Procesa mensaje
- `send_whatsapp_message(phone_number, response)`: Envía por WhatsApp

### MCPConnector

- `execute_query(sql, params, timeout)`: Ejecuta consulta SQL
- `call_stored_procedure(name, params)`: Llama procedimiento
- `get_schema_info(table_name)`: Info de tabla

### Visualizer

- `create_bar_chart(...)`: Gráfico de barras
- `create_line_chart(...)`: Gráfico de líneas
- `create_pie_chart(...)`: Gráfico de torta
- `create_scatter_plot(...)`: Dispersión
- `create_interactive_plotly(...)`: Interactivo

### ExcelGenerator

- `create_excel_from_data(...)`: Excel simple
- `create_multi_sheet_excel(...)`: Multi-hoja
- `add_chart_to_excel(...)`: Agrega gráfico

---

## 🤝 Contribuir

Para agregar funcionalidades:

1. Crea nueva tool en `/tools`
2. Registra en `evodata_agent.py`
3. Actualiza `IntentClassifier` si es necesario
4. Agrega ejemplos en `/examples`

---

## 📄 Licencia

Este proyecto es propiedad de **M.C.T. SAS** - 2024

---

## 👤 Autor

**EvoDataAgent** - Desarrollado para M.C.T. SAS

Para soporte: contacto@mctsas.com

---

## 🔄 Versiones

- **v1.0.0** (2024-12-23): Release inicial
  - PostgreSQL integration
  - OpenAI Whisper support
  - Dual delivery (attachment + URL)
  - 3 tools completos

---

¡Listo para usar! 🚀
