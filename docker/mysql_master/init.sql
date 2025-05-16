CREATE DATABASE IF NOT EXISTS banco;

USE banco;

CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100),
    correo VARCHAR(100)
);

INSERT INTO clientes (nombre, correo) VALUES ('Juan', 'juan@banco.com');

-- Crear usuario para replicación con plugin compatible
CREATE USER IF NOT EXISTS 'replica'@'%' IDENTIFIED WITH mysql_native_password BY 'replica123';
GRANT REPLICATION SLAVE ON *.* TO 'replica'@'%';
FLUSH PRIVILEGES;

-- Crear usuario técnico para ProxySQL
CREATE USER IF NOT EXISTS 'flask_user'@'%' IDENTIFIED BY 'flask_pass';
GRANT ALL PRIVILEGES ON *.* TO 'flask_user'@'%';
FLUSH PRIVILEGES;