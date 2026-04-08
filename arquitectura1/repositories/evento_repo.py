from db import obtener_conexion


def obtener_todos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, fecha, lugar FROM eventos;")
    rows = cursor.fetchall()
    conexion.close()
    return [{"id": r[0], "nombre": r[1], "fecha": str(r[2]), "lugar": r[3]} for r in rows]
