from flask import Blueprint, request, jsonify
import os
from werkzeug.utils import secure_filename

from aplicacion.seguridad.sesiones import esta_autenticado, usuario_actual
from aplicacion.servicios.proyecto_services import ProyectoService
from aplicacion.servicios.logger import registrar_evento    # 🟢 AUDITORÍA
from persistencia.conexion import obtener_conexion

proyectos_bp = Blueprint("proyectos_bp", __name__, url_prefix="/proyectos")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"mp3", "wav", "ogg", "m4a"}


def es_extension_valida(nombre):
    return "." in nombre and nombre.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# =====================================================
# Crear un nuevo proyecto (SUBIDA DE AUDIO)
# =====================================================
@proyectos_bp.route("", methods=["POST"])
def crear_proyecto():

    if not esta_autenticado():
        registrar_evento(
            usuario_id=None,
            accion="crear_proyecto_denegado",
            detalles={"motivo": "no_autenticado"},
            ip=request.remote_addr
        ) #para auditoria
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()

    titulo = request.form.get("titulo")
    descripcion = request.form.get("descripcion")
    genero = request.form.get("genero")
    necesita = request.form.get("necesita")
    archivo = request.files.get("archivo_audio")

    if not archivo:
        registrar_evento(
            usuario_id=user["usuario_id"],
            accion="crear_proyecto_fallido",
            detalles={"motivo": "sin_archivo"},
            ip=request.remote_addr
        ) #para auditoria
        return jsonify({"ok": False, "error": "No enviaste un archivo"}), 400

    if not es_extension_valida(archivo.filename):
        registrar_evento(
            usuario_id=user["usuario_id"],
            accion="crear_proyecto_fallido",
            detalles={"motivo": "extension_invalida", "archivo": archivo.filename},
            ip=request.remote_addr
        ) #para auditoria
        return jsonify({"ok": False, "error": "Formato no permitido"}), 400

    filename = secure_filename(archivo.filename)
    ruta_archivo = os.path.join(UPLOAD_FOLDER, filename)
    archivo.save(ruta_archivo)

    proyecto_id = ProyectoService.crear(
        usuario_id=user["usuario_id"],
        titulo=titulo,
        descripcion=descripcion,
        genero=genero,
        necesita=necesita,
        archivo_audio=filename
    )

    registrar_evento(
        usuario_id=user["usuario_id"],
        accion="crear_proyecto",
        detalles={
            "proyecto_id": proyecto_id,
            "titulo": titulo,
            "archivo": filename
        },
        ip=request.remote_addr
    ) #oara auditoria

    return jsonify({"ok": True, "proyecto_id": proyecto_id})


# =====================================================
# Obtener todos los audios para mostrar en home.html
# =====================================================
@proyectos_bp.route("/all", methods=["GET"])
def obtener_audios():

    try:
        conn = obtener_conexion()
        with conn.cursor(dictionary=True) as cursor:

            cursor.execute("""
                SELECT 
                    p.id,
                    p.titulo,
                    p.descripcion,
                    p.genero,
                    p.necesita,
                    p.archivo_audio,
                    p.fecha_creacion,
                    u.id AS usuario_id,
                    u.email,
                    pa.nombre_artistico
                FROM proyectos_audio p
                JOIN usuarios u ON p.usuario_id = u.id
                LEFT JOIN perfiles_artisticos pa ON pa.usuario_id = u.id
                ORDER BY p.fecha_creacion DESC
            """)

            audios = cursor.fetchall()

        conn.close()

        return jsonify({"ok": True, "audios": audios})

    except Exception as e:
        print("ERROR en /proyectos/all:", e)
        return jsonify({"ok": False, "error": "Error interno"}), 500

# =====================================================
# Obtener datos de UN proyecto por ID (proyecto.html)
# =====================================================
@proyectos_bp.route("/<int:proyecto_id>", methods=["GET"])
def obtener_proyecto(proyecto_id):
    try:
        user = usuario_actual() if esta_autenticado() else None
        user_id = user["usuario_id"] if user else None

        registrar_evento(
            usuario_id=user_id,
            accion="ver_proyecto",
            detalles={"proyecto_id": proyecto_id},
            ip=request.remote_addr
        ) # para auditoria

        conn = obtener_conexion()
        with conn.cursor(dictionary=True) as cursor:

            # 1) Obtener datos del proyecto
            cursor.execute("""
                SELECT 
                    p.id,
                    p.titulo,
                    p.descripcion,
                    p.genero,
                    p.necesita,
                    p.archivo_audio,
                    p.estado,
                    p.fecha_creacion,
                    u.id AS usuario_id,
                    u.email,
                    pa.nombre_artistico
                FROM proyectos_audio p
                JOIN usuarios u ON p.usuario_id = u.id
                LEFT JOIN perfiles_artisticos pa ON pa.usuario_id = u.id
                WHERE p.id = %s
            """, (proyecto_id,))

            proyecto = cursor.fetchone()

            if not proyecto:
                return jsonify({"ok": False, "error": "Proyecto no encontrado"}), 404

            # 2) Saber si el usuario logueado es dueño
            proyecto["es_duenio"] = (user_id == proyecto["usuario_id"])

            # 3) Buscar si el usuario ya solicitó colaborar
            proyecto["solicitud_estado"] = None
            proyecto["colaboracion_id"] = None

            if user_id:
                cursor.execute("""
                    SELECT id, estado
                    FROM colaboraciones
                    WHERE proyecto_id = %s AND usuario_colaborador_id = %s
                """, (proyecto_id, user_id))

                sol = cursor.fetchone()
                if sol:
                    proyecto["solicitud_estado"] = sol["estado"]
                    proyecto["colaboracion_id"] = sol["id"]

            # 4) Nombre del autor: artístico > email
            proyecto["autor_nombre"] = (
                proyecto["nombre_artistico"] 
                if proyecto["nombre_artistico"] 
                else proyecto["email"]
            )

        conn.close()

        return jsonify({"ok": True, "proyecto": proyecto})

    except Exception as e:
        print("ERROR en /proyectos/<id>:", e)
        return jsonify({"ok": False, "error": "Error interno"}), 500

# =====================================================
# Enviar solicitud de colaboración
# =====================================================
@proyectos_bp.route("/<int:proyecto_id>/solicitar", methods=["POST"])
def solicitar_colaboracion(proyecto_id):

    if not esta_autenticado():
        registrar_evento(
            usuario_id=None,
            accion="solicitar_colaboracion_denegado",
            detalles={"proyecto_id": proyecto_id, "motivo": "no_autenticado"},
            ip=request.remote_addr
        ) #para auditoria
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()
    user_id = user["usuario_id"]

    conn = obtener_conexion()
    with conn.cursor(dictionary=True) as cursor:

        # 1) Verificar que el proyecto exista
        cursor.execute("SELECT usuario_id FROM proyectos_audio WHERE id = %s", (proyecto_id,))
        proyecto = cursor.fetchone()

        if not proyecto:
            registrar_evento(
                usuario_id=user_id,
                accion="solicitar_colaboracion_fallido",
                detalles={"motivo": "proyecto_no_existe", "proyecto_id": proyecto_id},
                ip=request.remote_addr
            ) # auditoria
            conn.close()
            return jsonify({"ok": False, "error": "Proyecto no encontrado"}), 404

        # 2) No puedes solicitar tu propio proyecto
        if proyecto["usuario_id"] == user_id:
            registrar_evento(
                usuario_id=user_id,
                accion="solicitar_colaboracion_fallido",
                detalles={"motivo": "propio_proyecto", "proyecto_id": proyecto_id},
                ip=request.remote_addr
            ) #auditoria
            conn.close()
            return jsonify({"ok": False, "error": "No puedes colaborar en tu propio proyecto"}), 400

        # 3) Verificar si ya existe una solicitud
        cursor.execute("""
            SELECT id, estado FROM colaboraciones
            WHERE proyecto_id = %s AND usuario_colaborador_id = %s
        """, (proyecto_id, user_id))

        existente = cursor.fetchone()

        if existente:
            registrar_evento(
                usuario_id=user_id,
                accion="solicitar_colaboracion_fallido",
                detalles={"motivo": "ya_existente", "proyecto_id": proyecto_id},
                ip=request.remote_addr
            ) #auditoria
            conn.close()
            return jsonify({"ok": False, "error": "Ya enviaste una solicitud"}), 400

        # 4) Crear solicitud
        cursor.execute("""
            INSERT INTO colaboraciones (proyecto_id, usuario_colaborador_id, estado)
            VALUES (%s, %s, 'pendiente')
        """, (proyecto_id, user_id))

        conn.commit()
        conn.close()

        registrar_evento(
            usuario_id=user_id,
            accion="solicitar_colaboracion",
            detalles={"proyecto_id": proyecto_id},
            ip=request.remote_addr
        ) #auditoria


        return jsonify({"ok": True, "mensaje": "Solicitud enviada"})

@proyectos_bp.route("/mios", methods=["GET"])
def proyectos_mios():
    if not esta_autenticado():
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()

    conn = obtener_conexion()
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT id, titulo, genero, estado
            FROM proyectos_audio
            WHERE usuario_id = %s
            ORDER BY fecha_creacion DESC
        """, (user["usuario_id"],))
        proyectos = cursor.fetchall()

    conn.close()

    return jsonify({"ok": True, "proyectos": proyectos})

# ==========================================================
# Proyectos donde el usuario es colaborador aceptado
# ==========================================================
@proyectos_bp.route("/colaborando", methods=["GET"])
def proyectos_colaborando():

    if not esta_autenticado():
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()
    uid = user["usuario_id"]

    conn = obtener_conexion()
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT 
                p.id,
                p.titulo,
                p.descripcion,
                p.necesita,
                p.archivo_audio,
                u.email AS dueno_email,
                pa.nombre_artistico AS dueno_nombre
            FROM colaboraciones c
            JOIN proyectos_audio p ON p.id = c.proyecto_id
            JOIN usuarios u ON u.id = p.usuario_id
            LEFT JOIN perfiles_artisticos pa ON pa.usuario_id = u.id
            WHERE c.usuario_colaborador_id = %s
              AND c.estado = 'aceptada'
            ORDER BY p.fecha_creacion DESC
        """, (uid,))

        proyectos = cursor.fetchall()

    conn.close()

    return jsonify({"ok": True, "proyectos": proyectos})
