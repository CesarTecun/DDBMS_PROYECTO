import mysql.connector

def obtener_conexion_sucursal1():
    return mysql.connector.connect(
        host="mysql_sucursal1",
        port=3306,
        user="root",
        password="root",
        database="sucursal1"
    )
