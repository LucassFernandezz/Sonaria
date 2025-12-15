from flask import Blueprint, jsonify, request
from aplicacion.seguridad.sesiones import esta_autenticado, usuario_actual
from persistencia.conexion import obtener_conexion
from aplicacion.servicios.logger import registrar_evento

auditoria_bp = Blueprint("auditoria_bp", __name__, url_prefix="/admin/auditoria")


@auditoria_bp.get("/")
def listar_auditoria():

    # -------------------------------------------------------
    # Caso 1: NO autenticado → 401 + AUDITAR intento
    # -------------------------------------------------------
    if not esta_autenticado():

        registrar_evento(
            usuario_id=None,
            accion="acceso_denegado",
            detalles={
                "motivo": "usuario no autenticado",
                "ruta": "/admin/auditoria"
            },
            criticidad="alta"
        )

        return jsonify({"error": "No autorizado"}), 401

    user = usuario_actual()

    # -------------------------------------------------------
    # Caso 2: Autenticado pero NO admin → 403 + AUDITAR intento
    # -------------------------------------------------------
    if user["rol"] != "admin":

        registrar_evento(
            usuario_id=user["usuario_id"],
            accion="acceso_denegado",
            detalles={
                "motivo": "rol no admin",
                "ruta": "/admin/auditoria"
            },
            criticidad="alta"
        )

        return jsonify({"error": "Solo admin"}), 403

    # -------------------------------------------------------
    # Caso 3: ADMIN → acceso permitido y auditado
    # -------------------------------------------------------
    registrar_evento(
        usuario_id=user["usuario_id"],
        accion="ver_auditoria",
        detalles={"ruta": "/admin/auditoria"},
        criticidad="media"
    )

    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
                SELECT 
                   a.id, 
                   a.accion, 
                   a.detalles, 
                   a.fecha, 
                   a.ip,
                   a.criticidad,
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

