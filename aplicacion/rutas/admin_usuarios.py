# aplicacion/rutas/admin_usuarios.py
from flask import Blueprint, jsonify, request
from aplicacion.seguridad.sesiones import esta_autenticado, usuario_actual
from aplicacion.seguridad.auditoria import registrar_evento
from persistencia.conexion import obtener_conexion
from werkzeug.security import generate_password_hash

admin_usuarios_bp = Blueprint("admin_usuarios_bp", __name__, url_prefix="/admin/usuarios")


# ======================================================
# Validar ADMIN
# ======================================================
def require_admin():
    if not esta_autenticado():
        return None, jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()
    if user["rol"] != "admin":
        return None, jsonify({"ok": False, "error": "Solo admin"}), 403

    return user, None, None



# ======================================================
# 1) LISTAR TODOS LOS USUARIOS
# ======================================================
@admin_usuarios_bp.get("/")
def listar_usuarios():

    user, resp, code = require_admin()
    if resp:
        return resp, code

    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, email, rol, estado, fecha_registro
        FROM usuarios
        ORDER BY id DESC
    """)
    datos = cursor.fetchall()

    cursor.close()
    conn.close()

    registrar_evento(
        usuario_id=user["usuario_id"],
        accion="admin_listar_usuarios",
        detalles={"total": len(datos)}
    )

    return jsonify({"ok": True, "usuarios": datos})
    


# ======================================================
# 2) VER INFO DE UN USUARIO
# ======================================================
@admin_usuarios_bp.get("/info/<int:uid>")
def info_usuario(uid):

    user, resp, code = require_admin()
    if resp:
        return resp, code

    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, email, rol, estado, fecha_registro
        FROM usuarios
        WHERE id = %s
    """, (uid,))
    datos = cursor.fetchone()

    cursor.close()
    conn.close()

    if not datos:
        return jsonify({"ok": False, "error": "Usuario no encontrado"}), 404

    registrar_evento(
        usuario_id=user["usuario_id"],
        accion="admin_ver_info_usuario",
        detalles={"usuario_visto": uid}
    )

    return jsonify({"ok": True, "usuario": datos})



# ======================================================
# 3) BLOQUEAR / DESBLOQUEAR USUARIO
# ======================================================
@admin_usuarios_bp.post("/bloquear/<int:uid>")
def bloquear_usuario(uid):

    user, resp, code = require_admin()
    if resp:
        return resp, code

    nuevo_estado = request.json.get("estado")

    if nuevo_estado not in ["activo", "bloqueado"]:
        return jsonify({"ok": False, "error": "Estado inválido"}), 400

    conn = obtener_conexion()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET estado = %s
        WHERE id = %s
    """, (nuevo_estado, uid))

    conn.commit()
    cursor.close()
    conn.close()

    registrar_evento(
        usuario_id=user["usuario_id"],
        accion="admin_cambia_estado_usuario",
        detalles={"usuario": uid, "nuevo_estado": nuevo_estado}
    )

    return jsonify({"ok": True, "mensaje": "Estado actualizado"})



# ======================================================
# 4) CAMBIAR ROL
# ======================================================
@admin_usuarios_bp.post("/cambiar_rol/<int:uid>")
def cambiar_rol(uid):

    user, resp, code = require_admin()
    if resp:
        return resp, code

    nuevo_rol = request.json.get("rol")

    if nuevo_rol not in ["visitante", "registrado", "admin"]:
        return jsonify({"ok": False, "error": "Rol inválido"}), 400


    conn = obtener_conexion()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET rol = %s
        WHERE id = %s
    """, (nuevo_rol, uid))

    conn.commit()
    cursor.close()
    conn.close()

    registrar_evento(
        usuario_id=user["usuario_id"],
        accion="admin_cambia_rol",
        detalles={"usuario": uid, "nuevo_rol": nuevo_rol}
    )

    return jsonify({"ok": True, "mensaje": "Rol actualizado"})



# ======================================================
# 5) RESETEAR CONTRASEÑA
# ======================================================
@admin_usuarios_bp.post("/reset_pass/<int:uid>")
def resetear_password(uid):

    user, resp, code = require_admin()
    if resp:
        return resp, code

    nueva = request.json.get("nueva")

    if not nueva or len(nueva) < 6:
        return jsonify({"ok": False, "error": "Contraseña inválida"}), 400

    hash_pw = generate_password_hash(nueva)

    conn = obtener_conexion()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET password = %s
        WHERE id = %s
    """, (hash_pw, uid))

    conn.commit()
    cursor.close()
    conn.close()

    registrar_evento(
        usuario_id=user["usuario_id"],
        accion="admin_reset_pass",
        detalles={"usuario": uid}
    )

    return jsonify({"ok": True, "mensaje": "Contraseña reseteada"})
