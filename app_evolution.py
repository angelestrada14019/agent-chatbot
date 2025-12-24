import requests

# 🔧 Configuración Evolution API
EVOLUTION_URL = "http://82.25.93.102:8080/"   # Cambia por tu dominio o IP
INSTANCE = "clientes"                                 # Nombre de la instancia Evolution
API_KEY = "123456.+az154721ww"                           # Pega tu API key
NUMERO_DESTINO = "573124488445@c.us"                  # Número de WhatsApp destino (con @c.us)


# ==================================
# 💬 FUNCIÓN PARA ENVIAR MENSAJES
# ==================================
def enviar_mensaje_estado(estado, datos):
    """
    Envía un mensaje por Evolution API dependiendo del estado del vehículo.
    Estados válidos: 'cargando', 'en_ruta', 'mitad', 'proximo'

    Returns:
        tuple: (success: bool, response_data: dict, error_message: str)
    """

    cliente = datos.get("cliente", "Cliente")
    documento_cliente = datos.get("documento_cliente", "N/A")
    manifiesto = datos.get("manifiesto", "N/A")
    placa = datos.get("placa", "N/A")
    operacion = datos.get("operacion", "N/A")
    ciudad_origen = datos.get("ciudad_origen", "N/A")
    ciudad_destino = datos.get("ciudad_destino", "N/A")
    hora_reporte = datos.get("hora_reporte", "")
    hora_salida = datos.get("hora_salida", "")
    km_restantes = datos.get("km_restantes", 0)
    min_restantes = datos.get("min_restantes", 0)
    hora_estimada = datos.get("hora_estimada", "")

    # ======================
    # 📦 MENSAJES POR ESTADO
    # ======================
    if estado == "cargando":
        mensaje = (
            f"🚛 *Actualización de su envío*\n\n"
            f"👤 *Cliente:* {cliente}\n"
            f"📄 *Documento de viaje:* {documento_cliente}\n"
            f"📦 *Manifiesto:* {manifiesto}\n"
            f"🚗 *Placa del vehículo:* {placa}\n"
            f"🔧 *Operación:* {operacion}\n"
            f"📍 *Origen:* {ciudad_origen}\n"
            f"📍 *Destino:* {ciudad_destino}\n\n"
            f"📍 El vehículo se encuentra actualmente *en proceso de cargue*\n"
            f"🕒 *Hora del reporte:* {hora_reporte}\n\n"
            f"Pronto iniciará su recorrido hacia el destino. Gracias por su confianza en *M.C.T. SAS*. 🤝"
        )

    elif estado == "en_ruta":
        mensaje = (
            f"🚛 *Actualización de su envío*\n\n"
            f"👤 *Cliente:* {cliente}\n"
            f"📄 *Documento de viaje:* {documento_cliente}\n"
            f"📦 *Manifiesto:* {manifiesto}\n"
            f"🚗 *Placa del vehículo:* {placa}\n\n"
            f"✅ El vehículo ha *iniciado su ruta* hacia el punto de entrega.\n"
            f"🕒 *Hora de salida:* {hora_salida}\n\n"
            f"Nuestro equipo de monitoreo realiza seguimiento en tiempo real para garantizar una llegada segura y puntual. 🚚💨"
        )

    elif estado == "mitad":
        mensaje = (
            f"🚛 *Actualización de su envío*\n\n"
            f"👤 *Cliente:* {cliente}\n"
            f"📄 *Documento de viaje:* {documento_cliente}\n"
            f"📦 *Manifiesto:* {manifiesto}\n"
            f"🚗 *Placa del vehículo:* {placa}\n\n"
            f"📍 El vehículo se encuentra *a mitad del trayecto* hacia su destino.\n"
            f"🛣️ *Distancia restante:* {km_restantes} km\n"
            f"⏱️ *Tiempo estimado restante:* {min_restantes} minutos\n"
            f"🕓 *Hora estimada de llegada:* {hora_estimada}\n\n"
            f"El recorrido avanza según lo programado. Gracias por elegir *M.C.T. SAS*. 🚚📦"
        )

    elif estado == "proximo":
        mensaje = (
            f"🚛 *Actualización de su envío*\n\n"
            f"👤 *Cliente:* {cliente}\n"
            f"📄 *Documento de viaje:* {documento_cliente}\n"
            f"📦 *Manifiesto:* {manifiesto}\n"
            f"🚗 *Placa del vehículo:* {placa}\n\n"
            f"📍 El vehículo se encuentra *próximo a llegar al punto de descargue*.\n"
            f"🛣️ *Distancia restante:* {km_restantes} km\n"
            f"⏱️ *Tiempo estimado:* {min_restantes} minutos\n"
            f"🕓 *Hora estimada de llegada:* {hora_estimada}\n\n"
            f"Por favor aliste el área de recepción. Gracias por confiar en *M.C.T. SAS*. 🤝"
        )

    else:
        error_msg = "Estado no válido. Use: 'cargando', 'en_ruta', 'mitad' o 'proximo'"
        print(f"⚠️ {error_msg}")
        return (False, None, error_msg)

    # ============================
    # 🚀 ENVÍO POR EVOLUTION API
    # ============================
    url = f"{EVOLUTION_URL}/message/sendText/{INSTANCE}"
    headers = {"Content-Type": "application/json", "apikey": API_KEY}
    payload = {
        "number": NUMERO_DESTINO,
        "options": {"delay": 1000, "presence": "composing", "linkPreview": False},
        "text": mensaje
    }

    try:
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code in (200, 201):
            print(f"✅ Mensaje '{estado}' enviado correctamente")
            response_data = response.json()
            print(response_data)
            return (True, response_data, None)
        else:
            error_msg = f"Error {response.status_code}: {response.text}"
            print(f"❌ Error al enviar el mensaje '{estado}': {error_msg}")
            return (False, None, error_msg)
    except Exception as e:
        error_msg = f"Excepción al enviar mensaje: {str(e)}"
        print(f"❌ {error_msg}")
        return (False, None, error_msg)


# =====================================
# 🧪 EJEMPLO DE USO / PRUEBA DE ENVÍO
# =====================================
if __name__ == "__main__":
    datos_prueba = {
        "cliente": "Sebastián Flórez",
        "documento_cliente": "DOC-7788",
        "manifiesto": "MF-2211",
        "placa": "TXY456",
        "hora_reporte": "13:10",
        "hora_salida": "13:30",
        "km_restantes": 5,
        "min_restantes": 12,
        "hora_estimada": "14:35"
    }

    # Prueba: enviar mensaje de "vehículo próximo a llegar"
    enviar_mensaje_estado("proximo", datos_prueba)
