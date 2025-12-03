from flask import session

def crear_sesion(usuario_id, rol):
    session["usuario_id"] = usuario_id
    session["rol"] = rol
    session["autenticado"] = True

def cerrar_sesion():
    session.clear()

def usuario_actual():
    return session.get("usuario_id")

def rol_actual():
    return session.get("rol")

def esta_autenticado():
    return session.get("autenticado") is True
