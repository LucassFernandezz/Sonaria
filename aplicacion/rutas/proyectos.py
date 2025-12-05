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
                    p.archivo_audio,
                    p.fecha_creacion,
                    u.id AS usuario_id,
                    u.email
                FROM proyectos_audio p
                JOIN usuarios u ON p.usuario_id = u.id
                ORDER BY p.fecha_creacion DESC
            """)

            audios = cursor.fetchall()

        conn.close()

        return jsonify({"ok": True, "audios": audios})

    except Exception as e:
        print("ERROR en /proyectos/all:", e)
        return jsonify({"ok": False, "error": "Error interno"}), 500
