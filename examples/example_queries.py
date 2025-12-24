"""
📚 Example Usage of EvoDataAgent
Ejemplos completos de uso del agente
"""
import pandas as pd
from evodata_agent import EvoDataAgent
from utils.response_formatter import ResponseFormatter

def example_1_simple_query():
    """Ejemplo 1: Consulta simple de datos"""
    print("\n" + "="*60)
    print("📊 EJEMPLO 1: Consulta Simple")
    print("="*60)
    
    agent = EvoDataAgent()
    
    # Procesar mensaje
    response = agent.process_message("Muéstrame las ventas de este mes")
    
    # Mostrar respuesta
    print(ResponseFormatter.to_json(response, pretty=True))
    
    # Simular envío por WhatsApp
    # agent.send_whatsapp_message("573124488445@c.us", response)


def example_2_visualization():
    """Ejemplo 2: Generar visualización"""
    print("\n" + "="*60)
    print("📈 EJEMPLO 2: Visualización")
    print("="*60)
    
    agent = EvoDataAgent()
    
    # Procesar mensaje solicitando gráfico
    response = agent.process_message("Dame un gráfico de ventas por categoría")
    
    print(ResponseFormatter.to_json(response, pretty=True))
    
    # Verificar si se generó el gráfico
    if response["success"] and response["attachments"]:
        print(f"\n✅ Gráfico generado en: {response['data']}")


def example_3_excel_export():
    """Ejemplo 3: Exportar a Excel"""
    print("\n" + "="*60)
    print("📁 EJEMPLO 3: Exportación Excel")
    print("="*60)
    
    agent = EvoDataAgent()
    
    # Procesar mensaje solicitando Excel
    response = agent.process_message("Exporta las ventas del trimestre a Excel")
    
    print(ResponseFormatter.to_json(response, pretty=True))
    
    if response["success"]:
        print(f"\n✅ Excel generado: {response['data']['file_path']}")


def example_4_voice_processing():
    """Ejemplo 4: Procesar mensaje de voz"""
    print("\n" + "="*60)
    print("🎤 EJEMPLO 4: Mensaje de Voz")
    print("="*60)
    
    agent = EvoDataAgent()
    
    # Nota: Necesitas un archivo de audio real
    # audio_path = "path/to/voice_message.ogg"
    # response = agent.process_message("", is_voice=True, audio_path=audio_path)
    
    print("⚠️ Este ejemplo requiere un archivo de audio real")
    print("Descomenta el código y proporciona la ruta del audio")


def example_5_direct_tool_usage():
    """Ejemplo 5: Uso directo de herramientas"""
    print("\n" + "="*60)
    print("🔧 EJEMPLO 5: Uso Directo de Tools")
    print("="*60)
    
    from tools.mcp_connector import get_connector
    from tools.visualizer import get_visualizer
    from tools.excel_generator import get_excel_generator
    
    # 1. Consultar datos
    print("\n1️⃣ Consultando base de datos...")
    db = get_connector()
    result = db.execute_query(
        sql="SELECT categoria, SUM(monto) as total FROM ventas GROUP BY categoria",
        params={}
    )
    
    if result["success"]:
        print(f"✅ {result['row_count']} categorías encontradas")
        data = pd.DataFrame(result["data"])
        print(data)
        
        # 2. Crear visualización
        print("\n2️⃣ Generando visualización...")
        viz = get_visualizer()
        chart_result = viz.create_bar_chart(
            data=data,
            x_column="categoria",
            y_column="total",
            title="Ventas por Categoría"
        )
        
        if chart_result["success"]:
            print(f"✅ Gráfico guardado en: {chart_result['file_path']}")
        
        # 3. Exportar a Excel
        print("\n3️⃣ Exportando a Excel...")
        excel = get_excel_generator()
        excel_result = excel.create_excel_from_data(
            data=data,
            filename="ventas_por_categoria",
            apply_styling=True
        )
        
        if excel_result["success"]:
            print(f"✅ Excel guardado en: {excel_result['file_path']}")
    else:
        print(f"❌ Error en consulta: {result['error']}")


def example_6_multi_sheet_excel():
    """Ejemplo 6: Excel con múltiples hojas"""
    print("\n" + "="*60)
    print("📊 EJEMPLO 6: Excel Multi-Hoja")
    print("="*60)
    
    from tools.excel_generator import get_excel_generator
    
    # Datos de ejemplo
    ventas_df = pd.DataFrame({
        "Mes": ["Enero", "Febrero", "Marzo"],
        "Ventas": [10000, 15000, 12000]
    })
    
    productos_df = pd.DataFrame({
        "Producto": ["A", "B", "C"],
        "Cantidad": [50, 30, 40]
    })
    
    # Crear Excel multi-hoja
    excel = get_excel_generator()
    result = excel.create_multi_sheet_excel(
        sheets_data={
            "Ventas": ventas_df,
            "Productos": productos_df
        },
        filename="reporte_completo"
    )
    
    if result["success"]:
        print(f"✅ Excel con {result['sheet_count']} hojas creado")
        print(f"📁 Ubicación: {result['file_path']}")


def example_7_whatsapp_integration():
    """Ejemplo 7: Integración completa con WhatsApp"""
    print("\n" + "="*60)
    print("💬 EJEMPLO 7: Integración WhatsApp")
    print("="*60)
    
    agent = EvoDataAgent()
    
    # Simular webhook de EvolutionAPI
    # En producción, recibirías esto de un webhook
    incoming_message = {
        "number": "573124488445@c.us",
        "message": "Muéstrame las ventas de hoy"
    }
    
    print(f"📩 Mensaje recibido de: {incoming_message['number']}")
    print(f"💬 Contenido: {incoming_message['message']}")
    
    # Procesar mensaje
    response = agent.process_message(incoming_message["message"])
    
    # Enviar respuesta por WhatsApp
    print("\n📤 Enviando respuesta...")
    # success = agent.send_whatsapp_message(incoming_message["number"], response)
    
    print("⚠️ Descomenta la línea anterior para enviar realmente")
    print(f"\nRespuesta que se enviaría:\n{response['content']}")


if __name__ == "__main__":
    print("""
    🤖 EvoDataAgent - Ejemplos de Uso
    ==================================
    
    Selecciona un ejemplo para ejecutar:
    1. Consulta simple
    2. Generar visualización
    3. Exportar a Excel
    4. Procesar voz
    5. Uso directo de tools
    6. Excel multi-hoja
    7. Integración WhatsApp
    """)
    
    # Ejecutar un ejemplo
    try:
        # Ejecutar ejemplo 5 (más completo y seguro)
        example_5_direct_tool_usage()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n⚠️ Asegúrate de:")
        print("1. Configurar las variables de entorno en .env")
        print("2. Tener PostgreSQL corriendo")
        print("3. Tener los datos de ejemplo en la base de datos")
