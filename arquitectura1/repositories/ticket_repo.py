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
    query = """
        UPDATE tickets
        SET estado = 'reservado',
            usuario_id = %s,
            fecha_expiracion = NOW() + INTERVAL '30 seconds'
        WHERE id = %s
        RETURNING id;
    """
    cursor.execute(query, (usuario_id, ticket_id))
    resultado = cursor.fetchone()
    conexion.commit()
    conexion.close()
    return resultado


def confirmar(ticket_id, usuario_id):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    cursor.execute("SELECT usuario_id FROM tickets WHERE id = %s AND estado = 'reservado'", (ticket_id,))
    fila = cursor.fetchone()
    
    
    if fila:
        query = """
            UPDATE tickets
            SET estado = 'confirmado', fecha_expiracion = NULL
            WHERE id = %s AND usuario_id = %s
            RETURNING id;
        """
        cursor.execute(query, (ticket_id, usuario_id))
        resultado = cursor.fetchone()
        conexion.commit()
        conexion.close()
        return resultado
    
    conexion.close()
    return None


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
