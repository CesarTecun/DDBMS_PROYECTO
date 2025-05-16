-- Crear base de datos si no existe
CREATE DATABASE IF NOT EXISTS banco;
USE banco;

-- Crear usuario solo de lectura con plugin compatible
CREATE USER IF NOT EXISTS 'read_sucursal1'@'%' IDENTIFIED WITH mysql_native_password BY 'clave123';

-- Conceder solo SELECT sobre la base de datos 'banco'
GRANT SELECT ON banco.* TO 'read_sucursal1'@'%';

-- Aplicar cambios
FLUSH PRIVILEGES;
