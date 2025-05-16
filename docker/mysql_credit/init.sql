CREATE DATABASE IF NOT EXISTS banco;
USE banco;

CREATE TABLE IF NOT EXISTS tarjetas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_tarjeta VARCHAR(16) UNIQUE NOT NULL COMMENT 'Número único de tarjeta',
    cvv CHAR(3) NOT NULL COMMENT 'Código de seguridad de 3 dígitos',
    fecha_expiracion DATE NOT NULL,
    limite_credito DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    saldo_actual DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    estado ENUM('ACTIVA', 'BLOQUEADA', 'VENCIDA') DEFAULT 'ACTIVA'
);

CREATE TABLE IF NOT EXISTS cliente_tarjeta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL COMMENT 'ID del cliente en BD de sucursales',
    tarjeta_id INT NOT NULL,
    fecha_asignacion DATE DEFAULT (CURRENT_DATE),
    FOREIGN KEY (tarjeta_id) REFERENCES tarjetas(id)
);

-- Usuario de lectura/escritura para ProxySQL o Flask
CREATE USER IF NOT EXISTS 'read_credit'@'%' IDENTIFIED WITH mysql_native_password BY 'clave123';
GRANT SELECT, INSERT, UPDATE ON banco.* TO 'read_credit'@'%';

FLUSH PRIVILEGES;
