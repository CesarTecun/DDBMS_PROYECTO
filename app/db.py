# db.py
from sqlalchemy import create_engine
from config import DBS

connections = {}

for key, cfg in DBS.items():
    uri = f"mysql+pymysql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
    engine = create_engine(uri, pool_pre_ping=True)
    connections[key] = engine
