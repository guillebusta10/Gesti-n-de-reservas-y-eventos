"""
Test de condición de carrera
============================
Simula N usuarios que intentan reservar el MISMO ticket exactamente al mismo tiempo.

Requiere que la base de datos esté corriendo (docker-compose up).

Ejecutar:
    cd arquitectura1
    python -m pytest tests/test_condicion_carrera.py -v -s

O directamente:
    python tests/test_condicion_carrera.py
"""

import sys
import os
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from repositories import ticket_repo
from services import reserva_service

# ─── Configuración ────────────────────────────────────────────────────────────
TICKET_ID  = 1   # Ticket que todos intentarán reservar (debe existir en la BD)
N_USUARIOS = 8   # Hilos simultáneos (usuarios concurrentes)


# ─── Helper: resetear ticket a 'disponible' antes de cada prueba ──────────────
def _resetear_ticket(ticket_id: int) -> None:
    """Devuelve el ticket a estado 'disponible' sin importar su estado actual."""
    from db import obtener_conexion
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute(
        """
        UPDATE tickets
        SET estado = 'disponible',
            usuario_id = NULL,
            fecha_expiracion = NULL
        WHERE id = %s;
        """,
        (ticket_id,),
    )
    conexion.commit()
    conexion.close()


# ─── Escenario 1: código ACTUAL (sin protección) ──────────────────────────────
def test_race_condition_sin_proteccion():
    """
    DEMUESTRA la condición de carrera en bloquear() actual.

    Sin 'AND estado = disponible' en el WHERE, el segundo hilo
    sobrescribe la reserva del primero y TAMBIÉN devuelve éxito.
    Resultado esperado si el bug existe: éxitos > 1.
    """
    _resetear_ticket(TICKET_ID)

    resultados = []
    errores    = []
    barrera    = threading.Barrier(N_USUARIOS)  # todos arrancan al mismo tiempo

    def intentar_reservar(usuario_id: int) -> None:
        barrera.wait()  # sincronización: espera hasta que todos estén listos
        try:
            res = reserva_service.reservar(TICKET_ID, usuario_id)
            resultados.append(res)
        except Exception as exc:
            errores.append(str(exc))

    hilos = [
        threading.Thread(target=intentar_reservar, args=(uid,))
        for uid in range(1, N_USUARIOS + 1)
    ]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    exitosos = [r for r in resultados if r["ok"]]
    fallidos  = [r for r in resultados if not r["ok"]]

    print("\n" + "=" * 60)
    print("  ESCENARIO: código sin protección (bug actual)")
    print("=" * 60)
    print(f"  Usuarios concurrentes : {N_USUARIOS}")
    print(f"  Reservas EXITOSAS     : {len(exitosos)}")
    print(f"  Reservas fallidas     : {len(fallidos)}")
    print(f"  Errores de hilo       : {len(errores)}")

    if len(exitosos) > 1:
        print(
            f"\n  ⚠️  RACE CONDITION DETECTADA: {len(exitosos)} usuarios "
            "creen tener el mismo ticket."
        )
    else:
        print("\n  ✅ Solo 1 usuario obtuvo el ticket (PostgreSQL serializó correctamente).")
    print("=" * 60)

    # Este assert falla si hay condición de carrera (que es lo que esperamos mostrar)
    assert len(exitosos) == 1, (
        f"Race condition detectada: {len(exitosos)} usuarios 'ganaron' el mismo ticket. "
        "Falta 'AND estado = disponible' en bloquear()."
    )


# ─── Escenario 2: código CORREGIDO (con protección de estado) ─────────────────
def test_race_condition_con_proteccion():
    """
    Verifica que agregando 'AND estado = disponible' al UPDATE se elimina la race condition.

    Se parchea temporalmente ticket_repo.bloquear con la versión segura.
    Solo 1 usuario debe poder reservar; el resto recibe ok=False.
    """
    from db import obtener_conexion
    from unittest.mock import patch

    def bloquear_seguro(ticket_id: int, usuario_id: int):
        """Versión protegida: comprueba el estado antes de reservar."""
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE tickets
            SET estado = 'reservado',
                usuario_id = %s,
                fecha_expiracion = NOW() + INTERVAL '30 seconds'
            WHERE id = %s
              AND estado = 'disponible'   -- ← protección contra race condition
            RETURNING id;
            """,
            (usuario_id, ticket_id),
        )
        resultado = cursor.fetchone()
        conexion.commit()
        conexion.close()
        return resultado

    _resetear_ticket(TICKET_ID)

    resultados = []
    barrera    = threading.Barrier(N_USUARIOS)

    def intentar_reservar(usuario_id: int) -> None:
        barrera.wait()
        with patch("services.reserva_service.ticket_repo.bloquear", bloquear_seguro):
            res = reserva_service.reservar(TICKET_ID, usuario_id)
        resultados.append(res)

    hilos = [
        threading.Thread(target=intentar_reservar, args=(uid,))
        for uid in range(1, N_USUARIOS + 1)
    ]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    exitosos = [r for r in resultados if r["ok"]]
    fallidos  = [r for r in resultados if not r["ok"]]

    print("\n" + "=" * 60)
    print("  ESCENARIO: código corregido (con AND estado = 'disponible')")
    print("=" * 60)
    print(f"  Usuarios concurrentes : {N_USUARIOS}")
    print(f"  Reservas EXITOSAS     : {len(exitosos)}")
    print(f"  Reservas fallidas     : {len(fallidos)}")
    print("\n  ✅ Solo 1 usuario pudo reservar. Race condition eliminada.")
    print("=" * 60)

    assert len(exitosos) == 1, (
        f"Se esperaba exactamente 1 reserva exitosa, pero hubo {len(exitosos)}."
    )
    assert len(fallidos) == N_USUARIOS - 1


# ─── Ejecución directa ────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n>>> Ejecutando prueba SIN protección (bug actual)...")
    try:
        test_race_condition_sin_proteccion()
        print(">>> PASÓ (PostgreSQL serializó, no hubo doble reserva)")
    except AssertionError as e:
        print(f">>> FALLÓ → {e}")

    print("\n>>> Ejecutando prueba CON protección (fix propuesto)...")
    try:
        test_race_condition_con_proteccion()
        print(">>> PASÓ ✅")
    except AssertionError as e:
        print(f">>> FALLÓ → {e}")
