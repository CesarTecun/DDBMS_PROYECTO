CREATE DATABASE IF NOT EXISTS banco;
USE banco;

-- Tabla de clientes (con columna sucursal incluida)
CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_completo VARCHAR(100) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    documento_identidad VARCHAR(13) UNIQUE NOT NULL COMMENT 'DPI guatemalteco',
    correo_electronico VARCHAR(100),
    telefono VARCHAR(15) COMMENT 'Formato: 8 dígitos nacionales',
    direccion TEXT,
    municipio VARCHAR(50),
    departamento VARCHAR(50),
    sucursal VARCHAR(50),  -- <- Agregado aquí
    fecha_registro DATE DEFAULT (CURRENT_DATE)
);

-- Tabla de cuentas
CREATE TABLE IF NOT EXISTS cuentas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    numero_cuenta VARCHAR(36) UNIQUE NOT NULL,
    tipo ENUM('AHORRO', 'CORRIENTE', 'PLAZO') NOT NULL,
    estado ENUM('ACTIVA', 'INACTIVA', 'CERRADA') DEFAULT 'ACTIVA',
    saldo DECIMAL(14,2) DEFAULT 0.00,
    fecha_apertura DATE DEFAULT (CURRENT_DATE),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

-- Tabla de transacciones
CREATE TABLE IF NOT EXISTS transacciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cuenta_id INT NOT NULL,
    tipo ENUM('DEPOSITO', 'RETIRO', 'TRANSFERENCIA') NOT NULL,
    monto DECIMAL(14,2) NOT NULL,
    descripcion TEXT,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cuenta_id) REFERENCES cuentas(id)
);

-- Usuario técnico para ProxySQL
CREATE USER IF NOT EXISTS 'flask_user'@'%' IDENTIFIED BY 'flask_pass';
GRANT ALL PRIVILEGES ON *.* TO 'flask_user'@'%';
FLUSH PRIVILEGES;
