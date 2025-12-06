from flask import Blueprint, jsonify
from aplicacion.seguridad.sesiones import esta_autenticado, usuario_actual
from persistencia.conexion import obtener_conexion

# Usamos tu prefix original
auditoria_bp = Blueprint("auditoria_bp", __name__, url_prefix="/admin/auditoria")


@auditoria_bp.get("/")
def listar_auditoria():
    # Solo usuarios logueados
    if not esta_autenticado():
        return jsonify({"error": "No autorizado"}), 401

    user = usuario_actual()

    # Solo administrador
    if user["rol"] != "admin":
        return jsonify({"error": "Solo admin"}), 403

    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT a.id, a.accion, a.detalles, a.fecha, a.ip,
               u.email AS usuario_email
        FROM auditoria a
        LEFT JOIN usuarios u ON a.usuario_id = u.id
        ORDER BY a.fecha DESC
        LIMIT 200
    """)

    datos = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"ok": True, "auditoria": datos}), 200
