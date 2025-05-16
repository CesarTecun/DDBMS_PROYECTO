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

-- Usuario de lectura/escritura para ProxySQL o Flask
CREATE USER IF NOT EXISTS 'read_mercadeo'@'%' IDENTIFIED WITH mysql_native_password BY 'clave123';
GRANT SELECT, INSERT, UPDATE ON banco.* TO 'read_mercadeo'@'%';

FLUSH PRIVILEGES;
