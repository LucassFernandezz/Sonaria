from flask import Blueprint, request, jsonify
from aplicacion.seguridad.sesiones import esta_autenticado, usuario_actual
from aplicacion.servicios.perfil_services import PerfilService

perfiles_bp = Blueprint("perfiles_bp", __name__, url_prefix="/perfiles")

# =============================
# Obtener mi perfil
# =============================
@perfiles_bp.route("/me", methods=["GET"])
def obtener_mi_perfil():

    if not esta_autenticado():
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()
    perfil = PerfilService.obtener_o_crear(user["usuario_id"])

    return jsonify({"ok": True, "perfil": perfil})


# =============================
# Actualizar mi perfil
# =============================
@perfiles_bp.route("/me", methods=["PUT"])
def actualizar_mi_perfil():

    if not esta_autenticado():
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()
    datos = request.json

    PerfilService.actualizar(user["usuario_id"], datos)

    return jsonify({"ok": True, "mensaje": "Perfil actualizado"})