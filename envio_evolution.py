import requests, base64, mimetypes, os

EVOLUTION_URL = "http://82.25.93.102:8080"
INSTANCE = "clientes"
API_KEY = "123456.+az154721ww"
NUMERO_DESTINO = "573124488445"

def enviar_archivo(ruta, mensaje="📎 Archivo adjunto desde M.C.T. SAS"):
    if not os.path.exists(ruta):
        print("❌ El archivo no existe:", ruta)
        return

    # Forzar lectura binaria sin importar extensión
    with open(ruta, "rb") as f:
        contenido_b64 = base64.b64encode(f.read()).decode("utf-8")

    nombre = os.path.basename(ruta)
    mime, _ = mimetypes.guess_type(ruta)
    if mime is None:
        mime = "application/octet-stream"

    # Forzar tipo documento para CSV / TXT
    mediatype = "document"

    payload = {
        "number": NUMERO_DESTINO,
        "mediatype": mediatype,
        "mimetype": mime,
        "media": contenido_b64,
        "fileName": nombre,
        "caption": mensaje,
        "delay": 1000,
        "linkPreview": False
    }

    url = f"{EVOLUTION_URL}/message/sendMedia/{INSTANCE}"
    headers = {"Content-Type": "application/json", "apikey": API_KEY}

    r = requests.post(url, json=payload, headers=headers)

    if r.status_code in (200, 201):
        print(f"✅ '{nombre}' enviado correctamente")
    else:
        print(f"❌ Error al enviar '{nombre}':", r.status_code, r.text)


if __name__ == "__main__":
    # ✅ PDF (funciona normal)
    enviar_archivo("/home/sebastian/Documentos/python/envio_whatsapp_clientes/invoice.pdf",
                   "📄 Factura de despacho MF-2211")

    # ✅ CSV (forzado como documento binario)
    enviar_archivo("/home/sebastian/Documentos/python/envio_whatsapp_clientes/data.xlsx",
                   "📊 Reporte de ruta actualizado")

