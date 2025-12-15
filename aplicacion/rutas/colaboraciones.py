from flask import Blueprint, request, jsonify, current_app
from aplicacion.seguridad.sesiones import esta_autenticado, usuario_actual
from persistencia.conexion import obtener_conexion
from werkzeug.utils import secure_filename
from aplicacion.seguridad.auditoria import registrar_evento
from aplicacion.seguridad.cifrado import cifrar, descifrar
from aplicacion.sockets.tcp_client import enviar_notificacion_tcp
import os
import time

colaboraciones_bp = Blueprint("colaboraciones_bp", __name__, url_prefix="/colaboraciones")


# ==========================================================
# 1) Obtener solicitudes de un proyecto (solo dueño)
# ==========================================================
@colaboraciones_bp.route("/proyecto/<int:proyecto_id>", methods=["GET"])
def obtener_solicitudes(proyecto_id):

    if not esta_autenticado():
        registrar_evento(None, "ver_solicitudes_denegado",
                         {"proyecto_id": proyecto_id},
                         criticidad="alta")
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()
    uid = user["usuario_id"]

    conn = obtener_conexion()
    with conn.cursor(dictionary=True) as cursor:

        cursor.execute("SELECT usuario_id FROM proyectos_audio WHERE id = %s", (proyecto_id,))
        proyecto = cursor.fetchone()

        if not proyecto:
            registrar_evento(uid, "ver_solicitudes_error",
                             {"proyecto_id": proyecto_id, "motivo": "proyecto_no_existe"},
                             criticidad="alta")
            return jsonify({"ok": False, "error": "Proyecto no existe"}), 404

        if proyecto["usuario_id"] != uid:
            registrar_evento(uid, "ver_solicitudes_denegado",
                             {"proyecto_id": proyecto_id},
                             criticidad="alta")
            return jsonify({"ok": False, "error": "No autorizado"}), 403

        cursor.execute("""
            SELECT c.id AS colaboracion_id, c.estado, u.email, pa.nombre_artistico
            FROM colaboraciones c
            JOIN usuarios u ON u.id = c.usuario_colaborador_id
            LEFT JOIN perfiles_artisticos pa ON pa.usuario_id = u.id
            WHERE c.proyecto_id = %s
            ORDER BY c.fecha DESC
        """, (proyecto_id,))

        solicitudes = cursor.fetchall()

        for s in solicitudes:
            if s["nombre_artistico"]:
                s["nombre_artistico"] = descifrar(s["nombre_artistico"])

    conn.close()

    registrar_evento(uid, "ver_solicitudes",
                     {"proyecto_id": proyecto_id},
                     criticidad="baja")

    return jsonify({"ok": True, "solicitudes": solicitudes})


# ==========================================================
# 2) Aceptar solicitud
# ==========================================================
@colaboraciones_bp.route("/aceptar/<int:colab_id>", methods=["POST"])
def aceptar_solicitud(colab_id):

    if not esta_autenticado():
        registrar_evento(None, "aceptar_colab_denegado",
                         {"colab_id": colab_id},
                         criticidad="alta")
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()
    uid = user["usuario_id"]

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
            registrar_evento(uid, "aceptar_colab_error",
                             {"colab_id": colab_id, "motivo": "no_existe"},
                             criticidad="alta")
            return jsonify({"ok": False, "error": "Solicitud no encontrada"}), 404

        if fila["usuario_id"] != uid:
            registrar_evento(uid, "aceptar_colab_denegado",
                             {"colab_id": colab_id},
                             criticidad="alta")
            return jsonify({"ok": False, "error": "No autorizado"}), 403

        cursor.execute("UPDATE colaboraciones SET estado = 'aceptada' WHERE id = %s", (colab_id,))
        cursor.execute("""
            UPDATE colaboraciones
            SET estado = 'rechazada'
            WHERE proyecto_id = %s AND id != %s
        """, (fila["proyecto_id"], colab_id))

        conn.commit()

    conn.close()

    enviar_notificacion_tcp(f"Solicitud aceptada | colab_id={colab_id} | usuario={uid}")

    registrar_evento(uid, "aceptar_colab",
                     {"colab_id": colab_id},
                     criticidad="media")

    return jsonify({"ok": True, "mensaje": "Solicitud aceptada"})


# ==========================================================
# 3) Rechazar solicitud
# ==========================================================
@colaboraciones_bp.route("/rechazar/<int:colab_id>", methods=["POST"])
def rechazar_solicitud(colab_id):

    if not esta_autenticado():
        registrar_evento(None, "rechazar_colab_denegado",
                         {"colab_id": colab_id},
                         criticidad="alta")
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()
    uid = user["usuario_id"]

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
            registrar_evento(uid, "rechazar_colab_error",
                             {"colab_id": colab_id, "motivo": "no_existe"},
                             criticidad="alta")
            return jsonify({"ok": False, "error": "Solicitud no encontrada"}), 404

        if fila["usuario_id"] != uid:
            registrar_evento(uid, "rechazar_colab_denegado",
                             {"colab_id": colab_id},
                             criticidad="alta")
            return jsonify({"ok": False, "error": "No autorizado"}), 403

        cursor.execute("UPDATE colaboraciones SET estado = 'rechazada' WHERE id = %s", (colab_id,))
        conn.commit()

    conn.close()

    enviar_notificacion_tcp(f"Solicitud rechazada | colab_id={colab_id} | usuario={uid}")

    registrar_evento(uid, "rechazar_colab",
                     {"colab_id": colab_id},
                     criticidad="media")

    return jsonify({"ok": True, "mensaje": "Solicitud rechazada"})


# ==========================================================
# 4) Detalle colaboración
# ==========================================================
@colaboraciones_bp.route("/detalle/<int:colab_id>", methods=["GET"])
def obtener_detalle_colaboracion(colab_id):

    if not esta_autenticado():
        registrar_evento(
            None,
            "detalle_colab_denegado",
            {"colab_id": colab_id},
            criticidad="media"
        )
        return jsonify({"ok": False, "error": "No autenticado"}), 401
    
    user = usuario_actual()
    uid = user["usuario_id"]

    conn = obtener_conexion()
    with conn.cursor(dictionary=True) as cursor:

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

        if colab:
            if colab["dueno_artistico"]:
                colab["dueno_artistico"] = descifrar(colab["dueno_artistico"])
            if colab["colaborador_artistico"]:
                colab["colaborador_artistico"] = descifrar(colab["colaborador_artistico"])

        if not colab:
            registrar_evento(
                uid,
                "detalle_colab_error",
                {"colab_id": colab_id, "motivo": "no_existe"},
                criticidad="media"
            )
            return jsonify({"ok": False, "error": "Colaboración no encontrada"}), 404
        
        if uid not in (colab["dueno_id"], colab["colaborador_id"]):
            registrar_evento(
                uid,
                "detalle_colab_denegado",
                {"colab_id": colab_id},
                criticidad="alta"
            )
            return jsonify({"ok": False, "error": "No autorizado"}), 403

        cursor.execute("""
            SELECT id, archivo_audio, comentarios, fecha_subida
            FROM takes
            WHERE colaboracion_id = %s
            ORDER BY fecha_subida ASC
        """, (colab_id,))
        
        takes = cursor.fetchall()

    conn.close()

    registrar_evento(
        uid,
        "detalle_colab",
        {"colab_id": colab_id},
        criticidad="baja"
    )

    return jsonify({"ok": True, "colaboracion": colab, "takes": takes})


# ==========================================================
# 5) Subir take
# ==========================================================
@colaboraciones_bp.route("/subir_take/<int:colab_id>", methods=["POST"])
def subir_take(colab_id):

    if not esta_autenticado():
        registrar_evento(
            None,
            "subir_take_denegado",
            {"colab_id": colab_id},
            criticidad="alta"
        )
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()
    uid = user["usuario_id"]

    if "archivo" not in request.files:
        registrar_evento(
            uid,
            "subir_take_error",
            {"colab_id": colab_id, "motivo": "archivo_no_enviado"},
            criticidad="media"
        )
        return jsonify({"ok": False, "error": "Archivo no enviado"}), 400

    archivo = request.files["archivo"]

    if archivo.filename == "":
        registrar_evento(
            uid,
            "subir_take_error",
            {"colab_id": colab_id, "motivo": "nombre_vacio"},
            criticidad="media"
        )
        return jsonify({"ok": False, "error": "Nombre inválido"}), 400

    filename = secure_filename(str(int(time.time())) + "_" + archivo.filename)
    ruta = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    archivo.save(ruta)

    comentario = request.form.get("comentario", "")

    conn = obtener_conexion()
    with conn.cursor(dictionary=True) as cursor:

        cursor.execute("""
            SELECT proyecto_id, usuario_colaborador_id, estado
            FROM colaboraciones
            WHERE id = %s
        """, (colab_id,))
        fila = cursor.fetchone()

        if not fila:
            registrar_evento(
                uid,
                "subir_take_error",
                {"colab_id": colab_id, "motivo": "colab_no_existe"},
                criticidad="media"
            )
            return jsonify({"ok": False, "error": "Colaboración inexistente"}), 404

        if fila["estado"] != "aceptada":
            registrar_evento(
                uid,
                "subir_take_error",
                {"colab_id": colab_id, "motivo": "colab_no_aceptada"},
                criticidad="media"
            )
            return jsonify({"ok": False, "error": "La colaboración no está aceptada"}), 403

        cursor.execute(
            "SELECT usuario_id FROM proyectos_audio WHERE id = %s",
            (fila["proyecto_id"],)
        )
        dueno = cursor.fetchone()["usuario_id"]

        if uid not in (dueno, fila["usuario_colaborador_id"]):
            registrar_evento(
                uid,
                "subir_take_denegado",
                {"colab_id": colab_id},
                criticidad="alta"
            )
            return jsonify({"ok": False, "error": "No autorizado"}), 403

        cursor.execute("""
            INSERT INTO takes (colaboracion_id, archivo_audio, comentarios)
            VALUES (%s, %s, %s)
        """, (colab_id, filename, comentario))

        conn.commit()

    conn.close()

    registrar_evento(
        uid,
        "subir_take",
        {"colab_id": colab_id, "archivo": filename},
        criticidad="media"
    )
    enviar_notificacion_tcp(f"Nuevo take subido | colab_id={colab_id} | usuario={uid}")

    return jsonify({"ok": True, "mensaje": "Take subido correctamente"})


# ==========================================================
# 6) Obtener solo los takes
# ==========================================================
@colaboraciones_bp.route("/takes/<int:colab_id>", methods=["GET"])
def obtener_takes(colab_id):

    if not esta_autenticado():
        registrar_evento(
            None,
            "ver_takes_denegado",
            {"colab_id": colab_id},
            criticidad="media"
        )
        return jsonify({"ok": False}), 401

    user = usuario_actual()
    uid = user["usuario_id"]

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

    registrar_evento(
        uid,
        "ver_takes",
        {"colab_id": colab_id},
        criticidad="baja"
    )

    return jsonify({"ok": True, "takes": datos})


# ==========================================================
# 7) Publicar resultado final (solo dueño)
# ==========================================================
@colaboraciones_bp.route("/publicar_resultado/<int:colab_id>", methods=["POST"])
def publicar_resultado(colab_id):

    if not esta_autenticado():
        registrar_evento(
            None,
            "publicar_resultado_denegado",
            {"colab_id": colab_id},
            criticidad="alta"
        )
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()
    uid = user["usuario_id"]

    if "archivo" not in request.files:
        registrar_evento(
            uid,
            "publicar_resultado_error",
            {"colab_id": colab_id, "motivo": "archivo_no_enviado"},
            criticidad="media"
        )
        return jsonify({"ok": False, "error": "Archivo no enviado"}), 400

    archivo = request.files["archivo"]

    if archivo.filename == "":
        registrar_evento(
            uid,
            "publicar_resultado_error",
            {"colab_id": colab_id, "motivo": "nombre_vacio"},
            criticidad="media"
        )
        return jsonify({"ok": False, "error": "Nombre inválido"}), 400

    filename = secure_filename(str(int(time.time())) + "_" + archivo.filename)
    ruta = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    archivo.save(ruta)

    conn = obtener_conexion()
    with conn.cursor(dictionary=True) as cursor:

        cursor.execute("""
            SELECT p.usuario_id
            FROM colaboraciones c
            JOIN proyectos_audio p ON p.id = c.proyecto_id
            WHERE c.id = %s AND c.estado = 'aceptada'
        """, (colab_id,))
        fila = cursor.fetchone()

        if not fila:
            registrar_evento(
                uid,
                "publicar_resultado_error",
                {"colab_id": colab_id, "motivo": "colab_no_existe"},
                criticidad="media"
            )
            return jsonify({"ok": False, "error": "Colaboración no encontrada"}), 404

        if fila["usuario_id"] != uid:
            registrar_evento(
                uid,
                "publicar_resultado_denegado",
                {"colab_id": colab_id},
                criticidad="alta"
            )
            return jsonify({"ok": False, "error": "No autorizado"}), 403

        cursor.execute(
            "UPDATE colaboraciones SET resultado_final = %s WHERE id = %s",
            (filename, colab_id)
        )
        conn.commit()

    conn.close()

    registrar_evento(
        uid,
        "publicar_resultado",
        {"colab_id": colab_id, "archivo": filename},
        criticidad="alta"
    )

    return jsonify({"ok": True, "mensaje": "Resultado final publicado"})


# ==========================================================
# 8) Obtener resultado final
# ==========================================================
@colaboraciones_bp.route("/resultado_final/<int:colab_id>", methods=["GET"])
def obtener_resultado_final(colab_id):

    if not esta_autenticado():
        registrar_evento(
            None,
            "ver_resultado_final_denegado",
            {"colab_id": colab_id},
            criticidad="media"
        )
        return jsonify({"ok": False}), 401

    user = usuario_actual()
    uid = user["usuario_id"]

    conn = obtener_conexion()
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(
            "SELECT resultado_final FROM colaboraciones WHERE id = %s",
            (colab_id,)
        )
        fila = cursor.fetchone()

    conn.close()

    registrar_evento(
        uid,
        "ver_resultado_final",
        {"colab_id": colab_id},
        criticidad="baja"
    )

    if not fila or not fila["resultado_final"]:
        return jsonify({"ok": False, "resultado": None})

    return jsonify({"ok": True, "resultado": fila["resultado_final"]})
