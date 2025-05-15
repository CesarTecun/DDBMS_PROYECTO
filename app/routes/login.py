from flask import Blueprint, render_template, request, redirect, session, url_for
from app.db import connections
from sqlalchemy import text
from functools import wraps
from flask import session, redirect, url_for

def login_required(roles_permitidos=None):
    def decorador(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not session.get('autenticado'):
                return redirect(url_for('login.login'))
            if roles_permitidos and session.get("rol") not in roles_permitidos:
                return "❌ Acceso denegado: rol no autorizado", 403
            return func(*args, **kwargs)
        return wrapper
    return decorador


login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    mensaje = ""
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']

        try:
            conn = connections['admin'].connect()
            query = text("""
                SELECT * FROM usuarios
                WHERE username = :usuario AND password = :clave AND activo = TRUE
                LIMIT 1
            """)
            result = conn.execute(query, {"usuario": usuario, "clave": clave}).fetchone()
            conn.close()

            if result:
                session['autenticado'] = True
                session['usuario'] = result.username
                session['rol'] = result.rol
                session['sucursal'] = result.sucursal
                return redirect('/dashboard')
            else:
                mensaje = "❌ Usuario o contraseña incorrectos"
        except Exception as e:
            mensaje = f"⚠️ Error al conectar: {e}"

    return render_template('login.html', mensaje=mensaje)

@login_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/login')