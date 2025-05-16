CREATE DATABASE IF NOT EXISTS banco;
USE banco;

CREATE USER IF NOT EXISTS 'read_sucursal2'@'%' IDENTIFIED WITH mysql_native_password BY 'clave123';
GRANT SELECT ON banco.* TO 'read_sucursal2'@'%';

FLUSH PRIVILEGES;
