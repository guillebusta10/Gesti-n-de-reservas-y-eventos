"""
Tests de integracion para las rutas HTTP de app.py
Requiere base de datos activa (docker-compose up -d).

Tickets asignados a estos tests: 21 y 22 (evento 3).
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest
import app as flask_app

# Tickets de evento 3 reservados para este archivo
TICKET_R1 = 21
TICKET_R2 = 22
USUARIO_ID = 1
EVENTO_ID  = 3


@pytest.fixture
def client():
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def limpiar(resetear):
    resetear(TICKET_R1, TICKET_R2)
    yield
    resetear(TICKET_R1, TICKET_R2)


# --- GET / ---------------------------------------------------------------

class TestIndex:

    def test_pagina_principal_responde(self, client):
        response = client.get("/")
        assert response.status_code == 200


# --- GET /eventos --------------------------------------------------------

class TestObtenerEventos:

    def test_retorna_lista_de_eventos(self, client):
        response = client.get("/eventos")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_cada_evento_tiene_campos_esperados(self, client):
        response = client.get("/eventos")
        evento = response.get_json()[0]
        assert "id" in evento
        assert "nombre" in evento


# --- GET /eventos/<id>/tickets -------------------------------------------

class TestObtenerTickets:

    def test_retorna_tickets_de_evento_existente(self, client):
        response = client.get(f"/eventos/{EVENTO_ID}/tickets")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_evento_inexistente_retorna_lista_vacia(self, client):
        response = client.get("/eventos/9999/tickets")
        assert response.status_code == 200
        assert response.get_json() == []


# --- GET /reservas -------------------------------------------------------

class TestObtenerReservas:

    def test_retorna_200_con_lista(self, client):
        response = client.get("/reservas")
        assert response.status_code == 200
        assert isinstance(response.get_json(), list)

    def test_reserva_reciente_aparece_en_listado(self, client):
        client.post(
            "/reservar",
            data=json.dumps({"ticket_id": TICKET_R1, "usuario_id": USUARIO_ID}),
            content_type="application/json"
        )
        response = client.get("/reservas")
        ids = [r["ticket_id"] for r in response.get_json()]
        assert TICKET_R1 in ids


# --- POST /reservar ------------------------------------------------------

class TestReservarTicket:

    def test_reservar_exitoso(self, client):
        response = client.post(
            "/reservar",
            data=json.dumps({"ticket_id": TICKET_R1, "usuario_id": USUARIO_ID}),
            content_type="application/json"
        )
        assert response.status_code == 200
        assert response.get_json()["ticket_id"] == TICKET_R1

    def test_confirmar_ticket_ya_confirmado_retorna_400(self, client):
        # Con la nueva lógica, reservar() siempre es exitoso para tickets válidos.
        # La competencia se resuelve en confirmar(): el segundo intento retorna 400.
        client.post(
            "/reservar",
            data=json.dumps({"ticket_id": TICKET_R1, "usuario_id": 1}),
            content_type="application/json"
        )
        client.post(
            "/confirmar",
            data=json.dumps({"ticket_id": TICKET_R1, "usuario_id": 1}),
            content_type="application/json"
        )
        response = client.post(
            "/confirmar",
            data=json.dumps({"ticket_id": TICKET_R1, "usuario_id": 2}),
            content_type="application/json"
        )
        assert response.status_code == 400
        assert "error" in response.get_json()

    def test_reservar_sin_datos_retorna_400(self, client):
        response = client.post(
            "/reservar",
            data=json.dumps({}),
            content_type="application/json"
        )
        # APIFlask retorna 422 (Unprocessable Entity) cuando faltan campos requeridos del schema
        assert response.status_code == 422


# --- POST /confirmar -----------------------------------------------------

class TestConfirmarReserva:

    def test_confirmar_exitoso(self, client):
        client.post(
            "/reservar",
            data=json.dumps({"ticket_id": TICKET_R1, "usuario_id": USUARIO_ID}),
            content_type="application/json"
        )
        response = client.post(
            "/confirmar",
            data=json.dumps({"ticket_id": TICKET_R1, "usuario_id": USUARIO_ID}),
            content_type="application/json"
        )
        assert response.status_code == 200
        assert "confirmada" in response.get_json()["mensaje"].lower()

    def test_confirmar_sin_reserva_retorna_400(self, client):
        response = client.post(
            "/confirmar",
            data=json.dumps({"ticket_id": TICKET_R1, "usuario_id": USUARIO_ID}),
            content_type="application/json"
        )
        assert response.status_code == 400


# --- DELETE /reservas/<id> -----------------------------------------------

class TestEliminarReserva:

    def test_cancelar_exitoso(self, client):
        client.post(
            "/reservar",
            data=json.dumps({"ticket_id": TICKET_R1, "usuario_id": USUARIO_ID}),
            content_type="application/json"
        )
        response = client.delete(f"/reservas/{TICKET_R1}")
        assert response.status_code == 200
        assert str(TICKET_R1) in response.get_json()["mensaje"]

    def test_cancelar_ticket_inexistente_retorna_404(self, client):
        response = client.delete("/reservas/9999")
        assert response.status_code == 404
