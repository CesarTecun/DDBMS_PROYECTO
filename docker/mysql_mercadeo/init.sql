CREATE DATABASE IF NOT EXISTS mercadeo;
USE mercadeo;

CREATE TABLE IF NOT EXISTS campañas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    tipo ENUM('CORREO', 'SMS', 'LLAMADA', 'PRESENCIAL') DEFAULT 'CORREO',
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS cliente_campaña (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    campaña_id INT NOT NULL,
    resultado ENUM('POSITIVO', 'NEUTRO', 'NEGATIVO') DEFAULT 'NEUTRO',
    observaciones TEXT,
    fecha_asignacion DATE DEFAULT (CURRENT_DATE),
    FOREIGN KEY (campaña_id) REFERENCES campañas(id)
);
