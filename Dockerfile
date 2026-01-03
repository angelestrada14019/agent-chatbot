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

# Dar permisos al entrypoint
RUN chmod +x entrypoint.sh

# Exponer puertos
EXPOSE 5000 8001

# Comando de inicio usando el script
ENTRYPOINT ["./entrypoint.sh"]
