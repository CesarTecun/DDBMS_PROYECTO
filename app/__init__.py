from flask import Flask

def create_app():
    app = Flask(__name__)
    app.secret_key = 'clave_secreta_123'


    from .routes.main import main_bp
    app.register_blueprint(main_bp)

    from .routes.ddbms import ddbms_bp
    app.register_blueprint(ddbms_bp)

    from app.routes.login import login_bp
    app.register_blueprint(login_bp)

    return app
