from flask import Flask, jsonify, request, render_template

import psycopg 
import time

app = Flask(__name__)

DB_HOST = "localhost"
DB_NAME = "eventos_db"
DB_USER = "postgres"
DB_PASS = "101610"

def obtener_conexion():
    conexion = psycopg.connect(
        host=DB_HOST,
        dbname=DB_NAME, 
        user=DB_USER,
        password=DB_PASS
    )
    return conexion

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/test-db")
def test_db():
    try:
        conexion = obtener_conexion()
        conexion.close() 
        return jsonify({"mensaje": "¡Conexión exitosa a PostgreSQL! 🎉", "estado": "ok"})
    except Exception as e:
        return jsonify({"mensaje": "Error al conectar a la BD", "error": str(e)})

@app.route("/eventos", methods=["GET"])
def obtener_eventos():
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        cursor.execute("SELECT id, nombre, fecha, lugar FROM eventos;")
        eventos_db = cursor.fetchall() 
        
        lista_eventos = []
        for evento in eventos_db:
            lista_eventos.append({
                "id": evento[0],
                "nombre": evento[1],
                "fecha": str(evento[2]),
                "lugar": evento[3]
            })
            
        conexion.close()
        return jsonify(lista_eventos)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/eventos/<int:evento_id>/tickets", methods=["GET"])
def obtener_tickets(evento_id):
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        query = """
            SELECT id FROM tickets 
            WHERE evento_id = %s 
              AND (estado = 'disponible' OR (estado = 'reservado' AND fecha_expiracion < NOW()))
            ORDER BY id ASC;
        """
        cursor.execute(query, (evento_id,))
        tickets_db = cursor.fetchall()
        lista_tickets = [{"ticket_id": t[0]} for t in tickets_db]
        conexion.close()
        return jsonify(lista_tickets)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reservas", methods=["GET"])
def obtener_reservas():
    try:
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
        reservas_db = cursor.fetchall()
        lista_reservas = [
            {"ticket_id": r[0], "usuario_nombre": r[1], "evento_nombre": r[2], "estado": r[3]} 
            for r in reservas_db
        ]
        conexion.close()
        return jsonify(lista_reservas)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
      

@app.route("/reservar", methods=["POST"])
def reservar_ticket():
    datos = request.get_json()
    ticket_id = datos.get("ticket_id")
    usuario_id = datos.get("usuario_id")

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        query = """
            UPDATE tickets
            SET estado = 'reservado',
                usuario_id = %s,
                fecha_expiracion = NOW() + INTERVAL '30 seconds'
            WHERE id = %s
              AND (estado = 'disponible' OR (estado = 'reservado' AND fecha_expiracion < NOW()))
            RETURNING id, fecha_expiracion;
        """
        cursor.execute(query, (usuario_id, ticket_id))
        resultado = cursor.fetchone()
        conexion.commit()
        conexion.close()
        
        if resultado:
            return jsonify({"mensaje": "Ticket bloqueado por 30 segundos", "ticket_id": resultado[0]}), 200
        else:
            return jsonify({"error": "El ticket acaba de ser tomado por alguien más."}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    




@app.route("/confirmar", methods=["POST"])
def confirmar_reserva():
    datos = request.get_json()
    ticket_id = datos.get("ticket_id")
    usuario_id = datos.get("usuario_id")

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        query = """
            UPDATE tickets
            SET estado = 'confirmado',
                fecha_expiracion = NULL
            WHERE id = %s AND usuario_id = %s AND estado = 'reservado' AND fecha_expiracion >= NOW()
            RETURNING id;
        """
        cursor.execute(query, (ticket_id, usuario_id))
        resultado = cursor.fetchone()
        conexion.commit()
        conexion.close()
        
        if resultado:
            return jsonify({"mensaje": "¡Compra confirmada exitosamente!"}), 200
        else:
            return jsonify({"error": "El tiempo de 30s expiró o el ticket no es tuyo."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/reservas/<int:ticket_id>", methods=["DELETE"])
def eliminar_reserva(ticket_id):
    try:
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
        
        if resultado:
            return jsonify({"mensaje": f"Reserva del ticket {ticket_id} eliminada correctamente."}), 200
        else:
            return jsonify({"error": "No se encontró la reserva o ya estaba cancelada."}), 404
            
    except Exception as e:
        if 'conexion' in locals():
            conexion.rollback()
            conexion.close()
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)
