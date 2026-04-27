"""
Tests de integracion para repositories/evento_repo.py y ticket_repo.py
Requiere base de datos activa (docker-compose up -d).

Tickets asignados a estos tests: 1 y 2 (evento 1).
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from db import obtener_conexion
from repositories import evento_repo, ticket_repo

# Tickets de evento 1 reservados para este archivo de tests
TICKET_A = 1
TICKET_B = 2
USUARIO_ID = 1


@pytest.fixture(autouse=True)
def limpiar(resetear):
    """Restablece los tickets antes y despues de cada test."""
    resetear(TICKET_A, TICKET_B)
    yield
    resetear(TICKET_A, TICKET_B)


# --- evento_repo.obtener_todos -------------------------------------------

class TestEventoRepo:

    def test_retorna_lista_de_eventos(self):
        resultado = evento_repo.obtener_todos()
        assert isinstance(resultado, list)
        assert len(resultado) >= 1

    def test_cada_evento_tiene_campos_esperados(self):
        resultado = evento_repo.obtener_todos()
        evento = resultado[0]
        assert "id" in evento
        assert "nombre" in evento
        assert "fecha" in evento
        assert "lugar" in evento


# --- ticket_repo.obtener_disponibles -------------------------------------

class TestObtenerDisponibles:

    def test_retorna_tickets_de_evento_existente(self):
        resultado = ticket_repo.obtener_disponibles(evento_id=1)
        assert len(resultado) >= 1
        assert "ticket_id" in resultado[0]

    def test_evento_inexistente_retorna_lista_vacia(self):
        resultado = ticket_repo.obtener_disponibles(evento_id=9999)
        assert resultado == []

    def test_ticket_confirmado_no_aparece_en_disponibles(self):
        # obtener_disponibles muestra 'disponible' y 'reservado', pero no 'confirmado'
        ticket_repo.bloquear(TICKET_A, USUARIO_ID)
        ticket_repo.confirmar(TICKET_A, USUARIO_ID)
        disponibles = ticket_repo.obtener_disponibles(evento_id=1)
        ids = [t["ticket_id"] for t in disponibles]
        assert TICKET_A not in ids


# --- ticket_repo.bloquear ------------------------------------------------

class TestBloquear:

    def test_bloquear_retorna_id_del_ticket(self):
        resultado = ticket_repo.bloquear(TICKET_A, USUARIO_ID)
        assert resultado is not None
        assert resultado[0] == TICKET_A

    def test_estado_cambia_a_reservado_en_bd(self):
        ticket_repo.bloquear(TICKET_A, USUARIO_ID)

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT estado FROM tickets WHERE id=%s", (TICKET_A,))
        estado = cursor.fetchone()[0]
        conexion.close()

        assert estado == "reservado"

    def test_usuario_id_queda_registrado_en_bd(self):
        ticket_repo.bloquear(TICKET_A, USUARIO_ID)

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT usuario_id FROM tickets WHERE id=%s", (TICKET_A,))
        uid = cursor.fetchone()[0]
        conexion.close()

        assert uid == USUARIO_ID


# --- ticket_repo.confirmar -----------------------------------------------

class TestConfirmarRepo:

    def test_confirmar_exitoso(self):
        ticket_repo.bloquear(TICKET_A, USUARIO_ID)
        resultado = ticket_repo.confirmar(TICKET_A, USUARIO_ID)
        assert resultado is not None
        assert resultado[0] == TICKET_A

    def test_estado_cambia_a_confirmado_en_bd(self):
        ticket_repo.bloquear(TICKET_A, USUARIO_ID)
        ticket_repo.confirmar(TICKET_A, USUARIO_ID)

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT estado FROM tickets WHERE id=%s", (TICKET_A,))
        estado = cursor.fetchone()[0]
        conexion.close()

        assert estado == "confirmado"

    def test_confirmar_sin_reserva_previa_retorna_none(self):
        # Ticket esta disponible, no reservado
        resultado = ticket_repo.confirmar(TICKET_A, USUARIO_ID)
        assert resultado is None

    def test_confirmar_usuario_incorrecto_retorna_none(self):
        ticket_repo.bloquear(TICKET_A, USUARIO_ID)
        resultado = ticket_repo.confirmar(TICKET_A, usuario_id=99)
        assert resultado is None


# --- ticket_repo.liberar -------------------------------------------------

class TestLiberar:

    def test_liberar_retorna_id_del_ticket(self):
        ticket_repo.bloquear(TICKET_A, USUARIO_ID)
        resultado = ticket_repo.liberar(TICKET_A)
        assert resultado is not None
        assert resultado[0] == TICKET_A

    def test_estado_vuelve_a_disponible_en_bd(self):
        ticket_repo.bloquear(TICKET_A, USUARIO_ID)
        ticket_repo.liberar(TICKET_A)

        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT estado FROM tickets WHERE id=%s", (TICKET_A,))
        estado = cursor.fetchone()[0]
        conexion.close()

        assert estado == "disponible"

    def test_ticket_vuelve_a_aparecer_en_disponibles(self):
        ticket_repo.bloquear(TICKET_A, USUARIO_ID)
        ticket_repo.liberar(TICKET_A)

        disponibles = ticket_repo.obtener_disponibles(evento_id=1)
        ids = [t["ticket_id"] for t in disponibles]
        assert TICKET_A in ids
