from flask import Blueprint, request, jsonify
import os
from werkzeug.utils import secure_filename

from aplicacion.seguridad.sesiones import esta_autenticado, usuario_actual
from aplicacion.servicios.proyecto_services import ProyectoService
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
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()

    titulo = request.form.get("titulo")
    descripcion = request.form.get("descripcion")
    genero = request.form.get("genero")
    necesita = request.form.get("necesita")

    archivo = request.files.get("archivo_audio")

    if not archivo:
        return jsonify({"ok": False, "error": "No enviaste un archivo"}), 400

    if not es_extension_valida(archivo.filename):
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
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()
    user_id = user["usuario_id"]

    conn = obtener_conexion()
    with conn.cursor(dictionary=True) as cursor:

        # 1) Verificar que el proyecto exista
        cursor.execute("SELECT usuario_id FROM proyectos_audio WHERE id = %s", (proyecto_id,))
        proyecto = cursor.fetchone()

        if not proyecto:
            conn.close()
            return jsonify({"ok": False, "error": "Proyecto no encontrado"}), 404

        # 2) No puedes solicitar tu propio proyecto
        if proyecto["usuario_id"] == user_id:
            conn.close()
            return jsonify({"ok": False, "error": "No puedes colaborar en tu propio proyecto"}), 400

        # 3) Verificar si ya existe una solicitud
        cursor.execute("""
            SELECT id, estado FROM colaboraciones
            WHERE proyecto_id = %s AND usuario_colaborador_id = %s
        """, (proyecto_id, user_id))

        existente = cursor.fetchone()

        if existente:
            conn.close()
            return jsonify({"ok": False, "error": "Ya enviaste una solicitud"}), 400

        # 4) Crear solicitud
        cursor.execute("""
            INSERT INTO colaboraciones (proyecto_id, usuario_colaborador_id, estado)
            VALUES (%s, %s, 'pendiente')
        """, (proyecto_id, user_id))

        conn.commit()
        conn.close()

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
