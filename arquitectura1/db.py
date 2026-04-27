import psycopg
import os
try:
    from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, DB_SSLMODE
except ImportError:
    DB_HOST = DB_PORT = DB_NAME = DB_USER = DB_PASS = None
    DB_SSLMODE = "prefer"

def obtener_conexion():
    url_nube = os.environ.get('DATABASE_URL')
    
    if url_nube:
        if url_nube.startswith("postgres://"):
            url_nube = url_nube.replace("postgres://", "postgresql://", 1)
        return psycopg.connect(url_nube)
    
    return psycopg.connect(
        host=os.environ.get('DB_HOST', DB_HOST),
        port=os.environ.get('DB_PORT', DB_PORT),
        dbname=os.environ.get('DB_NAME', DB_NAME),
        user=os.environ.get('DB_USER', DB_USER),
        password=os.environ.get('DB_PASS', DB_PASS),
        sslmode=os.environ.get('DB_SSLMODE', DB_SSLMODE)
    )