CREATE DATABASE IF NOT EXISTS banco;
USE banco;

CREATE TABLE IF NOT EXISTS campana (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    tipo ENUM('CORREO', 'SMS', 'LLAMADA', 'PRESENCIAL') DEFAULT 'CORREO',
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS cliente_campana (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    campana_id INT NOT NULL,
    resultado ENUM('POSITIVO', 'NEUTRO', 'NEGATIVO') DEFAULT 'NEUTRO',
    observaciones TEXT,
    fecha_asignacion DATE DEFAULT (CURRENT_DATE),
    FOREIGN KEY (campana_id) REFERENCES campana(id)
);

-- Crear usuario técnico para ProxySQL
CREATE USER IF NOT EXISTS 'flask_user'@'%' IDENTIFIED BY 'flask_pass';
GRANT ALL PRIVILEGES ON *.* TO 'flask_user'@'%';
FLUSH PRIVILEGES;