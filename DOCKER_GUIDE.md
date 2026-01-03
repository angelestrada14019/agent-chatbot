# 🐳 Guía de Despliegue con Docker

## 📋 Requisitos Previos

- Docker Desktop instalado
- Docker Compose instalado
- Archivo `.env` configurado

---

## 🚀 Inicio Rápido

### 1. Clonar variables de entorno

```bash
copy .env.example .env
```

Editar `.env` con tus credenciales:
```bash
OPENAI_API_KEY=sk-tu-key-aqui
EVOLUTION_URL=http://tu-evolution-api:8080/
EVOLUTION_INSTANCE=tu-instancia
EVOLUTION_API_KEY=tu-api-key
```

### 2. Levantar todos los servicios

```bash
docker-compose up -d
```

Esto levanta:
- ✅ **PostgreSQL** (puerto 5432)
- ✅ **MCP Server** (interno, comunicación stdio)
- ✅ **Webhook Server** (puerto 5000)
- ✅ **File Server** (puerto 8001)

### 3. Verificar logs

```bash
# Ver todos los logs
docker-compose logs -f

# Ver logs específicos
docker-compose logs -f webhook-server
docker-compose logs -f mcp-server
docker-compose logs -f postgres
```

### 4. Verificar estado

```bash
# Health check del webhook
curl http://localhost:5000/health

# Health check del file server
curl http://localhost:8001/health

# Documentación API
# Abrir en navegador:
http://localhost:5000/docs
http://localhost:8001/docs
```

---

## 🏗️ Arquitectura Docker

```
┌─────────────────────────────────────────────────────┐
│                Docker Network                        │
│  evodata-network (bridge)                           │
│                                                      │
│  ┌──────────────┐  ┌───────────────┐               │
│  │  PostgreSQL  │  │  MCP Server   │               │
│  │  (port 5432) │◄─┤  (stdio)      │               │
│  └──────────────┘  └───────┬───────┘               │
│                             │                        │
│  ┌─────────────────────────┴────────────────┐      │
│  │         Webhook Server                    │      │
│  │         (port 5000)                       │      │
│  │  - Recibe webhooks EvolutionAPI          │      │
│  │  - Usa MCP Client → MCP Server           │      │
│  │  - Procesa mensajes                       │      │
│  └───────────────────────────────────────────┘      │
│                                                      │
│  ┌───────────────────────────────────────────┐      │
│  │         File Server                        │      │
│  │         (port 8001)                       │      │
│  │  - Sirve archivos generados               │      │
│  └───────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────┘
```

---

## 📦 Servicios Individuales

### PostgreSQL

```bash
# Detener/Iniciar solo PostgreSQL
docker-compose stop postgres
docker-compose start postgres

# Conectar a PostgreSQL
docker exec -it evodata-postgres psql -U postgres -d analytics

# Ver tablas
\dt

# Query de ejemplo
SELECT * FROM ventas LIMIT 5;
```

### MCP Server

```bash
# Ver logs del MCP Server
docker-compose logs -f mcp-server

# El servidor MCP se comunica vía stdio con webhook-server
# No tiene puerto HTTP expuesto
```

### Webhook Server

```bash
# Reiniciar webhook server
docker-compose restart webhook-server

# Ver logs en tiempo real
docker-compose logs -f webhook-server

# Ejecutar comando dentro del contenedor
docker exec -it evodata-webhook python -c "from tools.mcp_client import get_mcp_client; print('MCP OK')"
```

### File Server

```bash
# Reiniciar file server
docker-compose restart file-server

# Ver archivos generados
docker exec -it evodata-fileserver ls -la /app/exports
```

---

## 🛠️ Comandos Útiles

### Construcción y Despliegue

```bash
# Construir imágenes
docker-compose build

# Construir sin cache
docker-compose build --no-cache

# Levantar en foreground (ver logs directamente)
docker-compose up

# Levantar en background
docker-compose up -d

# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (⚠️ BORRA DATOS)
docker-compose down -v
```

### Depuración

```bash
# Entrar a contenedor
docker exec -it evodata-webhook bash

# Ver uso de recursos
docker stats

# Inspeccionar red
docker network inspect chatbot_evodata-network

# Ver volúmenes
docker volume ls
docker volume inspect chatbot_postgres_data
```

### Logs y Monitoreo

```bash
# Logs de todos los servicios
docker-compose logs

# Logs con timestamp
docker-compose logs -t

# Últimas 100 líneas
docker-compose logs --tail=100

# Seguir logs en tiempo real
docker-compose logs -f webhook-server

# Logs de PostgreSQL
docker-compose logs postgres | grep ERROR
```

---

## 🔧 Configuración Avanzada

### Variables de Entorno

El archivo `.env` se carga automáticamente en `docker-compose.yml`.

Variables importantes:

```bash
# OpenAI
OPENAI_API_KEY=sk-xxx

# EvolutionAPI
EVOLUTION_URL=http://tu-servidor:8080/
EVOLUTION_INSTANCE=instancia
EVOLUTION_API_KEY=xxx

# Database (ya configurado en docker-compose)
DB_HOST=postgres  # Nombre del servicio Docker
DB_PORT=5432
DB_NAME=analytics
DB_USER=postgres
DB_PASSWORD=postgres
```

### Volúmenes Persistentes

```yaml
volumes:
  # Base de datos PostgreSQL (persistente)
  postgres_data:
    driver: local
  
  # Logs (compartido con host)
  - ./logs:/app/logs
  
  # Exports (compartido con host)
  - ./exports:/app/exports
```

### Networking

Todos los servicios están en la red `evodata-network`:

```bash
# Ping entre servicios
docker exec -it evodata-webhook ping postgres
docker exec -it evodata-webhook ping mcp-server
```

---

## 🐛 Troubleshooting

### Error: "Port already in use"

```bash
# Ver qué usa el puerto 5432
netstat -ano | findstr :5432

# Matar proceso (Windows)
taskkill /PID <PID> /F

# O cambiar puerto en docker-compose.yml
ports:
  - "5433:5432"  # Puerto local:Puerto contenedor
```

### Error: "Cannot connect to MCP Server"

```bash
# Verificar que mcp-server está corriendo
docker-compose ps

# Ver logs del MCP Server
docker-compose logs mcp-server

# Reiniciar MCP Server
docker-compose restart mcp-server
```

### Error: "Database connection failed"

```bash
# Verificar PostgreSQL health
docker-compose ps postgres

# Logs de PostgreSQL
docker-compose logs postgres

# Conectar manualmente
docker exec -it evodata-postgres psql -U postgres -d analytics
```

### Error: "MCP SDK not installed"

```bash
# Reconstruir imagen
docker-compose build --no-cache webhook-server

# Verificar requirements.txt incluya mcp>=0.9.0
```

---

## 📊 Monitoreo

### Health Checks

```bash
# Webhook Server
curl http://localhost:5000/health

# File Server
curl http://localhost:8001/health

# PostgreSQL (dentro del contenedor)
docker exec evodata-postgres pg_isready -U postgres
```

### Métricas

```bash
# CPU/Memoria por contenedor
docker stats

# Tamaño de imágenes
docker images | grep evodata

# Espacio usado por volúmenes
docker system df -v
```

---

## 🔄 Actualización

```bash
# 1. Detener servicios
docker-compose down

# 2. Pull cambios de código
git pull  # o actualizar archivos manualmente

# 3. Reconstruir imágenes
docker-compose build

# 4. Levantar servicios
docker-compose up -d

# 5. Verificar
docker-compose logs -f
```

---

## 🧹 Limpieza

```bash
# Detener y eliminar contenedores
docker-compose down

# Eliminar también volúmenes (⚠️ BORRA DATOS)
docker-compose down -v

# Limpiar imágenes no usadas
docker image prune

# Limpiar todo (⚠️ CUIDADO)
docker system prune -a --volumes
```

---

## 🎯 Comandos de Producción

### Despliegue en Servidor

```bash
# En servidor remoto:
git clone <repo>
cd chatbot

# Configurar .env
nano .env

# Levantar
docker-compose up -d

# Verificar
docker-compose ps
docker-compose logs -f
```

### Backup de Base de Datos

```bash
# Backup
docker exec evodata-postgres pg_dump -U postgres analytics > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20240123.sql | docker exec -i evodata-postgres psql -U postgres analytics
```

### Auto-restart

Los servicios tienen `restart: unless-stopped` en docker-compose.yml,
se reinician automáticamente si fallan o si el servidor se reinicia.

---

## 🎉 Verificación Final

Checklist después de `docker-compose up -d`:

- [ ] PostgreSQL corriendo: `docker-compose ps postgres`
- [ ] MCP Server corriendo: `docker-compose ps mcp-server`
- [ ] Webhook Server respondiendo: `curl http://localhost:5000/health`
- ✅ **File Server** (puerto 8001)
- [ ] File Server respondiendo: `curl http://localhost:8001/health`
- [ ] Docs accesibles: `http://localhost:8001/docs`
- [ ] Base de datos con datos: `docker exec evodata-postgres psql -U postgres -d analytics -c "SELECT COUNT(*) FROM ventas;"`

**¡Sistema completo con MCP real funcionando en Docker!** 🚀
