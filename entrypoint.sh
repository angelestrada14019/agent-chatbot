#!/bin/bash
set -e

echo "============================================"
echo "🚀 Starting EvoDataAgent Core Services"
echo "============================================"
echo "Webhook Port: $WEBHOOK_SERVER_PORT"
echo "File Server Port: $FILE_SERVER_PORT"
echo "Evolution URL: $EVOLUTION_URL"
echo "MCP Server URL: $MCP_SERVER_URL"
echo "============================================"

# Iniciar File Server en background
echo "📂 Starting File Server (Background)..."
python file_server.py &
FILE_SERVER_PID=$!

# Iniciar Webhook Server en foreground
echo "📡 Starting Webhook Server (Foreground)..."
exec uvicorn webhook_server:app --host 0.0.0.0 --port $WEBHOOK_SERVER_PORT
