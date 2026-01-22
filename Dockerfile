FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p logs exports temp

# Convertir line endings (CRLF -> LF) y dar permisos al entrypoint
# Esto soluciona problemas de compatibilidad cuando el repo se clona en Windows
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

# Exponer puertos
EXPOSE 5000 8001

# Comando de inicio usando el script
ENTRYPOINT ["./entrypoint.sh"]
