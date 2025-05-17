from sqlalchemy import text
#utils_ddbms.py
def obtener_clientes_todas_sucursales(conexiones):
    vistos = set()
    clientes = []

    # Obtener IDs de clientes que tienen tarjeta
    credit_conn = conexiones["credit"].connect()
    tarjetas_clientes = credit_conn.execute(text("SELECT cliente_id FROM cliente_tarjeta")).fetchall()
    credit_conn.close()
    clientes_con_tarjeta = set(row[0] for row in tarjetas_clientes)

    for sucursal in ["sucursal1", "sucursal2", "sucursal3"]:
        conn = conexiones[sucursal].connect()
        result = conn.execute(text("""
            SELECT 
                c.id AS cliente_id,
                c.nombre_completo,
                c.documento_identidad,
                c.sucursal AS sucursal,
                cu.numero_cuenta,
                cu.tipo,
                cu.estado,
                cu.saldo,
                cu.fecha_apertura
            FROM clientes c
            LEFT JOIN cuentas cu ON c.id = cu.cliente_id
        """))

        for r in result:
            cliente = dict(r._mapping)
            dpi = cliente["documento_identidad"]
            cliente_id = cliente["cliente_id"]
            if dpi not in vistos:
                vistos.add(dpi)
                cliente["tarjeta"] = "Sí" if cliente_id in clientes_con_tarjeta else "No"
                clientes.append(cliente)

        conn.close()

    return clientes


# tarjetas_utils.py
from sqlalchemy import text
from datetime import date
import random

def buscar_cliente_por_dpi(dpi, conexiones):
    for sucursal in ["sucursal1", "sucursal2", "sucursal3"]:
        conn = conexiones[sucursal].connect()
        cliente = conn.execute(
            text("SELECT id, telefono FROM clientes WHERE documento_identidad = :dpi"),
            {"dpi": dpi}
        ).fetchone()
        conn.close()
        if cliente:
            return cliente
    return None

def generar_datos_tarjeta():
    numero = ''.join([str(random.randint(0, 9)) for _ in range(16)])
    cvv = ''.join([str(random.randint(0, 9)) for _ in range(3)])
    return numero, cvv

def asociar_tarjeta(conn_credit, cliente_id, numero_tarjeta, cvv):
    fecha_creacion = date.today()
    fecha_expiracion = fecha_creacion.replace(year=fecha_creacion.year + 5)
    limite = 3500.00

    result = conn_credit.execute(text("""
        INSERT INTO tarjetas (numero_tarjeta, cvv, fecha_expiracion, limite_credito, saldo_actual)
        VALUES (:numero, :cvv, :fecha, :limite, :limite)
    """), {
        "numero": numero_tarjeta,
        "cvv": cvv,
        "fecha": fecha_expiracion,
        "limite": limite
    })
    tarjeta_id = result.lastrowid

    conn_credit.execute(text("""
        INSERT INTO cliente_tarjeta (cliente_id, tarjeta_id)
        VALUES (:cliente_id, :tarjeta_id)
    """), {
        "cliente_id": cliente_id,
        "tarjeta_id": tarjeta_id
    })
    conn_credit.commit()

def contar_tarjetas_cliente(dpi, conexiones):
    cliente = buscar_cliente_por_dpi(dpi, conexiones)
    if not cliente:
        return 0
    cliente_id = cliente[0]
    conn = conexiones["credit"].connect()
    count = conn.execute(text("""
        SELECT COUNT(*) FROM cliente_tarjeta WHERE cliente_id = :cid
    """), {"cid": cliente_id}).scalar()
    conn.close()
    return count

def obtener_telefono_tarjeta(tarjeta_id, conexiones):
    conn = conexiones["credit"].connect()
    cliente = conn.execute(
        text("SELECT cliente_id FROM cliente_tarjeta WHERE tarjeta_id = :tid"),
        {"tid": tarjeta_id}
    ).fetchone()
    conn.close()
    if not cliente:
        return None

    cliente_id = cliente[0]
    for sucursal in ["sucursal1", "sucursal2", "sucursal3"]:
        conn = conexiones[sucursal].connect()
        telefono = conn.execute(
            text("SELECT telefono FROM clientes WHERE id = :cid"),
            {"cid": cliente_id}
        ).fetchone()
        conn.close()
        if telefono:
            return telefono[0]
    return None

def buscar_cuenta(conn, numero_cuenta):
    return conn.execute(
        text("SELECT id, saldo FROM cuentas WHERE numero_cuenta = :num"),
        {"num": numero_cuenta}
    ).fetchone()

def validar_saldo(cuenta, monto):
    return cuenta and cuenta[1] >= monto

def registrar_transaccion(conn, cuenta_id, monto, descripcion):
    conn.execute(
        text("""
            INSERT INTO transacciones (cuenta_id, tipo, monto, descripcion)
            VALUES (:id, 'TRANSFERENCIA', :monto, :desc)
        """),
        {"id": cuenta_id, "monto": monto, "desc": descripcion}
    )

def actualizar_saldo(conn, cuenta_id, monto, operacion='+'):
    operador = '+' if operacion == '+' else '-'
    conn.execute(
        text(f"UPDATE cuentas SET saldo = saldo {operador} :monto WHERE id = :id"),
        {"monto": monto, "id": cuenta_id}
    )