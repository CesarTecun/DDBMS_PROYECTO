CREATE DATABASE IF NOT EXISTS banco;
USE banco;

-- Tabla de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_completo VARCHAR(100) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    documento_identidad VARCHAR(13) UNIQUE NOT NULL,
    correo_electronico VARCHAR(100),
    telefono VARCHAR(15),
    direccion TEXT,
    municipio VARCHAR(50),
    departamento VARCHAR(50),
    sucursal VARCHAR(50),  -- Fragmentación horizontal
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

-- Usuario de replicación (usa plugin compatible con réplicas)
CREATE USER IF NOT EXISTS 'replica'@'%' IDENTIFIED WITH mysql_native_password BY 'replica123';
GRANT REPLICATION SLAVE ON *.* TO 'replica'@'%';

-- Usuario de escritura global (para ProxySQL)
CREATE USER IF NOT EXISTS 'admin_user'@'%' IDENTIFIED WITH mysql_native_password BY 'clave123';
GRANT ALL PRIVILEGES ON banco.* TO 'admin_user'@'%';

-- Usuarios por sucursal (solo lectura)
CREATE USER IF NOT EXISTS 'read_sucursal1'@'%' IDENTIFIED WITH mysql_native_password BY 'clave123';
GRANT SELECT ON banco.* TO 'read_sucursal1'@'%';

CREATE USER IF NOT EXISTS 'read_sucursal2'@'%' IDENTIFIED WITH mysql_native_password BY 'clave123';
GRANT SELECT ON banco.* TO 'read_sucursal2'@'%';

CREATE USER IF NOT EXISTS 'read_sucursal3'@'%' IDENTIFIED WITH mysql_native_password BY 'clave123';
GRANT SELECT ON banco.* TO 'read_sucursal3'@'%';

CREATE USER IF NOT EXISTS 'read_credit'@'%' IDENTIFIED WITH mysql_native_password BY 'clave123';
GRANT SELECT ON banco.* TO 'read_credit'@'%';

CREATE USER IF NOT EXISTS 'read_mercadeo'@'%' IDENTIFIED WITH mysql_native_password BY 'clave123';
GRANT SELECT ON banco.* TO 'read_mercadeo'@'%';

-- Aplicar cambios
FLUSH PRIVILEGES;
