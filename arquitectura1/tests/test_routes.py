"""
Pruebas unitarias para los endpoints HTTP de app.py

Se mockean los repositorios y servicios para no necesitar base de datos.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from unittest.mock import patch
import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ─── GET /eventos ────────────────────────────────────────────────────────────

class TestObtenerEventos:

    @patch("app.evento_repo.obtener_todos")
    def test_retorna_lista_de_eventos(self, mock_repo, client):
        mock_repo.return_value = [
            {"id": 1, "nombre": "Concierto de Rock", "fecha": "2026-05-10", "lugar": "Estadio Nacional"},
            {"id": 2, "nombre": "Festival de Jazz",  "fecha": "2026-06-15", "lugar": "Parque Central"},
        ]

        response = client.get("/eventos")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        assert data[0]["nombre"] == "Concierto de Rock"

    @patch("app.evento_repo.obtener_todos")
    def test_retorna_500_si_falla_repo(self, mock_repo, client):
        mock_repo.side_effect = Exception("Error de BD")

        response = client.get("/eventos")

        assert response.status_code == 500
        assert "error" in response.get_json()


# ─── GET /eventos/<id>/tickets ───────────────────────────────────────────────

class TestObtenerTickets:

    @patch("app.ticket_repo.obtener_disponibles")
    def test_retorna_tickets_disponibles(self, mock_repo, client):
        mock_repo.return_value = [{"ticket_id": 1}, {"ticket_id": 2}]

        response = client.get("/eventos/1/tickets")

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        mock_repo.assert_called_once_with(1)

    @patch("app.ticket_repo.obtener_disponibles")
    def test_retorna_500_si_falla_repo(self, mock_repo, client):
        mock_repo.side_effect = Exception("Error")

        response = client.get("/eventos/1/tickets")

        assert response.status_code == 500


# ─── GET /reservas ───────────────────────────────────────────────────────────

class TestObtenerReservas:

    @patch("app.ticket_repo.obtener_reservas_activas")
    def test_retorna_reservas_activas(self, mock_repo, client):
        mock_repo.return_value = [
            {"ticket_id": 3, "usuario_nombre": "Ana García", "evento_nombre": "Concierto", "estado": "reservado"}
        ]

        response = client.get("/reservas")

        assert response.status_code == 200
        data = response.get_json()
        assert data[0]["estado"] == "reservado"


# ─── POST /reservar ──────────────────────────────────────────────────────────

class TestReservarTicket:

    @patch("app.reserva_service.reservar")
    def test_reservar_exitoso(self, mock_service, client):
        mock_service.return_value = {"ok": True, "ticket_id": 5}

        response = client.post("/reservar",
                               data=json.dumps({"ticket_id": 5, "usuario_id": 1}),
                               content_type="application/json")

        assert response.status_code == 200
        assert response.get_json()["ticket_id"] == 5

    @patch("app.reserva_service.reservar")
    def test_reservar_ticket_ya_tomado(self, mock_service, client):
        mock_service.return_value = {"ok": False, "error": "El ticket acaba de ser tomado"}

        response = client.post("/reservar",
                               data=json.dumps({"ticket_id": 5, "usuario_id": 1}),
                               content_type="application/json")

        assert response.status_code == 409
        assert "error" in response.get_json()


# ─── POST /confirmar ─────────────────────────────────────────────────────────

class TestConfirmarReserva:

    @patch("app.reserva_service.confirmar")
    def test_confirmar_exitoso(self, mock_service, client):
        mock_service.return_value = {"ok": True}

        response = client.post("/confirmar",
                               data=json.dumps({"ticket_id": 5, "usuario_id": 1}),
                               content_type="application/json")

        assert response.status_code == 200
        assert "confirmada" in response.get_json()["mensaje"].lower()

    @patch("app.reserva_service.confirmar")
    def test_confirmar_tiempo_expirado(self, mock_service, client):
        mock_service.return_value = {"ok": False, "error": "El tiempo de 30s expiró"}

        response = client.post("/confirmar",
                               data=json.dumps({"ticket_id": 5, "usuario_id": 1}),
                               content_type="application/json")

        assert response.status_code == 400


# ─── DELETE /reservas/<id> ───────────────────────────────────────────────────

class TestEliminarReserva:

    @patch("app.reserva_service.cancelar")
    def test_cancelar_exitoso(self, mock_service, client):
        mock_service.return_value = {"ok": True, "ticket_id": 3}

        response = client.delete("/reservas/3")

        assert response.status_code == 200
        assert "3" in response.get_json()["mensaje"]

    @patch("app.reserva_service.cancelar")
    def test_cancelar_no_encontrado(self, mock_service, client):
        mock_service.return_value = {"ok": False, "error": "No se encontró la reserva"}

        response = client.delete("/reservas/99")

        assert response.status_code == 404
