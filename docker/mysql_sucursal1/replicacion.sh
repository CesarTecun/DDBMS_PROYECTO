#!/bin/bash
set -e

echo "🔧 Iniciando MySQL en segundo plano..."
docker-entrypoint.sh mysqld &

pid="$!"

# Espera hasta que el servidor esté listo
until mysqladmin ping -h "localhost" -proot --silent; do
  echo "⏳ Esperando que MySQL esté listo para conexiones..."
  sleep 2
done

# Esperar un poco más para asegurar que init.sql se haya ejecutado
sleep 5

echo "🔁 Configurando replicación..."

# Ejecutar replicación con autenticación segura
mysql -uroot -proot <<EOF
STOP SLAVE;
RESET SLAVE ALL;

CHANGE MASTER TO
  MASTER_HOST='mysql_master',
  MASTER_PORT=3306,
  MASTER_USER='replica',
  MASTER_PASSWORD='replica123',
  MASTER_AUTO_POSITION=1;

START SLAVE;
EOF

echo "✅ Replicación configurada exitosamente."

# Esperar al proceso principal de MySQL
wait "$pid"
