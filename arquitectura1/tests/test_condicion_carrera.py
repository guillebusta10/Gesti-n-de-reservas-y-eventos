"""
Test de condición de carrera
============================
Con la arquitectura de reservas_temporales:
- reservar()  → TODOS los usuarios insertan en reservas_temporales (ok=True para todos)
- confirmar() → solo el PRIMERO que actualiza tickets a 'confirmado' gana (AND estado='reservado')

Verifica que solo 1 usuario puede confirmar; el resto recibe ok=False.

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
    """Devuelve el ticket a 'disponible' y limpia reservas_temporales."""
    from db import obtener_conexion
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM reservas_temporales WHERE ticket_id = %s;", (ticket_id,))
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


# ─── Escenario: múltiples reservas → solo 1 confirmación ─────────────────────
def test_race_condition_con_proteccion():
    """
    Con la nueva arquitectura:
    - Fase 1: TODOS los usuarios llaman a reservar() → todos obtienen ok=True
      (se insertan en reservas_temporales; el ticket pasa a 'reservado')
    - Fase 2: TODOS intentan confirmar() al mismo tiempo.
      Solo el primero cuyo UPDATE encuentra estado='reservado' gana.
      El resto recibe ok=False porque el ticket ya está 'confirmado'.

    Verifica que exactamente 1 usuario confirma y los demás fallan.
    """
    _resetear_ticket(TICKET_ID)

    # Usuarios válidos en la BD (IDs 1, 2, 3); se ciclan para N_USUARIOS hilos
    usuario_ids = [(i % 3) + 1 for i in range(N_USUARIOS)]

    # Fase 1: todos reservan — todos deben tener ok=True
    for uid in usuario_ids:
        res = reserva_service.reservar(TICKET_ID, uid)
        assert res["ok"] is True, f"Usuario {uid} no pudo reservar: {res}"

    # Fase 2: todos intentan confirmar al mismo tiempo
    resultados = []
    barrera    = threading.Barrier(N_USUARIOS)

    def intentar_confirmar(usuario_id: int) -> None:
        barrera.wait()
        res = reserva_service.confirmar(TICKET_ID, usuario_id)
        resultados.append(res)

    hilos = [
        threading.Thread(target=intentar_confirmar, args=(uid,))
        for uid in usuario_ids
    ]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    exitosos = [r for r in resultados if r["ok"]]
    fallidos  = [r for r in resultados if not r["ok"]]

    print("\n" + "=" * 60)
    print("  ESCENARIO: múltiples reservas → solo 1 confirmación")
    print("=" * 60)
    print(f"  Usuarios concurrentes  : {N_USUARIOS}")
    print(f"  Confirmaciones EXITOSAS: {len(exitosos)}")
    print(f"  Confirmaciones fallidas: {len(fallidos)}")
    print("\n  ✅ Solo 1 usuario pudo confirmar. Race condition eliminada.")
    print("=" * 60)

    assert len(exitosos) == 1, (
        f"Se esperaba exactamente 1 confirmación exitosa, pero hubo {len(exitosos)}."
    )
    assert len(fallidos) == N_USUARIOS - 1


# ─── Ejecución directa ────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n>>> Ejecutando prueba de race condition en confirmar()...")
    try:
        test_race_condition_con_proteccion()
        print(">>> PASÓ ✅")
    except AssertionError as e:
        print(f">>> FALLÓ → {e}")
