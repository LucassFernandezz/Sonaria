from flask import session

def crear_sesion(usuario_id, rol, email):
    session["usuario_id"] = usuario_id
    session["rol"] = rol
    session["email"] = email
    session["autenticado"] = True

def cerrar_sesion():
    session.clear()

def usuario_actual():
    return {
        "usuario_id": session.get("usuario_id"),
        "rol": session.get("rol"),
        "email": session.get("email")
    }

def rol_actual():
    return session.get("rol")

def esta_autenticado():
    return session.get("autenticado") is True
