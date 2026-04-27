import psycopg
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, DB_SSLMODE


def obtener_conexion():
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        sslmode=DB_SSLMODE
    )
