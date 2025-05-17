#!/bin/bash
set -e

echo "🔧 Iniciando MySQL en segundo plano..."
docker-entrypoint.sh mysqld &

pid="$!"


until mysqladmin ping -h127.0.0.1 -uroot -proot --silent; do
  echo "⏳ Esperando que MySQL esté listo para conexiones..."
  sleep 2
done


sleep 5

echo "🔁 Configurando replicación..."

mysql -uroot -proot -h127.0.0.1 <<EOF
STOP REPLICA;
RESET REPLICA ALL;

CHANGE REPLICATION SOURCE TO
  SOURCE_HOST='mysql_master',
  SOURCE_PORT=3306,
  SOURCE_USER='replica',
  SOURCE_PASSWORD='replica123',
  SOURCE_AUTO_POSITION = 1;

START REPLICA;
EOF

echo "✅ Replicación configurada exitosamente."


wait "$pid"
