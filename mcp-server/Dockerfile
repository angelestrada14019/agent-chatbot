FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar servidor
COPY server.py .

# Variables de entorno por defecto
ENV DB_HOST=postgres
ENV DB_PORT=5432
ENV DB_NAME=analytics
ENV DB_USER=postgres
ENV DB_PASSWORD=postgres

# Ejecutar servidor
CMD ["python", "server.py"]
