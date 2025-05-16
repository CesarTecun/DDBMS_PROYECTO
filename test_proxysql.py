from flask import Flask, jsonify
from sqlalchemy import create_engine, text

app = Flask(__name__)

# Conexión usando ProxySQL (hostgroup dinámico según reglas)
engine = create_engine("mysql+pymysql://flask_user:flask_pass@127.0.0.1:6033/banco")

@app.route("/")
def index():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT NOW()"))
        row = result.fetchone()
    return jsonify({"hora_actual": str(row[0])})

@app.route("/clientes")
def clientes():
    with engine.connect() as conn:
        # Esta consulta activa la regla de enrutamiento por sucursal
        result = conn.execute(text("SELECT * FROM clientes WHERE sucursal='sucursal1' LIMIT 5"))
        rows = [dict(row._mapping) for row in result]
    return jsonify(rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
