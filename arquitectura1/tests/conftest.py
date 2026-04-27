"""
Fixtures compartidos para todos los tests de integración.
Requiere base de datos activa: docker-compose up -d
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from db import obtener_conexion


@pytest.fixture
def resetear():
    """
    Devuelve una función que restablece tickets a estado 'disponible'.
    Uso: resetear(ticket_id) o resetear(id1, id2, ...)
    """
    def _reset(*ticket_ids):
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        for tid in ticket_ids:
            cursor.execute(
                "UPDATE tickets SET estado='disponible', usuario_id=NULL, "
                "fecha_expiracion=NULL WHERE id=%s",
                (tid,)
            )
        conexion.commit()
        conexion.close()

    return _reset
