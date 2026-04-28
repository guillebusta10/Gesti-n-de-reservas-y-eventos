from db import obtener_conexion

def obtener_disponibles(evento_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    query = """
        SELECT id FROM tickets
        WHERE evento_id = %s
            AND estado IN ('disponible', 'reservado')        
        ORDER BY id ASC;
    """
    cursor.execute(query, (evento_id,))
    rows = cursor.fetchall()
    conexion.close()
    return [{"ticket_id": r[0]} for r in rows]


def obtener_reservas_activas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    query = """
        SELECT t.id, COALESCE(u.nombre, 'Sin nombre'), e.nombre, t.estado
        FROM tickets t
        LEFT JOIN usuarios u ON t.usuario_id = u.id
        JOIN eventos e ON t.evento_id = e.id
        WHERE t.estado IN ('reservado', 'confirmado')
        ORDER BY t.id DESC;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conexion.close()
    return [{"ticket_id": r[0], "usuario_nombre": r[1], "evento_nombre": r[2], "estado": r[3]} for r in rows]


def bloquear(ticket_id, usuario_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    # Insertamos una "intención" de reserva. 
    # Varios usuarios pueden insertar una para el mismo ticket_id.
    query = """
        INSERT INTO reservas_temporales (ticket_id, usuario_id)
        VALUES (%s, %s) RETURNING id;
    """
    cursor.execute(query, (ticket_id, usuario_id))
    resultado = cursor.fetchone()
    
    # También actualizamos el estado visual en la tabla tickets
    cursor.execute("UPDATE tickets SET estado = 'reservado' WHERE id = %s", (ticket_id,))
    
    conexion.commit()
    conexion.close()
    return resultado


def confirmar(ticket_id, usuario_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    # LA CARRERA: Solo el primero que logre pasar el ticket de 'reservado' 
    # a 'confirmado' en la tabla principal gana.
    query = """
        UPDATE tickets
        SET estado = 'confirmado', 
            usuario_id = %s,
            fecha_expiracion = NULL
        WHERE id = %s AND estado = 'reservado'
        RETURNING id;
    """
    cursor.execute(query, (usuario_id, ticket_id))
    resultado = cursor.fetchone()
    
    if resultado:
        # Si ganó, limpiamos las reservas temporales de los demás
        cursor.execute("DELETE FROM reservas_temporales WHERE ticket_id = %s", (ticket_id,))
        conexion.commit()
    
    conexion.close()
    return resultado
    
  


def liberar(ticket_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    query = """
        UPDATE tickets
        SET estado = 'disponible',
            usuario_id = NULL,
            fecha_expiracion = NULL
        WHERE id = %s
        RETURNING id;
    """
    cursor.execute(query, (ticket_id,))
    resultado = cursor.fetchone()
    conexion.commit()
    conexion.close()
    return resultado
