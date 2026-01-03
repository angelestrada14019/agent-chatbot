-- Crear tabla de ventas
CREATE TABLE IF NOT EXISTS ventas (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    producto VARCHAR(100),
    categoria VARCHAR(50),
    cantidad INTEGER,
    precio DECIMAL(10, 2),
    total DECIMAL(10, 2)
);

-- Insertar datos de prueba
INSERT INTO ventas (fecha, producto, categoria, cantidad, precio, total) VALUES
('2023-10-01 10:00:00', 'Laptop Gamer X1', 'Electrónica', 1, 1500.00, 1500.00),
('2023-10-01 11:30:00', 'Mouse Inalámbrico', 'Accesorios', 2, 25.50, 51.00),
('2023-10-02 09:15:00', 'Monitor 4K 27"', 'Electrónica', 1, 450.00, 450.00),
('2023-10-02 14:20:00', 'Teclado Mecánico', 'Accesorios', 1, 89.99, 89.99),
('2023-10-03 16:45:00', 'Silla Ergonómica', 'Muebles', 1, 250.00, 250.00),
('2023-10-04 10:00:00', 'Escritorio Ajustable', 'Muebles', 1, 350.00, 350.00),
('2023-10-05 11:00:00', 'Webcam HD', 'Accesorios', 3, 60.00, 180.00),
('2023-10-05 15:30:00', 'Auriculares Noise Cancelling', 'Audio', 1, 200.00, 200.00),
('2023-10-06 09:00:00', 'Smartphone Z5', 'Electrónica', 2, 800.00, 1600.00),
('2023-10-07 13:00:00', 'Tablet Pro 11', 'Electrónica', 1, 700.00, 700.00);
