from repositories import ticket_repo


def reservar(ticket_id, usuario_id):
    resultado = ticket_repo.bloquear(ticket_id, usuario_id)
    if resultado:
        return {"ok": True, "ticket_id": resultado[0]}
    return {"ok": False, "error": "El ticket ya fue comprado."}


def confirmar(ticket_id, usuario_id):
    resultado = ticket_repo.confirmar(ticket_id, usuario_id)
    if resultado:
        return {"ok": True}
    return {"ok": False, "error": "El tiempo de 30s expiró o el ticket fue confirmado."}


def cancelar(ticket_id):
    resultado = ticket_repo.liberar(ticket_id)
    if resultado:
        return {"ok": True, "ticket_id": ticket_id}
    return {"ok": False, "error": "No se encontró la reserva o ya estaba cancelada."}
