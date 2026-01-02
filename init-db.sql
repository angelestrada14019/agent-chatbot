-- Script de inicialización de PostgreSQL
-- Crea tablas de ejemplo para EvoDataAgent

CREATE TABLE IF NOT EXISTS ventas (
    id SERIAL PRIMARY KEY,
    producto VARCHAR(100) NOT NULL,
    cantidad INTEGER NOT NULL,
    precio DECIMAL(10, 2) NOT NULL,
    fecha DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    precio_unitario DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    ciudad VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar datos de ejemplo
INSERT INTO ventas (producto, cantidad, precio, fecha) VALUES
    ('Laptop', 10, 1200.00, '2024-01-15'),
    ('Mouse', 50, 25.00, '2024-01-16'),
    ('Teclado', 30, 75.00, '2024-01-17'),
    ('Monitor', 15, 350.00, '2024-01-18'),
    ('Webcam', 20, 85.00, '2024-01-19'),
    ('Audífonos', 40, 45.00, '2024-01-20'),
    ('Impresora', 8, 200.00, '2024-01-21'),
    ('Scanner', 12, 150.00, '2024-01-22'),
    ('Router', 25, 80.00, '2024-01-23'),
    ('Switch', 18, 120.00, '2024-01-24');

INSERT INTO productos (nombre, categoria, stock, precio_unitario) VALUES
    ('Laptop', 'Computadoras', 50, 1200.00),
    ('Mouse', 'Accesorios', 200, 25.00),
    ('Teclado', 'Accesorios', 150, 75.00),
    ('Monitor', 'Pantallas', 75, 350.00),
    ('Webcam', 'Video', 100, 85.00),
    ('Audífonos', 'Audio', 120, 45.00),
    ('Impresora', 'Impresión', 40, 200.00),
    ('Scanner', 'Impresión', 30, 150.00),
    ('Router', 'Redes', 60, 80.00),
    ('Switch', 'Redes', 45, 120.00);

INSERT INTO clientes (nombre, email, telefono, ciudad) VALUES
    ('Juan Pérez', 'juan@example.com', '3001234567', 'Bogotá'),
    ('María García', 'maria@example.com', '3007654321', 'Medellín'),
    ('Carlos López', 'carlos@example.com', '3009876543', 'Cali'),
    ('Ana Martínez', 'ana@example.com', '3005555555', 'Barranquilla'),
    ('Luis Rodríguez', 'luis@example.com', '3004444444', 'Cartagena');

-- Crear índices para mejorar rendimiento
CREATE INDEX idx_ventas_fecha ON ventas(fecha);
CREATE INDEX idx_ventas_producto ON ventas(producto);
CREATE INDEX idx_productos_categoria ON productos(categoria);
CREATE INDEX idx_clientes_ciudad ON clientes(ciudad);

-- Crear vista para análisis
CREATE OR REPLACE VIEW vista_ventas_resumen AS
SELECT 
    v.producto,
    COUNT(*) as total_transacciones,
    SUM(v.cantidad) as total_unidades,
    SUM(v.cantidad * v.precio) as total_ingresos,
    AVG(v.precio) as precio_promedio,
    p.categoria
FROM ventas v
LEFT JOIN productos p ON v.producto = p.nombre
GROUP BY v.producto, p.categoria;

COMMENT ON TABLE ventas IS 'Registro de todas las ventas realizadas';
COMMENT ON TABLE productos IS 'Catálogo de productos disponibles';
COMMENT ON TABLE clientes IS 'Información de clientes registrados';
COMMENT ON VIEW vista_ventas_resumen IS 'Vista resumida de ventas con análisis agregado';
