# aplicacion/rutas/admin_rectificaciones.py
from flask import Blueprint, request, jsonify
from aplicacion.seguridad.sesiones import esta_autenticado, usuario_actual
from aplicacion.seguridad.auditoria import registrar_evento
from persistencia.conexion import obtener_conexion
from aplicacion.seguridad.cifrado import cifrar

admin_rectificaciones_bp = Blueprint("admin_rectificaciones_bp", __name__, url_prefix="/admin/rectificaciones")

# ==========================================================
# VALIDAR ADMIN
# ==========================================================
def require_admin():
    if not esta_autenticado():
        return None, jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()
    if user["rol"] != "admin":
        return None, jsonify({"ok": False, "error": "No autorizado"}), 403

    return user, None, None


# ==========================================================
# 1) Listar solicitudes de rectificación
# ==========================================================
@admin_rectificaciones_bp.get("/")
def listar_rectificaciones():

    user, resp, status = require_admin()
    if resp:
        return resp, status

    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT r.id, r.usuario_id, u.email, r.campo,
               r.valor_anterior, r.valor_nuevo,
               r.estado, r.fecha_solicitud
        FROM rectificaciones r
        JOIN usuarios u ON u.id = r.usuario_id
        ORDER BY r.fecha_solicitud DESC
    """)

    datos = cursor.fetchall()

    cursor.close()
    conn.close()

    # auditoría
    registrar_evento(
        usuario_id=user["usuario_id"],
        accion="admin_listar_rectificaciones",
        detalles={"total": len(datos)}
    )

    return jsonify({"ok": True, "rectificaciones": datos}), 200


# ==========================================================
# 2) Aprobar una rectificación
# ==========================================================
@admin_rectificaciones_bp.post("/aprobar/<int:rect_id>")
def aprobar_rectificacion(rect_id):

    user, resp, status = require_admin()
    if resp:
        return resp, status

    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)

    # obtener rectificación
    cursor.execute("""
        SELECT *
        FROM rectificaciones
        WHERE id = %s
    """, (rect_id,))
    rect = cursor.fetchone()

    if not rect:
        cursor.close()
        conn.close()
        return jsonify({"ok": False, "error": "Rectificación no encontrada"}), 404


    # ------------------------------------------------------
    # Si el campo es nombre_artistico → cifrar antes
    # ------------------------------------------------------
    if rect["campo"] == "nombre_artistico":
        valor_final = cifrar(rect["valor_nuevo"])
    else:
        valor_final = rect["valor_nuevo"]

    # aplicar cambio
    cursor.execute(f"""
        UPDATE perfiles_artisticos
        SET {rect['campo']} = %s
        WHERE usuario_id = %s
    """, (valor_final, rect["usuario_id"]))

    # marcar rectificación como aprobada
    cursor.execute("""
        UPDATE rectificaciones
        SET estado = 'aprobada'
        WHERE id = %s
    """, (rect_id,))

    conn.commit()
    cursor.close()
    conn.close()

    registrar_evento(
        usuario_id=user["usuario_id"],
        accion="admin_aprobar_rectificacion",
        detalles={"rect_id": rect_id}
    )

    return jsonify({"ok": True, "mensaje": "Rectificación aprobada"}), 200


# ==========================================================
# 3) Rechazar rectificación
# ==========================================================
@admin_rectificaciones_bp.post("/rechazar/<int:rect_id>")
def rechazar_rectificacion(rect_id):

    user, resp, status = require_admin()
    if resp:
        return resp, status

    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id FROM rectificaciones WHERE id = %s
    """, (rect_id,))
    existe = cursor.fetchone()

    if not existe:
        cursor.close()
        conn.close()
        return jsonify({"ok": False, "error": "Rectificación no encontrada"}), 404

    cursor.execute("""
        UPDATE rectificaciones
        SET estado = 'rechazada'
        WHERE id = %s
    """, (rect_id,))

    conn.commit()
    cursor.close()
    conn.close()

    registrar_evento(
        usuario_id=user["usuario_id"],
        accion="admin_rechazar_rectificacion",
        detalles={"rect_id": rect_id}
    )

    return jsonify({"ok": True, "mensaje": "Rectificación rechazada"}), 200
