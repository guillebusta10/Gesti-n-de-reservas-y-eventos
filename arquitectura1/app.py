from flask import Flask, jsonify, request, render_template
from flasgger import Swagger
from db import obtener_conexion
from repositories import evento_repo, ticket_repo
from services import reserva_service

app = Flask(__name__)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
}

swagger_template = {
    "info": {
        "title": "API Gestión de Reservas y Eventos",
        "description": "API REST para gestionar eventos, tickets y reservas con control de concurrencia.",
        "version": "1.0.0",
    }
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/test-db")
def test_db():
    """
    Verificar conexión a la base de datos.
    ---
    tags:
      - Sistema
    responses:
      200:
        description: Conexión exitosa
        schema:
          type: object
          properties:
            mensaje:
              type: string
            estado:
              type: string
    """
    try:
        conexion = obtener_conexion()
        conexion.close()
        return jsonify({"mensaje": "¡Conexión exitosa a PostgreSQL! 🎉", "estado": "ok"})
    except Exception as e:
        return jsonify({"mensaje": "Error al conectar a la BD", "error": str(e)})


@app.route("/eventos", methods=["GET"])
def obtener_eventos():
    """
    Listar todos los eventos disponibles.
    ---
    tags:
      - Eventos
    responses:
      200:
        description: Lista de eventos
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              nombre:
                type: string
                example: Concierto de Rock
              fecha:
                type: string
                example: "2026-06-15"
              capacidad:
                type: integer
                example: 100
      500:
        description: Error interno del servidor
    """
    try:
        return jsonify(evento_repo.obtener_todos())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/eventos/<int:evento_id>/tickets", methods=["GET"])
def obtener_tickets(evento_id):
    """
    Listar tickets disponibles de un evento.
    ---
    tags:
      - Eventos
    parameters:
      - name: evento_id
        in: path
        type: integer
        required: true
        description: ID del evento
        example: 1
    responses:
      200:
        description: Lista de tickets disponibles
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 5
              evento_id:
                type: integer
                example: 1
              precio:
                type: number
                example: 50.00
              estado:
                type: string
                example: disponible
      500:
        description: Error interno del servidor
    """
    try:
        return jsonify(ticket_repo.obtener_disponibles(evento_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reservas", methods=["GET"])
def obtener_reservas():
    """
    Listar todas las reservas activas.
    ---
    tags:
      - Reservas
    responses:
      200:
        description: Lista de reservas activas
        schema:
          type: array
          items:
            type: object
            properties:
              ticket_id:
                type: integer
                example: 5
              usuario_id:
                type: integer
                example: 42
              reservado_hasta:
                type: string
                example: "2026-04-28T15:30:00"
      500:
        description: Error interno del servidor
    """
    try:
        return jsonify(ticket_repo.obtener_reservas_activas())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reservar", methods=["POST"])
def reservar_ticket():
    """
    Reservar un ticket (bloqueo temporal de 30 segundos).
    ---
    tags:
      - Reservas
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - ticket_id
            - usuario_id
          properties:
            ticket_id:
              type: integer
              example: 5
            usuario_id:
              type: integer
              example: 42
    responses:
      200:
        description: Ticket bloqueado exitosamente
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: Ticket bloqueado por 30 segundos
            ticket_id:
              type: integer
              example: 5
      400:
        description: Faltan parámetros requeridos
      409:
        description: Ticket no disponible o ya reservado
      500:
        description: Error interno del servidor
    """
    try:
        datos = request.get_json() or {}
        ticket_id = datos.get("ticket_id")
        usuario_id = datos.get("usuario_id")
        if ticket_id is None or usuario_id is None:
            return jsonify({"error": "Se requieren ticket_id y usuario_id"}), 400
        resultado = reserva_service.reservar(ticket_id, usuario_id)
        if resultado["ok"]:
            return jsonify({"mensaje": "Ticket bloqueado por 30 segundos", "ticket_id": resultado["ticket_id"]}), 200
        return jsonify({"error": resultado["error"]}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/confirmar", methods=["POST"])
def confirmar_reserva():
    """
    Confirmar la compra de un ticket reservado.
    ---
    tags:
      - Reservas
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - ticket_id
            - usuario_id
          properties:
            ticket_id:
              type: integer
              example: 5
            usuario_id:
              type: integer
              example: 42
    responses:
      200:
        description: Compra confirmada exitosamente
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "¡Compra confirmada exitosamente!"
      400:
        description: No se pudo confirmar (reserva expirada o no existe)
      500:
        description: Error interno del servidor
    """
    try:
        datos = request.get_json()
        resultado = reserva_service.confirmar(datos.get("ticket_id"), datos.get("usuario_id"))
        if resultado["ok"]:
            return jsonify({"mensaje": "¡Compra confirmada exitosamente!"}), 200
        return jsonify({"error": resultado["error"]}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reservas/<int:ticket_id>", methods=["DELETE"])
def eliminar_reserva(ticket_id):
    """
    Cancelar la reserva de un ticket.
    ---
    tags:
      - Reservas
    parameters:
      - name: ticket_id
        in: path
        type: integer
        required: true
        description: ID del ticket a cancelar
        example: 5
    responses:
      200:
        description: Reserva cancelada exitosamente
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: Reserva del ticket 5 eliminada correctamente.
      404:
        description: Reserva no encontrada
      500:
        description: Error interno del servidor
    """
    try:
        resultado = reserva_service.cancelar(ticket_id)
        if resultado["ok"]:
            return jsonify({"mensaje": f"Reserva del ticket {ticket_id} eliminada correctamente."}), 200
        return jsonify({"error": resultado["error"]}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

