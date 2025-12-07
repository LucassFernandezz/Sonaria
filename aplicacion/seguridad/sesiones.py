# aplicacion/seguridad/sesiones.py

from flask import session
from persistencia.conexion import obtener_conexion

def crear_sesion(usuario_id, rol, email):
    session["usuario_id"] = usuario_id
    session["rol"] = rol
    session["email"] = email
    session["autenticado"] = True

def cerrar_sesion():
    session.clear()

def usuario_actual():
    """
    Devuelve datos del usuario actual, pero si el usuario está bloqueado
    o eliminado, lo desloguea automáticamente.
    """
    uid = session.get("usuario_id")
    if not uid:
        return None

    # Consulta estado REAL en DB
    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, email, rol, estado
        FROM usuarios
        WHERE id = %s
    """, (uid,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        # Usuario eliminado → cerrar sesión
        cerrar_sesion()
        return None

    if user["estado"] in ["bloqueado", "eliminado"]:
        # Usuario no debería poder operar → cerrar sesión
        cerrar_sesion()
        return None

    return {
        "usuario_id": user["id"],
        "email": user["email"],
        "rol": user["rol"],
        "estado": user["estado"]
    }

def rol_actual():
    u = usuario_actual()
    return u["rol"] if u else None

def esta_autenticado():
    """
    Este chequeo ahora también considera el estado real en la DB.
    """
    u = usuario_actual()
    return u is not None
