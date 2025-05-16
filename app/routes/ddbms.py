# app/routes/ddbms.py
from sqlalchemy import text
from flask import Blueprint, jsonify,session, redirect, render_template, request
from app.db import connections
import random
from flask import session, redirect
from datetime import date
from sqlalchemy import text

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

from flask import render_template, request  # ya tienes jsonify, agrega estos

@ddbms_bp.route('/dashboard', methods=['GET'])
def dashboard():
    if not session.get("autenticado"):
        return redirect("/login")
    if session.get("rol") == "admin":
        rol = request.args.get("rol")
    elif session.get("rol") == "credit":
        rol = "credit"
    else:
        rol = session.get("sucursal")
    datos = []

    if rol in connections:
        try:
            conn = connections[rol].connect()
            if 'sucursal' in rol:
                # Mostrar clientes con sus cuentas
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
                """))
            elif rol == 'credit':
                result = conn.execute(text("SELECT * FROM tarjetas"))
            elif rol == 'mercadeo':
                result = conn.execute(text("SELECT * FROM campañas"))
            else:
                result = []

            datos = [dict(r._mapping) for r in result]
            conn.close()
        except Exception as e:
            print(f"[ERROR] {rol}: {e}")

    return render_template("dashboard.html", rol=rol, datos=datos)

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

@ddbms_bp.route('/acciones', methods=['GET'])
def ver_formulario():
    return render_template("acciones.html")

@ddbms_bp.route('/acciones/ejecutar', methods=['POST'])
def ejecutar_formulario():
    sucursal = request.form['sucursal']
    operacion = request.form['operacion']
    cliente_id = request.form['cliente_id']
    monto = request.form.get('monto')
    cuenta_destino = request.form.get('cuenta_destino')
    tarjeta = request.form.get('tarjeta')

    conn = connections[sucursal].connect()
    msg = ""

    try:
        if operacion == "crear_cuenta":
            conn.execute(text("INSERT INTO cuentas (cliente_id, numero_cuenta, tipo, saldo) VALUES (:cid, UUID(), 'AHORRO', 0.00)"), {"cid": cliente_id})
            msg = "Cuenta creada"
        elif operacion == "transferencia":
            conn.execute(text("INSERT INTO transacciones (cuenta_id, tipo, monto, descripcion) VALUES (:cid, 'TRANSFERENCIA', :monto, 'Transferencia a cuenta ' || :dest)"),
                         {"cid": cliente_id, "monto": monto, "dest": cuenta_destino})
            msg = "Transferencia registrada"
        elif operacion == "asociar_tarjeta":
            credit_conn = connections["credit"].connect()
            credit_conn.execute(text("INSERT INTO cliente_tarjeta (cliente_id, tarjeta_id) VALUES (:cid, (SELECT id FROM tarjetas WHERE numero_tarjeta = :t))"),
                                {"cid": cliente_id, "t": tarjeta})
            credit_conn.close()
            msg = "Tarjeta asociada"

        conn.commit()
    except Exception as e:
        msg = f" Error: {e}"
    finally:
        conn.close()

    return render_template("acciones.html", resultado=msg)


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
            conn = connections[data['sucursal']].connect()
            stmt = text("""
                INSERT INTO clientes (nombre_completo, fecha_nacimiento, documento_identidad, correo_electronico, telefono, direccion, municipio, departamento)
                VALUES (:nombre_completo, :fecha_nacimiento, :documento_identidad, :correo_electronico, :telefono, :direccion, :municipio, :departamento)
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
            sucursal = request.form["sucursal"]
            dpi = request.form["documento_identidad"]
            tipo = request.form["tipo"]
            saldo = request.form["saldo"]

            conn = connections[sucursal].connect()

            # Buscar cliente por DPI
            result = conn.execute(
                text("SELECT id FROM clientes WHERE documento_identidad = :dpi"),
                {"dpi": dpi}
            ).fetchone()

            if result is None:
                mensaje = "No se encontró ningún cliente con ese DPI."
            else:
                cliente_id = result[0]

                # Mapeo de tipo a código TT
                tipo_map = {
                    "AHORRO": "01",
                    "CORRIENTE": "02",
                    "PLAZO": "03"
                }
                tipo_codigo = tipo_map.get(tipo, "00")
                banco_codigo = "059"

                numero_principal = f"{random.randint(100000, 999999)}"
                digito_verificador = str(sum(int(d) for d in numero_principal) % 10)
                numero_cuenta = f"{banco_codigo}-{tipo_codigo}-{numero_principal}-{digito_verificador}"

                conn.execute(
                    text("""
                        INSERT INTO cuentas (cliente_id, numero_cuenta, tipo, saldo)
                        VALUES (:cliente_id, :numero_cuenta, :tipo, :saldo)
                    """),
                    {
                        "cliente_id": cliente_id,
                        "numero_cuenta": numero_cuenta,
                        "tipo": tipo,
                        "saldo": saldo
                    }
                )
                conn.commit()
                mensaje = f"✅ Cuenta creada: {numero_cuenta}"
            conn.close()

        except Exception as e:
            mensaje = f"❌ Error: {e}"

    return render_template("crear_cuenta.html", mensaje=mensaje, dpi=dpi_precargado, sucursal=sucursal_precargada)



def generar_numero_cuenta(codigo_banco, tipo):
    import random
    numero_principal = f"{random.randint(100000, 999999)}"
    suma = sum(int(d) for d in numero_principal)
    digito_verificador = str(suma % 10)
    return f"{codigo_banco}-{tipo}-{numero_principal}-{digito_verificador}"


@ddbms_bp.route("/acciones/nueva", methods=["GET"])
def menu_nuevo():
    return render_template("menu_nuevo.html")

@ddbms_bp.route("/acciones/transferencia", methods=["GET", "POST"])
def transferencia():
    mensaje = ""
    if request.method == "POST":
        try:
            origen_sucursal = request.form["origen_sucursal"]
            destino_sucursal = request.form["destino_sucursal"]
            cuenta_origen = request.form["cuenta_origen"]
            cuenta_destino = request.form["cuenta_destino"]
            monto = float(request.form["monto"])

            conn_origen = connections[origen_sucursal].connect()
            conn_destino = connections[destino_sucursal].connect()

            # Buscar cuenta origen y validar saldo
            origen = conn_origen.execute(
                text("SELECT id, saldo FROM cuentas WHERE numero_cuenta = :num"),
                {"num": cuenta_origen}
            ).fetchone()

            if origen is None:
                mensaje = "Cuenta origen no encontrada."
            elif origen[1] < monto:
                mensaje = "Saldo insuficiente en la cuenta origen."
            else:
                # Buscar cuenta destino
                destino = conn_destino.execute(
                    text("SELECT id FROM cuentas WHERE numero_cuenta = :num"),
                    {"num": cuenta_destino}
                ).fetchone()

                if destino is None:
                    mensaje = "Cuenta destino no encontrada."
                else:
                    origen_id = origen[0]
                    destino_id = destino[0]

                    # Descontar de cuenta origen
                    conn_origen.execute(
                        text("""
                            INSERT INTO transacciones (cuenta_id, tipo, monto, descripcion)
                            VALUES (:id, 'TRANSFERENCIA', :monto, :desc)
                        """),
                        {"id": origen_id, "monto": monto, "desc": f"A {cuenta_destino}"}
                    )
                    conn_origen.execute(
                        text("UPDATE cuentas SET saldo = saldo - :monto WHERE id = :id"),
                        {"monto": monto, "id": origen_id}
                    )

                    # Abonar en cuenta destino
                    conn_destino.execute(
                        text("""
                            INSERT INTO transacciones (cuenta_id, tipo, monto, descripcion)
                            VALUES (:id, 'TRANSFERENCIA', :monto, :desc)
                        """),
                        {"id": destino_id, "monto": monto, "desc": f"De {cuenta_origen}"}
                    )
                    conn_destino.execute(
                        text("UPDATE cuentas SET saldo = saldo + :monto WHERE id = :id"),
                        {"monto": monto, "id": destino_id}
                    )

                    conn_origen.commit()
                    conn_destino.commit()
                    mensaje = "Transferencia completada exitosamente."

            conn_origen.close()
            conn_destino.close()

        except Exception as e:
            mensaje = f"Error: {e}"

    return render_template("transferencia.html", mensaje=mensaje)


@ddbms_bp.route("/tarjetas/gestionar", methods=["GET", "POST"])
def gestionar_tarjetas():
    if not session.get("autenticado"):
        return redirect("/login")
    if session.get("rol") not in ["admin", "credit"]:
        return "Acceso denegado", 403

    mensaje = ""
    tarjeta_generada = None
    dpi_enviado = request.form.get("dpi") if request.method == "POST" else None
    tarjetas = []  # Initialize here to ensure it always exists
    conn_credit = None

    try:
        conn_credit = connections["credit"].connect()

        if request.method == "POST":
            if "actualizar_estado" in request.form:
                tarjeta_id = request.form.get("id")
                nuevo_estado = request.form.get("estado")

                if tarjeta_id and nuevo_estado:
                    conn_credit.execute(text("""
                        UPDATE tarjetas
                        SET estado = :estado
                        WHERE id = :id
                    """), {"estado": nuevo_estado, "id": tarjeta_id})
                    conn_credit.commit()
                    mensaje = "✅ Estado actualizado correctamente."

            if "generar" in request.form:
                dpi = request.form["dpi"].strip()
                
                if not dpi:
                    mensaje = "❌ El campo DPI es obligatorio."
                elif not dpi.isdigit() or len(dpi) != 13:
                    mensaje = "❌ El DPI debe contener exactamente 13 dígitos numéricos."
                else:
                    cliente_id = None
                    telefono = None
                    sucursales = ["sucursal1", "sucursal2", "sucursal3"]

                    for sucursal in sucursales:
                        conn_cliente = connections[sucursal].connect()
                        cliente = conn_cliente.execute(
                            text("SELECT id, telefono FROM clientes WHERE documento_identidad = :dpi"),
                            {"dpi": dpi}
                        ).fetchone()
                        conn_cliente.close()

                        if cliente:
                            cliente_id = cliente[0]
                            telefono = cliente[1]
                            break

                    if not cliente_id:
                        mensaje = "❌ Cliente no encontrado."
                    else:
                        numero_tarjeta = ''.join([str(random.randint(0, 9)) for _ in range(16)])
                        cvv = ''.join([str(random.randint(0, 9)) for _ in range(3)])
                        tarjeta_generada = {
                            "numero": numero_tarjeta,
                            "cvv": cvv,
                            "telefono": telefono
                        }

            elif "asociar" in request.form:
                dpi = request.form["dpi"]
                numero_tarjeta = request.form["numero_tarjeta"]
                cvv = request.form["cvv"]
                fecha_creacion = date.today()
                fecha_expiracion = fecha_creacion.replace(year=fecha_creacion.year + 5)
                limite = 3500.00
                cliente_id = None

                for sucursal in ["sucursal1", "sucursal2", "sucursal3"]:
                    conn_cliente = connections[sucursal].connect()
                    cliente = conn_cliente.execute(
                        text("SELECT id FROM clientes WHERE documento_identidad = :dpi"),
                        {"dpi": dpi}
                    ).fetchone()
                    conn_cliente.close()
                    if cliente:
                        cliente_id = cliente[0]
                        break

                if not cliente_id:
                    mensaje = "❌ Cliente no encontrado."
                else:
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
                    mensaje = "✅ Tarjeta generada y asociada correctamente."

        # Actualizar tarjetas vencidas
        conn_credit.execute(text("""
            UPDATE tarjetas
            SET estado = 'VENCIDA'
            WHERE fecha_expiracion <= CURDATE() AND estado != 'VENCIDA'
        """))
        conn_credit.commit()

        tarjetas_raw = conn_credit.execute(text("SELECT * FROM tarjetas")).fetchall()
        tarjetas = []

        for t in tarjetas_raw:
            tarjeta_dict = dict(t._mapping)
            telefono = None

            # Obtener cliente_id asociado a la tarjeta
            cliente = conn_credit.execute(text("""
                SELECT cliente_id FROM cliente_tarjeta WHERE tarjeta_id = :tid
            """), {"tid": t.id}).fetchone()

            if cliente:
                cliente_id = cliente[0]
                for sucursal in ["sucursal1", "sucursal2", "sucursal3"]:
                    conn_s = connections[sucursal].connect()
                    result = conn_s.execute(text("""
                        SELECT telefono FROM clientes WHERE id = :cid
                    """), {"cid": cliente_id}).fetchone()
                    conn_s.close()
                    if result:
                        telefono = result[0]
                        break

            tarjeta_dict["telefono"] = telefono
            tarjetas.append(tarjeta_dict)

    except Exception as e:
        mensaje = f"❌ Error: {e}"
    finally:
        if conn_credit:
            conn_credit.close()

    return render_template(
        "gestionar_tarjetas.html",
        tarjetas=tarjetas,
        mensaje=mensaje,
        tarjeta_generada=tarjeta_generada,
        dpi=dpi_enviado,
        rol=session.get("rol")
    )