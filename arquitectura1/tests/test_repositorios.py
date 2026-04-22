"""
Pruebas unitarias para repositories/evento_repo.py y ticket_repo.py

Se mockea obtener_conexion para no necesitar base de datos real.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
from repositories import evento_repo, ticket_repo


def crear_mock_conexion(filas=None, fetchone=None):
    """Helper que devuelve un mock de conexión con cursor configurado."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = filas or []
    mock_cursor.fetchone.return_value = fetchone

    mock_conexion = MagicMock()
    mock_conexion.cursor.return_value = mock_cursor

    return mock_conexion, mock_cursor


# ─── evento_repo ─────────────────────────────────────────────────────────────

class TestEventoRepo:

    @patch("repositories.evento_repo.obtener_conexion")
    def test_obtener_todos_devuelve_lista(self, mock_conn_fn):
        filas = [
            (1, "Concierto de Rock", "2026-05-10", "Estadio Nacional"),
            (2, "Festival de Jazz",  "2026-06-15", "Parque Central"),
        ]
        mock_conexion, _ = crear_mock_conexion(filas=filas)
        mock_conn_fn.return_value = mock_conexion

        resultado = evento_repo.obtener_todos()

        assert len(resultado) == 2
        assert resultado[0]["id"] == 1
        assert resultado[0]["nombre"] == "Concierto de Rock"
        assert resultado[1]["lugar"] == "Parque Central"

    @patch("repositories.evento_repo.obtener_conexion")
    def test_obtener_todos_lista_vacia(self, mock_conn_fn):
        mock_conexion, _ = crear_mock_conexion(filas=[])
        mock_conn_fn.return_value = mock_conexion

        resultado = evento_repo.obtener_todos()

        assert resultado == []

    @patch("repositories.evento_repo.obtener_conexion")
    def test_obtener_todos_cierra_conexion(self, mock_conn_fn):
        mock_conexion, _ = crear_mock_conexion(filas=[])
        mock_conn_fn.return_value = mock_conexion

        evento_repo.obtener_todos()

        mock_conexion.close.assert_called_once()


# ─── ticket_repo.obtener_disponibles ─────────────────────────────────────────

class TestObtenerDisponibles:

    @patch("repositories.ticket_repo.obtener_conexion")
    def test_retorna_tickets(self, mock_conn_fn):
        mock_conexion, _ = crear_mock_conexion(filas=[(1,), (2,), (3,)])
        mock_conn_fn.return_value = mock_conexion

        resultado = ticket_repo.obtener_disponibles(evento_id=1)

        assert len(resultado) == 3
        assert resultado[0]["ticket_id"] == 1

    @patch("repositories.ticket_repo.obtener_conexion")
    def test_sin_tickets_disponibles(self, mock_conn_fn):
        mock_conexion, _ = crear_mock_conexion(filas=[])
        mock_conn_fn.return_value = mock_conexion

        resultado = ticket_repo.obtener_disponibles(evento_id=99)

        assert resultado == []


# ─── ticket_repo.bloquear ────────────────────────────────────────────────────

class TestBloquear:

    @patch("repositories.ticket_repo.obtener_conexion")
    def test_bloquear_exitoso(self, mock_conn_fn):
        mock_conexion, _ = crear_mock_conexion(fetchone=(5,))
        mock_conn_fn.return_value = mock_conexion

        resultado = ticket_repo.bloquear(ticket_id=5, usuario_id=1)

        assert resultado == (5,)
        mock_conexion.commit.assert_called_once()

    @patch("repositories.ticket_repo.obtener_conexion")
    def test_bloquear_ticket_no_disponible(self, mock_conn_fn):
        mock_conexion, _ = crear_mock_conexion(fetchone=None)
        mock_conn_fn.return_value = mock_conexion

        resultado = ticket_repo.bloquear(ticket_id=5, usuario_id=1)

        assert resultado is None


# ─── ticket_repo.confirmar ───────────────────────────────────────────────────

class TestConfirmarRepo:

    @patch("repositories.ticket_repo.obtener_conexion")
    def test_confirmar_exitoso(self, mock_conn_fn):
        mock_conexion = MagicMock()
        mock_cursor = MagicMock()
        mock_conexion.cursor.return_value = mock_cursor
        # Primera llamada (SELECT): devuelve el usuario_id
        # Segunda llamada (UPDATE RETURNING): devuelve el ticket
        mock_cursor.fetchone.side_effect = [(1,), (10,)]
        mock_conn_fn.return_value = mock_conexion

        resultado = ticket_repo.confirmar(ticket_id=10, usuario_id=1)

        assert resultado == (10,)
        mock_conexion.commit.assert_called_once()

    @patch("repositories.ticket_repo.obtener_conexion")
    def test_confirmar_reserva_no_encontrada(self, mock_conn_fn):
        mock_conexion = MagicMock()
        mock_cursor = MagicMock()
        mock_conexion.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # no hay reserva activa
        mock_conn_fn.return_value = mock_conexion

        resultado = ticket_repo.confirmar(ticket_id=10, usuario_id=1)

        assert resultado is None


# ─── ticket_repo.liberar ─────────────────────────────────────────────────────

class TestLiberar:

    @patch("repositories.ticket_repo.obtener_conexion")
    def test_liberar_exitoso(self, mock_conn_fn):
        mock_conexion, _ = crear_mock_conexion(fetchone=(3,))
        mock_conn_fn.return_value = mock_conexion

        resultado = ticket_repo.liberar(ticket_id=3)

        assert resultado == (3,)
        mock_conexion.commit.assert_called_once()

    @patch("repositories.ticket_repo.obtener_conexion")
    def test_liberar_ticket_no_existente(self, mock_conn_fn):
        mock_conexion, _ = crear_mock_conexion(fetchone=None)
        mock_conn_fn.return_value = mock_conexion

        resultado = ticket_repo.liberar(ticket_id=99)

        assert resultado is None
