"""
Tests de integracion para services/reserva_service.py
Requiere base de datos activa (docker-compose up -d).

Ticket asignado a estos tests: 11 (evento 2).
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from services import reserva_service

# Ticket de evento 2 reservado para este archivo
TICKET_SVC = 11
USUARIO_A  = 1
USUARIO_B  = 2


@pytest.fixture(autouse=True)
def limpiar(resetear):
    resetear(TICKET_SVC)
    yield
    resetear(TICKET_SVC)


# --- reserva_service.reservar --------------------------------------------

class TestReservar:

    def test_reservar_exitoso(self):
        resultado = reserva_service.reservar(TICKET_SVC, USUARIO_A)
        assert resultado["ok"] is True
        assert resultado["ticket_id"] == TICKET_SVC

    def test_reservar_ticket_ya_tomado_falla(self):
        # Primer usuario reserva
        reserva_service.reservar(TICKET_SVC, USUARIO_A)
        # Segundo usuario intenta el mismo ticket
        resultado = reserva_service.reservar(TICKET_SVC, USUARIO_B)
        assert resultado["ok"] is False
        assert "error" in resultado

    def test_reservar_retorna_error_si_ticket_no_existe(self):
        resultado = reserva_service.reservar(ticket_id=9999, usuario_id=USUARIO_A)
        assert resultado["ok"] is False


# --- reserva_service.confirmar -------------------------------------------

class TestConfirmar:

    def test_confirmar_exitoso(self):
        reserva_service.reservar(TICKET_SVC, USUARIO_A)
        resultado = reserva_service.confirmar(TICKET_SVC, USUARIO_A)
        assert resultado["ok"] is True

    def test_confirmar_sin_reserva_previa_falla(self):
        resultado = reserva_service.confirmar(TICKET_SVC, USUARIO_A)
        assert resultado["ok"] is False
        assert "error" in resultado

    def test_confirmar_usuario_incorrecto_falla(self):
        reserva_service.reservar(TICKET_SVC, USUARIO_A)
        resultado = reserva_service.confirmar(TICKET_SVC, usuario_id=99)
        assert resultado["ok"] is False
        assert "error" in resultado


# --- reserva_service.cancelar --------------------------------------------

class TestCancelar:

    def test_cancelar_exitoso(self):
        reserva_service.reservar(TICKET_SVC, USUARIO_A)
        resultado = reserva_service.cancelar(TICKET_SVC)
        assert resultado["ok"] is True
        assert resultado["ticket_id"] == TICKET_SVC

    def test_cancelar_libera_ticket_para_nuevo_uso(self):
        reserva_service.reservar(TICKET_SVC, USUARIO_A)
        reserva_service.cancelar(TICKET_SVC)
        # Despues de cancelar, otro usuario puede reservar
        resultado = reserva_service.reservar(TICKET_SVC, USUARIO_B)
        assert resultado["ok"] is True

    def test_cancelar_ticket_inexistente_falla(self):
        resultado = reserva_service.cancelar(ticket_id=9999)
        assert resultado["ok"] is False
