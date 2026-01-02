# MCP Server Simulator

Servidor MCP que implementa el protocolo Model Context Protocol para PostgreSQL.

## Características

- ✅ Implementa protocolo MCP estándar
- ✅ Comunicación vía stdio (JSON-RPC)
- ✅ Datos simulados para testing
- ✅ 3 herramientas: query, list_tables, get_schema
- ✅ Recursos dinámicos (tablas)

## Instalación

```bash
cd mcp-server
pip install -r requirements.txt
```

## Uso

### Ejecutar directamente

```bash
python server.py
```

### Ejecutar con Docker

```bash
docker build -t mcp-server .
docker run -it mcp-server
```

## Datos Simulados

El servidor incluye 3 tablas simuladas:

- `ventas`: 5 registros de ventas
- `productos`: 5 productos
- `clientes`: 3 clientes

## Herramientas Disponibles

### 1. query

Ejecuta una query SQL (simulada).

```json
{
  "name": "query",
  "arguments": {
    "sql": "SELECT * FROM ventas",
    "params": {}
  }
}
```

### 2. list_tables

Lista todas las tablas.

```json
{
  "name": "list_tables",
  "arguments": {}
}
```

### 3. get_schema

Obtiene schema de una tabla.

```json
{
  "name": "get_schema",
  "arguments": {
    "table_name": "ventas"
  }
}
```

## Recursos

Recursos expuestos:

- `postgres://analytics/ventas`
- `postgres://analytics/productos`
- `postgres://analytics/clientes`

## Logs

Los logs se guardan en `mcp-server.log`
