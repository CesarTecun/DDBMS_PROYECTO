from flask import Blueprint, redirect, url_for, session

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if session.get("autenticado"):
        return redirect("ddbms.dashboard")  # o url_for('ddbms.dashboard')
    return redirect(url_for('login.login'))
