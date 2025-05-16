import time
import mysql.connector
from mysql.connector import Error

# Verificamos conexión a través de ProxySQL con los usuarios por rol
SERVIDORES = [
    {"name": "sucursal1", "user": "read_sucursal1", "password": "clave123"},
    {"name": "sucursal2", "user": "read_sucursal2", "password": "clave123"},
    {"name": "sucursal3", "user": "read_sucursal3", "password": "clave123"},
    {"name": "credit",    "user": "read_credit",    "password": "clave123"},
    {"name": "mercadeo",  "user": "read_mercadeo",  "password": "clave123"},
    {"name": "master",    "user": "admin_user",     "password": "clave123"}
]

for servidor in SERVIDORES:
    print(f"Conectando a {servidor['name']} vía ProxySQL...")

    intentos = 0
    while intentos < 20:
        try:
            conn = mysql.connector.connect(
                host="proxysql",
                port=6033,
                user=servidor["user"],
                password=servidor["password"],
                database="banco"
            )
            if conn.is_connected():
                print(f"✅ {servidor['name']} listo.")
                break
        except Error:
            print(f"⏳ {servidor['name']} no disponible aún. Reintentando...")
            time.sleep(3)
            intentos += 1
    else:
        print(f"❌ Error: {servidor['name']} no respondió tras 20 intentos.")
        exit(1)

print("🎉 Todos los servidores accesibles vía ProxySQL. Lanzando Flask...")