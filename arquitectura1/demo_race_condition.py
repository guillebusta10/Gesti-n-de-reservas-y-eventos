"""
Demo de condición de carrera vía HTTP
======================================
Simula N usuarios intentando reservar el MISMO ticket al mismo tiempo
enviando peticiones HTTP reales al servidor Flask.

Uso:
    # 1. Levanta la app en otra terminal:
    #    python app.py   (o flask --app app.py run)
    #
    # 2. Corre este script (tú o tu compañero, o ambos a la vez):
    #    python demo_race_condition.py
    #
    # Parámetros ajustables abajo (BASE_URL, TICKET_ID, N_USUARIOS)
"""

import threading
import urllib.request
import urllib.error
import json
import time

# ─── Configuración ────────────────────────────────────────────────────────────
BASE_URL  = "http://127.0.0.1:5000"   # cambia a la IP del compañero si corre en otra máquina
TICKET_ID = 1                          # ticket que todos intentarán reservar
N_USUARIOS = 10                        # hilos simultáneos por ejecución del script


# ─── Helpers HTTP (sin dependencias externas) ─────────────────────────────────
def _post(url: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def _delete(url: str) -> tuple[int, dict]:
    req = urllib.request.Request(url, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


# ─── Resetear ticket ──────────────────────────────────────────────────────────
def resetear_via_api(ticket_id: int) -> None:
    """Cancela la reserva del ticket vía DELETE /reservas/{id} para dejarlo 'disponible'."""
    _delete(f"{BASE_URL}/reservas/{ticket_id}")


# ─── Demo ─────────────────────────────────────────────────────────────────────
def main():
    print(f"\nConectando a {BASE_URL} ...")

    # Verificar que la app está corriendo
    try:
        urllib.request.urlopen(f"{BASE_URL}/", timeout=5)
    except Exception:
        print(f"\n  ERROR: no se pudo conectar a {BASE_URL}")
        print("  Asegúrate de que la app Flask está corriendo:\n")
        print("    python app.py\n")
        return

    print(f"App activa. Reseteando ticket {TICKET_ID}...")
    resetear_via_api(TICKET_ID)
    time.sleep(0.3)

    resultados = []
    lock     = threading.Lock()
    barrera  = threading.Barrier(N_USUARIOS)  # sincronización: todos disparan juntos

    def intentar_reservar(usuario_id: int) -> None:
        barrera.wait()  # ← espera hasta que todos los hilos estén listos
        status, body = _post(
            f"{BASE_URL}/reservar",
            {"ticket_id": TICKET_ID, "usuario_id": usuario_id},
        )
        with lock:
            resultados.append({"usuario": usuario_id, "status": status, "resp": body})

    print(f"Lanzando {N_USUARIOS} usuarios simultáneos sobre ticket {TICKET_ID}...\n")

    hilos = [threading.Thread(target=intentar_reservar, args=(uid,)) for uid in range(1, N_USUARIOS + 1)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    # ─── Resultados ───────────────────────────────────────────────────────────
    exitosos = [r for r in resultados if r["status"] == 200]
    fallidos  = [r for r in resultados if r["status"] != 200]

    print("=" * 60)
    print(f"  Ticket disputado      : {TICKET_ID}")
    print(f"  Usuarios concurrentes : {N_USUARIOS}")
    print(f"  Reservas EXITOSAS     : {len(exitosos)}")
    print(f"  Reservas fallidas     : {len(fallidos)}")
    print("=" * 60)

    if exitosos:
        print("\n  Usuarios que obtuvieron el ticket:")
        for r in exitosos:
            print(f"    → Usuario {r['usuario']:>2}  |  respuesta: {r['resp']}")

    if len(exitosos) > 1:
        print(f"\n  ⚠️  RACE CONDITION: {len(exitosos)} usuarios creen tener el mismo ticket.")
        print("     En una compra real, solo uno debería ganar.")
    else:
        print("\n  ✅ Solo 1 usuario ganó el ticket. No hubo race condition detectable.")

    print("=" * 60)


if __name__ == "__main__":
    main()
