import time
import mysql.connector
from mysql.connector import Error

SERVIDORES = [
    {"name": "sucursal1", "host": "mysql_sucursal1", "port": 3306, "database": "banco"},
    {"name": "master", "host": "mysql_master", "port": 3306, "database": "banco"},
    {"name": "credit", "host": "mysql_credit", "port": 3306, "database": "banco"},
    {"name": "mercadeo", "host": "mysql_mercadeo", "port": 3306, "database": "banco"}
]

for servidor in SERVIDORES:
    print(f"Esperando MySQL de {servidor['name']} en {servidor['host']}:{servidor['port']}...")

    intentos = 0
    while intentos < 20:
        try:
            conn = mysql.connector.connect(
                host=servidor["host"],
                port=servidor["port"],
                user="root",
                password="root",
                database=servidor["database"]
            )
            if conn.is_connected():
                print(f" {servidor['name']} listo.")
                break
        except Error:
            print(f"⏳ {servidor['name']} no disponible aún. Reintentando...")
            time.sleep(3)
            intentos += 1
    else:
        print(f"Error: {servidor['name']} no respondió tras 20 intentos.")
        exit(1)

print("Todos los servidores listos. Lanzando Flask...")
