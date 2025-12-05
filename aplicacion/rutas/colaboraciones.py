from flask import Blueprint, jsonify
from aplicacion.seguridad.sesiones import esta_autenticado, usuario_actual
from persistencia.conexion import obtener_conexion

colaboraciones_bp = Blueprint("colaboraciones_bp", __name__, url_prefix="/colaboraciones")


# ==========================================================
# 1) Obtener solicitudes de un proyecto (solo dueño)
# ==========================================================
@colaboraciones_bp.route("/proyecto/<int:proyecto_id>", methods=["GET"])
def obtener_solicitudes(proyecto_id):

    if not esta_autenticado():
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()

    conn = obtener_conexion()
    with conn.cursor(dictionary=True) as cursor:

        # Verificar que el usuario sea dueño del proyecto
        cursor.execute("""
            SELECT usuario_id
            FROM proyectos_audio
            WHERE id = %s
        """, (proyecto_id,))
        proyecto = cursor.fetchone()

        if not proyecto:
            return jsonify({"ok": False, "error": "Proyecto no existe"}), 404

        if proyecto["usuario_id"] != user["usuario_id"]:
            return jsonify({"ok": False, "error": "No autorizado"}), 403

        # Obtener solicitudes
        cursor.execute("""
            SELECT 
                c.id,
                c.estado,
                u.email,
                pa.nombre_artistico
            FROM colaboraciones c
            JOIN usuarios u ON u.id = c.usuario_colaborador_id
            LEFT JOIN perfiles_artisticos pa ON pa.usuario_id = u.id
            WHERE c.proyecto_id = %s
            ORDER BY c.fecha DESC
        """, (proyecto_id,))

        solicitudes = cursor.fetchall()

    conn.close()

    return jsonify({"ok": True, "solicitudes": solicitudes})
    

# ==========================================================
# 2) Aceptar solicitud
# ==========================================================
@colaboraciones_bp.route("/aceptar/<int:colab_id>", methods=["POST"])
def aceptar_solicitud(colab_id):

    if not esta_autenticado():
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()

    conn = obtener_conexion()
    with conn.cursor(dictionary=True) as cursor:

        # Verificar que la solicitud exista y que el usuario sea dueño del proyecto
        cursor.execute("""
            SELECT c.proyecto_id, p.usuario_id
            FROM colaboraciones c
            JOIN proyectos_audio p ON p.id = c.proyecto_id
            WHERE c.id = %s
        """, (colab_id,))
        fila = cursor.fetchone()

        if not fila:
            return jsonify({"ok": False, "error": "Solicitud no encontrada"}), 404

        if fila["usuario_id"] != user["usuario_id"]:
            return jsonify({"ok": False, "error": "No autorizado"}), 403

        # Actualizar estado
        cursor.execute("""
            UPDATE colaboraciones
            SET estado = 'aceptada'
            WHERE id = %s
        """, (colab_id,))

        conn.commit()

    conn.close()

    return jsonify({"ok": True, "mensaje": "Solicitud aceptada"})


# ==========================================================
# 3) Rechazar solicitud
# ==========================================================
@colaboraciones_bp.route("/rechazar/<int:colab_id>", methods=["POST"])
def rechazar_solicitud(colab_id):

    if not esta_autenticado():
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()

    conn = obtener_conexion()
    with conn.cursor(dictionary=True) as cursor:

        cursor.execute("""
            SELECT c.proyecto_id, p.usuario_id
            FROM colaboraciones c
            JOIN proyectos_audio p ON p.id = c.proyecto_id
            WHERE c.id = %s
        """, (colab_id,))
        fila = cursor.fetchone()

        if not fila:
            return jsonify({"ok": False, "error": "Solicitud no encontrada"}), 404

        if fila["usuario_id"] != user["usuario_id"]:
            return jsonify({"ok": False, "error": "No autorizado"}), 403

        cursor.execute("""
            UPDATE colaboraciones
            SET estado = 'rechazada'
            WHERE id = %s
        """, (colab_id,))

        conn.commit()

    conn.close()

    return jsonify({"ok": True, "mensaje": "Solicitud rechazada"})
