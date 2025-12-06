from flask import Blueprint, request, jsonify, current_app
from aplicacion.seguridad.sesiones import esta_autenticado, usuario_actual
from persistencia.conexion import obtener_conexion
from werkzeug.utils import secure_filename
import os
import time

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

        # Obtener solicitudes (AQUÍ AÑADIMOS colaboracion_id = c.id)
        cursor.execute("""
            SELECT 
                c.id AS colaboracion_id,
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

        # Verificar que la solicitud existe y pertenece al dueño
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

        proyecto_id = fila["proyecto_id"]

        # 1) Aceptar esta solicitud
        cursor.execute("""
            UPDATE colaboraciones
            SET estado = 'aceptada'
            WHERE id = %s
        """, (colab_id,))

        # 2) Rechazar todas las demás
        cursor.execute("""
            UPDATE colaboraciones
            SET estado = 'rechazada'
            WHERE proyecto_id = %s AND id != %s
        """, (proyecto_id, colab_id))

        conn.commit()

    conn.close()

    return jsonify({"ok": True, "mensaje": "Solicitud aceptada", "colaboracion_id": colab_id})


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


# ==========================================================
# 4) Obtener detalle completo de la colaboración
# ==========================================================
@colaboraciones_bp.route("/detalle/<int:colab_id>", methods=["GET"])
def obtener_detalle_colaboracion(colab_id):

    if not esta_autenticado():
        return jsonify({"ok": False, "error": "No autenticado"}), 401
    
    user = usuario_actual()

    conn = obtener_conexion()
    with conn.cursor(dictionary=True) as cursor:

        # 1) Obtener datos principales
        cursor.execute("""
            SELECT 
                c.id,
                c.estado,
                p.id AS proyecto_id,
                p.titulo,
                p.archivo_audio AS audio_original,
                p.usuario_id AS dueno_id,
                u1.email AS dueno_email,
                pa1.nombre_artistico AS dueno_artistico,

                u2.id AS colaborador_id,
                u2.email AS colaborador_email,
                pa2.nombre_artistico AS colaborador_artistico
            FROM colaboraciones c
            JOIN proyectos_audio p ON p.id = c.proyecto_id
            JOIN usuarios u1 ON u1.id = p.usuario_id
            LEFT JOIN perfiles_artisticos pa1 ON pa1.usuario_id = u1.id
            JOIN usuarios u2 ON u2.id = c.usuario_colaborador_id
            LEFT JOIN perfiles_artisticos pa2 ON pa2.usuario_id = u2.id
            WHERE c.id = %s AND c.estado = 'aceptada'
        """, (colab_id,))
        
        colab = cursor.fetchone()

        if not colab:
            return jsonify({"ok": False, "error": "Colaboración no encontrada"}), 404
        
        # 2) Validar que el usuario sea dueño o colaborador
        if user["usuario_id"] not in (colab["dueno_id"], colab["colaborador_id"]):
            return jsonify({"ok": False, "error": "No autorizado"}), 403

        # 3) Obtener lista de takes
        cursor.execute("""
            SELECT id, archivo_audio, comentarios, fecha_subida
            FROM takes
            WHERE colaboracion_id = %s
            ORDER BY fecha_subida ASC
        """, (colab_id,))
        
        takes = cursor.fetchall()

    conn.close()

    return jsonify({
        "ok": True,
        "colaboracion": colab,
        "takes": takes
    })



# ==========================================================
# 5) Subir audio (take)
# ==========================================================
@colaboraciones_bp.route("/subir_take/<int:colab_id>", methods=["POST"])
def subir_take(colab_id):

    if not esta_autenticado():
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()

    if "archivo" not in request.files:
        return jsonify({"ok": False, "error": "Archivo no enviado"}), 400

    archivo = request.files["archivo"]

    if archivo.filename == "":
        return jsonify({"ok": False, "error": "Nombre inválido"}), 400

    filename = secure_filename(str(int(time.time())) + "_" + archivo.filename)
    ruta = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    archivo.save(ruta)

    comentario = request.form.get("comentario", "")

    conn = obtener_conexion()
    with conn.cursor(dictionary=True) as cursor:

        # verificar que el usuario pertenece a esta colaboración
        cursor.execute("""
            SELECT proyecto_id, usuario_colaborador_id
            FROM colaboraciones
            WHERE id = %s AND estado = 'aceptada'
        """, (colab_id,))
        fila = cursor.fetchone()

        if not fila:
            return jsonify({"ok": False, "error": "Colaboración inexistente"}), 404

        # dueño o colaborador
        cursor.execute("""
            SELECT usuario_id 
            FROM proyectos_audio
            WHERE id = %s
        """, (fila["proyecto_id"],))
        
        dueno = cursor.fetchone()["usuario_id"]

        if user["usuario_id"] not in (dueno, fila["usuario_colaborador_id"]):
            return jsonify({"ok": False, "error": "No autorizado"}), 403

        # insertar take
        cursor.execute("""
            INSERT INTO takes (colaboracion_id, archivo_audio, comentarios)
            VALUES (%s, %s, %s)
        """, (colab_id, filename, comentario))

        conn.commit()

    conn.close()

    return jsonify({"ok": True, "mensaje": "Take subido correctamente"})


@colaboraciones_bp.route("/takes/<int:colab_id>", methods=["GET"])
def obtener_takes(colab_id):
    if not esta_autenticado():
        return jsonify({"ok": False}), 401

    conn = obtener_conexion()
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT id, archivo_audio, comentarios, fecha_subida
            FROM takes
            WHERE colaboracion_id = %s
            ORDER BY fecha_subida ASC
        """, (colab_id,))
        datos = cursor.fetchall()
    
    conn.close()
    return jsonify({"ok": True, "takes": datos})
