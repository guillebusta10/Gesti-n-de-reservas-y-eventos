"""
Pruebas unitarias para services/reserva_service.py

Se mockea ticket_repo para no necesitar base de datos real.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch
from services import reserva_service


# ─── reservar ───────────────────────────────────────────────────────────────

class TestReservar:

    @patch("services.reserva_service.ticket_repo.bloquear")
    def test_reservar_exitoso(self, mock_bloquear):
        """Cuando bloquear devuelve un ticket, el resultado es ok=True."""
        mock_bloquear.return_value = (42,)

        resultado = reserva_service.reservar(ticket_id=1, usuario_id=5)

        assert resultado["ok"] is True
        assert resultado["ticket_id"] == 42
        mock_bloquear.assert_called_once_with(1, 5)

    @patch("services.reserva_service.ticket_repo.bloquear")
    def test_reservar_ticket_ya_tomado(self, mock_bloquear):
        """Cuando bloquear devuelve None, el ticket ya fue tomado."""
        mock_bloquear.return_value = None

        resultado = reserva_service.reservar(ticket_id=1, usuario_id=5)

        assert resultado["ok"] is False
        assert "error" in resultado

    @patch("services.reserva_service.ticket_repo.bloquear")
    def test_reservar_llama_con_parametros_correctos(self, mock_bloquear):
        """Verifica que reservar pasa los ids correctos al repositorio."""
        mock_bloquear.return_value = (7,)

        reserva_service.reservar(ticket_id=99, usuario_id=3)

        mock_bloquear.assert_called_once_with(99, 3)


# ─── confirmar ──────────────────────────────────────────────────────────────

class TestConfirmar:

    @patch("services.reserva_service.ticket_repo.confirmar")
    def test_confirmar_exitoso(self, mock_confirmar):
        """Cuando confirmar devuelve resultado, ok=True."""
        mock_confirmar.return_value = (10,)

        resultado = reserva_service.confirmar(ticket_id=10, usuario_id=2)

        assert resultado["ok"] is True
        mock_confirmar.assert_called_once_with(10, 2)

    @patch("services.reserva_service.ticket_repo.confirmar")
    def test_confirmar_expirado_o_no_es_tuyo(self, mock_confirmar):
        """Cuando confirmar devuelve None, el tiempo expiró o no coincide usuario."""
        mock_confirmar.return_value = None

        resultado = reserva_service.confirmar(ticket_id=10, usuario_id=2)

        assert resultado["ok"] is False
        assert "error" in resultado


# ─── cancelar ───────────────────────────────────────────────────────────────

class TestCancelar:

    @patch("services.reserva_service.ticket_repo.liberar")
    def test_cancelar_exitoso(self, mock_liberar):
        """Cuando liberar devuelve resultado, ok=True y devuelve ticket_id."""
        mock_liberar.return_value = (5,)

        resultado = reserva_service.cancelar(ticket_id=5)

        assert resultado["ok"] is True
        assert resultado["ticket_id"] == 5
        mock_liberar.assert_called_once_with(5)

    @patch("services.reserva_service.ticket_repo.liberar")
    def test_cancelar_reserva_no_encontrada(self, mock_liberar):
        """Cuando liberar devuelve None, la reserva no existe."""
        mock_liberar.return_value = None

        resultado = reserva_service.cancelar(ticket_id=5)

        assert resultado["ok"] is False
        assert "error" in resultado
