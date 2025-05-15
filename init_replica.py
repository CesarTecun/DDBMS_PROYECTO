import time
import mysql.connector

REPLICAS = [
    {"name": "mysql_sucursal1", "host": "127.0.0.1", "port": 3307, "server_id": 2},
    {"name": "mysql_sucursal2", "host": "127.0.0.1", "port": 3308, "server_id": 3},
    {"name": "mysql_sucursal3", "host": "127.0.0.1", "port": 3309, "server_id": 4},
    {"name": "mysql_credit",     "host": "127.0.0.1", "port": 3310, "server_id": 5},
    {"name": "mysql_mercadeo",   "host": "127.0.0.1", "port": 3311, "server_id": 6},
]

MASTER = {"host": "127.0.0.1", "port": 3315, "user": "root", "password": "root"}

def esperar_mysql(host, port):
    while True:
        try:
            conn = mysql.connector.connect(
                host=host,
                port=port,
                user='root',
                password='root'
            )
            conn.close()
            print(f"✅ MySQL en {host}:{port} está listo.")
            break
        except:
            print(f"⏳ Esperando MySQL en {host}:{port}...")
            time.sleep(2)

def obtener_master_log():
    conn = mysql.connector.connect(
        host=MASTER["host"],
        port=MASTER["port"],
        user=MASTER["user"],
        password=MASTER["password"]
    )
    cursor = conn.cursor()
    cursor.execute("SHOW MASTER STATUS;")
    row = cursor.fetchone()
    conn.close()
    return row[0], row[1]  # File, Position

def configurar_replica(replica, log_file, log_pos):
    try:
        conn = mysql.connector.connect(
            host=replica["host"],
            port=replica["port"],
            user='root',
            password='root'
        )
        cursor = conn.cursor()
        cursor.execute("STOP REPLICA;")
        cursor.execute("RESET REPLICA;")

        stmt = f"""
        CHANGE REPLICATION SOURCE TO
          SOURCE_HOST='mysql_master',
          SOURCE_PORT=3306,
          SOURCE_USER='replica',
          SOURCE_PASSWORD='replica123',
          SOURCE_LOG_FILE='{log_file}',
          SOURCE_LOG_POS={log_pos};
        """
        cursor.execute(stmt)
        cursor.execute("START REPLICA;")
        conn.close()
        print(f"✅ {replica['name']} configurada como réplica.")
    except Exception as e:
        print(f"❌ Error configurando {replica['name']}: {e}")

if __name__ == "__main__":
    esperar_mysql(MASTER["host"], MASTER["port"])
    for replica in REPLICAS:
        esperar_mysql(replica["host"], replica["port"])

    log_file, log_pos = obtener_master_log()
    print(f"\n📦 Binlog actual del master: {log_file}, posición: {log_pos}\n")

    for replica in REPLICAS:
        configurar_replica(replica, log_file, log_pos)
