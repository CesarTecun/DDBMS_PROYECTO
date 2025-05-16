CREATE DATABASE IF NOT EXISTS banco_admin;
USE banco_admin;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    rol ENUM('admin', 'sucursal', 'credit', 'mercadeo', 'transacciones') NOT NULL,
    sucursal ENUM('sucursal1', 'sucursal2', 'sucursal3', 'creditos', 'mercadeo') DEFAULT NULL,
    activo BOOLEAN DEFAULT TRUE
);

INSERT INTO usuarios (username, password, rol, sucursal) VALUES
('admin', 'admin123', 'admin', NULL),
('cajero_s1', 'clave1', 'sucursal', 'sucursal1'),
('cajero_s2', 'clave2', 'sucursal', 'sucursal2'),
('cajero_s3', 'clave3', 'sucursal', 'sucursal3'),
('tarjetas1', 'tarjeta456', 'credit', 'creditos'),
('marketing1', 'mk2024', 'mercadeo', 'mercadeo');

-- Crear usuario técnico para ProxySQL
CREATE USER IF NOT EXISTS 'flask_user'@'%' IDENTIFIED BY 'flask_pass';
GRANT ALL PRIVILEGES ON *.* TO 'flask_user'@'%';
FLUSH PRIVILEGES;