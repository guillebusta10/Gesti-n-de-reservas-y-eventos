from apiflask import APIFlask, Schema
from apiflask.fields import Integer
from flask import render_template
from db import obtener_conexion
from repositories import evento_repo, ticket_repo
from services import reserva_service

app = APIFlask(__name__, title="API Gestión de Reservas y Eventos", version="1.0.0")
app.config["SPEC_FORMAT"] = "json"
app.config["DOCS_UI"] = "swagger-ui"


# ── Schemas ───────────────────────────────────────────────────────────────────

class ReservaInput(Schema):
    ticket_id  = Integer(required=True, metadata={"example": 5})
    usuario_id = Integer(required=True, metadata={"example": 42})


# ── Rutas ─────────────────────────────────────────────────────────────────────

@app.get("/")
@app.doc(hide=True)
def index():
    return render_template("index.html")


@app.get("/test-db")
@app.doc(tags=["Sistema"], summary="Verificar conexión a la BD")
def test_db():
    try:
        conexion = obtener_conexion()
        conexion.close()
        return {"mensaje": "¡Conexión exitosa a PostgreSQL! 🎉", "estado": "ok"}
    except Exception as e:
        return {"mensaje": "Error al conectar a la BD", "error": str(e)}


@app.get("/eventos")
@app.doc(tags=["Eventos"], summary="Listar todos los eventos disponibles")
def obtener_eventos():
    try:
        return evento_repo.obtener_todos()
    except Exception as e:
        return {"error": str(e)}, 500


@app.get("/eventos/<int:evento_id>/tickets")
@app.doc(tags=["Eventos"], summary="Tickets disponibles de un evento")
def obtener_tickets(evento_id):
    try:
        return ticket_repo.obtener_disponibles(evento_id)
    except Exception as e:
        return {"error": str(e)}, 500


@app.get("/reservas")
@app.doc(tags=["Reservas"], summary="Listar todas las reservas activas")
def obtener_reservas():
    try:
        return ticket_repo.obtener_reservas_activas()
    except Exception as e:
        return {"error": str(e)}, 500


@app.post("/reservar")
@app.input(ReservaInput, arg_name="datos")
@app.doc(tags=["Reservas"], summary="Reservar un ticket (bloqueo de 30 segundos)")
def reservar_ticket(datos):
    resultado = reserva_service.reservar(datos["ticket_id"], datos["usuario_id"])
    if resultado["ok"]:
        return {"mensaje": "Ticket bloqueado por 30 segundos", "ticket_id": resultado["ticket_id"]}
    return {"error": resultado["error"]}, 409


@app.post("/confirmar")
@app.input(ReservaInput, arg_name="datos")
@app.doc(tags=["Reservas"], summary="Confirmar la compra de un ticket reservado")
def confirmar_reserva(datos):
    resultado = reserva_service.confirmar(datos["ticket_id"], datos["usuario_id"])
    if resultado["ok"]:
        return {"mensaje": "¡Compra confirmada exitosamente!"}
    return {"error": resultado["error"]}, 400


@app.delete("/reservas/<int:ticket_id>")
@app.doc(tags=["Reservas"], summary="Cancelar una reserva activa")
def eliminar_reserva(ticket_id):
    resultado = reserva_service.cancelar(ticket_id)
    if resultado["ok"]:
        return {"mensaje": f"Reserva del ticket {ticket_id} eliminada correctamente."}
    return {"error": resultado["error"]}, 404


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

