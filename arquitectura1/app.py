from flask import Flask, jsonify, request, render_template
from db import obtener_conexion
from repositories import evento_repo, ticket_repo
from services import reserva_service

app = Flask(__name__)


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
        return jsonify(evento_repo.obtener_todos())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/eventos/<int:evento_id>/tickets", methods=["GET"])
def obtener_tickets(evento_id):
    try:
        return jsonify(ticket_repo.obtener_disponibles(evento_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reservas", methods=["GET"])
def obtener_reservas():
    try:
        return jsonify(ticket_repo.obtener_reservas_activas())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reservar", methods=["POST"])
def reservar_ticket():
    try:
        datos = request.get_json()
        resultado = reserva_service.reservar(datos.get("ticket_id"), datos.get("usuario_id"))
        if resultado["ok"]:
            return jsonify({"mensaje": "Ticket bloqueado por 30 segundos", "ticket_id": resultado["ticket_id"]}), 200
        return jsonify({"error": resultado["error"]}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/confirmar", methods=["POST"])
def confirmar_reserva():
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
    try:
        resultado = reserva_service.cancelar(ticket_id)
        if resultado["ok"]:
            return jsonify({"mensaje": f"Reserva del ticket {ticket_id} eliminada correctamente."}), 200
        return jsonify({"error": resultado["error"]}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

