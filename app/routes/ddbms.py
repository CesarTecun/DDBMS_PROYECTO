# app/routes/ddbms.py
from sqlalchemy import text
from flask import Blueprint, jsonify,session, redirect, render_template, request
from app.db import connections
import random
from flask import session, redirect
from datetime import date
from sqlalchemy import text

from app.utils_ddbms import (
    obtener_clientes_todas_sucursales,
    buscar_cliente_por_dpi,
    generar_datos_tarjeta,
    asociar_tarjeta,
    buscar_cuenta,
    validar_saldo,
    registrar_transaccion,
    actualizar_saldo,
    contar_tarjetas_cliente,
    obtener_telefono_tarjeta
)


ddbms_bp = Blueprint('ddbms', __name__)

@ddbms_bp.route('/clientes/<sucursal>')
def get_clientes(sucursal):
    try:
        if sucursal not in connections:
            return jsonify({'error': 'Sucursal inválida'}), 404

        conn = connections[sucursal].connect()
        result = conn.execute(text("SELECT * FROM clientes"))
        clientes = [dict(r._mapping) for r in result]
        conn.close()
        return jsonify(clientes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ddbms_bp.route('/tarjetas')
def get_tarjetas():
    conn = connections['credit'].connect()
    result = conn.execute(text("SELECT * FROM tarjetas"))
    tarjetas = [dict(r._mapping) for r in result]
    conn.close()
    return jsonify(tarjetas)

@ddbms_bp.route('/test-conexiones')
def test_conexiones():
    estados = {}
    for nombre, engine in connections.items():
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                estados[nombre] = "Conexión exitosa"
        except Exception as e:
            estados[nombre] = f"Error: {str(e)}"
    return jsonify(estados)


@ddbms_bp.route('/dashboard', methods=['GET'])
def dashboard():
    if not session.get("autenticado"):
        return redirect("/login")

    rol_usuario = session.get("rol")
    sucursal_actual = ""

    # Determinar sucursal/rol seleccionado
    if rol_usuario == "admin":
        sucursal_actual = request.args.get("rol") or "clientes_todas"
    elif rol_usuario == "credit":
        sucursal_actual = "clientes_todas"  # nuevo código interno
    elif rol_usuario == "mercadeo":
        sucursal_actual = "mercadeo"
    else:
        sucursal_actual = session.get("sucursal")

    datos = []

    # Mostrar todos los clientes si es credit
    if sucursal_actual == "clientes_todas" and rol_usuario in ["credit", "admin"]:
        datos = obtener_clientes_todas_sucursales(connections)

    elif sucursal_actual in connections:
        try:
            conn = connections[sucursal_actual].connect()

            if "sucursal" in sucursal_actual:
                result = conn.execute(text("""
                    SELECT 
                        c.id AS cliente_id,
                        c.nombre_completo,
                        c.documento_identidad,
                        cu.numero_cuenta,
                        cu.tipo,
                        cu.estado,
                        cu.saldo,
                        cu.fecha_apertura
                    FROM clientes c
                    LEFT JOIN cuentas cu ON c.id = cu.cliente_id
                    WHERE c.sucursal = :sucursal
                """), {"sucursal": sucursal_actual})
            elif sucursal_actual == 'credit':
                result = conn.execute(text("SELECT * FROM tarjetas"))
            elif sucursal_actual == 'mercadeo':
                result = conn.execute(text("SELECT * FROM campana"))
            else:
                result = []

            datos = [dict(r._mapping) for r in result]
            conn.close()
        except Exception as e:
            print(f"[ERROR] {sucursal_actual}: {e}")

    # Mostrar el selector con Clientes por defecto para credit
    sucursales_disponibles = [
        ("clientes_todas", "Clientes") if rol_usuario in ["credit", "admin"] else None,
        ("sucursal1", "Sucursal 1"),
        ("sucursal2", "Sucursal 2"),
        ("sucursal3", "Sucursal 3"),
        ("credit", "Tarjetas de Crédito"),
        ("mercadeo", "Mercadeo"),
        ("admin", "Administrador")
    ]
    sucursales_disponibles = [s for s in sucursales_disponibles if s is not None]

    return render_template(
        "dashboard.html",
        datos=datos,
        sucursal_actual=sucursal_actual,
        rol_usuario=rol_usuario,
        sucursales_disponibles=sucursales_disponibles
    )




@ddbms_bp.route("/cuenta/<sucursal>/<numero_cuenta>")
def ver_transacciones(sucursal, numero_cuenta):
    transacciones = []
    if sucursal in connections:
        try:
            conn = connections[sucursal].connect()
            result = conn.execute(text("""
                SELECT t.id, t.tipo, t.monto, t.descripcion, t.fecha
                FROM transacciones t
                JOIN cuentas c ON t.cuenta_id = c.id
                WHERE c.numero_cuenta = :num
            """), {"num": numero_cuenta})
            transacciones = [dict(r._mapping) for r in result]
            conn.close()
        except Exception as e:
            transacciones = [{"Error": str(e)}]

    return render_template("transacciones.html", numero_cuenta=numero_cuenta, transacciones=transacciones)


from flask import render_template, request, redirect

@ddbms_bp.route("/clientes/registrar", methods=["GET", "POST"])
def registrar_cliente():
    if not session.get("autenticado"):
        return redirect("/login")

    if session.get("rol") not in ["sucursal", "admin"]:
        return "❌ Acceso denegado", 403
    mensaje = ""
    if request.method == "POST":
        try:
            data = request.form
            conn = connections["master"].connect()
            stmt = text("""
                INSERT INTO clientes (
                    nombre_completo, fecha_nacimiento, documento_identidad,
                    correo_electronico, telefono, direccion, municipio, departamento, sucursal
                )
                VALUES (
                    :nombre_completo, :fecha_nacimiento, :documento_identidad,
                    :correo_electronico, :telefono, :direccion, :municipio, :departamento, :sucursal
                )
            """)
            conn.execute(stmt, dict(data))
            conn.commit()
            conn.close()
            mensaje = "Cliente registrado correctamente"

            return redirect(f"/dashboard?rol={data['sucursal']}")
        except Exception as e:
            mensaje = f"Error: {e}"

    return render_template("registrar_cliente.html", mensaje=mensaje)



@ddbms_bp.route("/acciones/crear-cuenta", methods=["GET", "POST"])
def crear_cuenta():
    mensaje = ""
    dpi_precargado = request.args.get("dpi", "")
    sucursal_precargada = request.args.get("sucursal", "")

    if request.method == "POST":
        try:
            # Obtener datos del formulario
            sucursal = request.form["sucursal"]
            dpi = request.form["documento_identidad"]
            tipo = request.form["tipo"]
            saldo = request.form["saldo"]

            # Validación de tipo
            if tipo not in ["AHORRO", "CORRIENTE", "PLAZO"]:
                return render_template("crear_cuenta.html", mensaje="❌ Tipo de cuenta inválido.", dpi=dpi, sucursal=sucursal)

            # Validar y convertir saldo
            try:
                saldo = float(saldo)
                if saldo < 0:
                    raise ValueError("Saldo negativo.")
            except ValueError:
                return render_template("crear_cuenta.html", mensaje="❌ El saldo debe ser un número positivo.", dpi=dpi, sucursal=sucursal)

            # Protección según rol
            if session.get("rol") != "admin":
                sucursal = session.get("sucursal")

            conn = connections["master"].connect()

            # Buscar cliente por DPI
            result = conn.execute(
                text("SELECT id FROM clientes WHERE documento_identidad = :dpi"),
                {"dpi": dpi}
            ).fetchone()

            if result is None:
                mensaje = "❌ No se encontró ningún cliente con ese DPI."
            else:
                cliente_id = result[0]

                # Verificar si ya tiene cuenta de ese tipo
                existe = conn.execute(
                    text("SELECT 1 FROM cuentas WHERE cliente_id = :cliente_id AND tipo = :tipo"),
                    {"cliente_id": cliente_id, "tipo": tipo}
                ).fetchone()

                if existe:
                    mensaje = f"⚠️ El cliente ya tiene una cuenta de tipo {tipo}."
                else:
                    # Generar número de cuenta
                    tipo_map = {"AHORRO": "01", "CORRIENTE": "02", "PLAZO": "03"}
                    tipo_codigo = tipo_map.get(tipo, "00")
                    banco_codigo = "059"

                    numero_principal = f"{random.randint(100000, 999999)}"
                    digito_verificador = str(sum(int(d) for d in numero_principal) % 10)
                    numero_cuenta = f"{banco_codigo}-{tipo_codigo}-{numero_principal}-{digito_verificador}"

                    # Insertar cuenta
                    conn.execute(
                        text("""
                            INSERT INTO cuentas (cliente_id, numero_cuenta, tipo, saldo, sucursal)
                            VALUES (:cliente_id, :numero_cuenta, :tipo, :saldo, :sucursal)
                        """),
                        {
                            "cliente_id": cliente_id,
                            "numero_cuenta": numero_cuenta,
                            "tipo": tipo,
                            "saldo": saldo,
                            "sucursal": sucursal
                        }
                    )
                    conn.commit()
                    mensaje = f"✅ Cuenta creada exitosamente: {numero_cuenta}"

            conn.close()

        except Exception as e:
            mensaje = f"❌ Error inesperado: {e}"

    return render_template("crear_cuenta.html", mensaje=mensaje, dpi=dpi_precargado, sucursal=sucursal_precargada)


def generar_numero_cuenta(codigo_banco, tipo):
    import random
    numero_principal = f"{random.randint(100000, 999999)}"
    suma = sum(int(d) for d in numero_principal)
    digito_verificador = str(suma % 10)
    return f"{codigo_banco}-{tipo}-{numero_principal}-{digito_verificador}"


@ddbms_bp.route("/acciones/transferencia", methods=["GET", "POST"])
def transferencia():
    mensaje = ""

    if request.method == "POST":
        try:
            origen_sucursal = request.form["origen_sucursal"]
            destino_sucursal = request.form["destino_sucursal"]
            cuenta_origen = request.form["cuenta_origen"]
            cuenta_destino = request.form["cuenta_destino"]

            # Validar monto
            try:
                monto = float(request.form["monto"])
                if monto <= 0:
                    raise ValueError
            except ValueError:
                return render_template("transferencia.html", mensaje="❌ El monto debe ser un número positivo.")

            if cuenta_origen == cuenta_destino and origen_sucursal == destino_sucursal:
                return render_template("transferencia.html", mensaje="❌ Las cuentas origen y destino no pueden ser iguales.")

            # Conexiones SOLO DE LECTURA para validar cuentas
            conn_origen_read = connections[origen_sucursal].connect()
            conn_destino_read = connections[destino_sucursal].connect()

            origen = buscar_cuenta(conn_origen_read, cuenta_origen)
            destino = buscar_cuenta(conn_destino_read, cuenta_destino)

            conn_origen_read.close()
            conn_destino_read.close()

            if not origen:
                mensaje = "❌ Cuenta origen no encontrada."
            elif not destino:
                mensaje = "❌ Cuenta destino no encontrada."
            elif not validar_saldo(origen, monto):
                mensaje = "❌ Saldo insuficiente en la cuenta origen."
            else:
                # Usamos conexión MASTER para las escrituras
                conn_master = connections["master"].connect()

                registrar_transaccion(conn_master, origen[0], monto, f"A {cuenta_destino}")
                actualizar_saldo(conn_master, origen[0], monto, '-')

                registrar_transaccion(conn_master, destino[0], monto, f"De {cuenta_origen}")
                actualizar_saldo(conn_master, destino[0], monto, '+')

                conn_master.commit()
                conn_master.close()

                mensaje = "✅ Transferencia completada exitosamente."

        except Exception as e:
            mensaje = f"❌ Error: {e}"

    return render_template("transferencia.html", mensaje=mensaje)




@ddbms_bp.route("/tarjetas/gestionar", methods=["GET", "POST"])
def gestionar_tarjetas():
    if not session.get("autenticado"):
        return redirect("/login")
    if session.get("rol") not in ["admin", "credit"]:
        return "Acceso denegado", 403

    mensaje = ""
    tarjeta_generada = None
    dpi_enviado = request.form.get("dpi") if request.method == "POST" else request.args.get("dpi", "")
    tarjetas = []

    try:
        conn_credit = connections["credit"].connect()

        if request.method == "POST":
            if "actualizar_estado" in request.form:
                conn_credit.execute(
                    text("UPDATE tarjetas SET estado = :estado WHERE id = :id"),
                    {
                        "estado": request.form.get("estado"),
                        "id": request.form.get("id")
                    }
                )
                conn_credit.commit()
                mensaje = "✅ Estado actualizado correctamente."

            elif "generar" in request.form:
                dpi = request.form["dpi"].strip()
                if not dpi or not dpi.isdigit() or len(dpi) != 13:
                    mensaje = "❌ El DPI debe tener exactamente 13 dígitos numéricos."
                else:
                    cliente = buscar_cliente_por_dpi(dpi, connections)
                    if not cliente:
                        mensaje = "❌ Cliente no encontrado."
                    else:
                        numero_tarjeta, cvv = generar_datos_tarjeta()
                        tarjeta_generada = {
                            "numero": numero_tarjeta,
                            "cvv": cvv,
                            "telefono": cliente[1]
                        }

            elif "asociar" in request.form:
                dpi = request.form["dpi"]
                cliente = buscar_cliente_por_dpi(dpi, connections)
                if not cliente:
                    mensaje = "❌ Cliente no encontrado."
                else:
                    asociar_tarjeta(conn_credit, cliente[0], request.form["numero_tarjeta"], request.form["cvv"])
                    mensaje = "✅ Tarjeta generada y asociada correctamente."

        # Marcar vencidas
        conn_credit.execute(text("""
            UPDATE tarjetas
            SET estado = 'VENCIDA'
            WHERE fecha_expiracion <= CURDATE() AND estado != 'VENCIDA'
        """))
        conn_credit.commit()

        tarjetas_raw = conn_credit.execute(text("SELECT * FROM tarjetas")).fetchall()
        tarjetas = []

        for t in tarjetas_raw:
            tarjeta = dict(t._mapping)
            tarjeta["telefono"] = obtener_telefono_tarjeta(t.id, connections)
            tarjetas.append(tarjeta)

        conn_credit.close()

    except Exception as e:
        mensaje = f"❌ Error: {e}"

    tarjetas_cliente = contar_tarjetas_cliente(dpi_enviado, connections) if dpi_enviado else 0

    return render_template(
        "gestionar_tarjetas.html",
        tarjetas=tarjetas,
        mensaje=mensaje,
        tarjeta_generada=tarjeta_generada,
        dpi=dpi_enviado,
        tarjetas_cliente=tarjetas_cliente,
        rol=session.get("rol")
    )