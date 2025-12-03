from flask import Blueprint, request, jsonify
from aplicacion.servicios.auth_service import AuthService
from aplicacion.seguridad.sesiones import crear_sesion, cerrar_sesion, esta_autenticado, usuario_actual, rol_actual


auth_bp = Blueprint("auth_bp", __name__, url_prefix="/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    datos = request.json

    email = datos.get("email")
    password = datos.get("password")

    resultado = AuthService.registrar(email, password)

    return jsonify(resultado)


@auth_bp.route("/login", methods=["POST"])
def login():
    datos = request.json

    email = datos.get("email")
    password = datos.get("password")

    resultado = AuthService.login(email, password)

    if not resultado["ok"]:
        return jsonify(resultado), 400

    usuario = resultado["usuario"]

    crear_sesion(
        usuario_id = usuario["id"],
        rol = usuario["rol"],
        email = usuario["email"]
    )

    return jsonify({
        "ok": True,
        "mensaje": "Inicio de sesión exitoso",
        "usuario_id": usuario["id"],
        "email": usuario["email"],
        "rol": usuario["rol"]
    })


@auth_bp.route("/logout", methods=["POST"])
def logout():
    cerrar_sesion()
    return jsonify({"ok": True, "mensaje": "Sesión cerrada"})


@auth_bp.route("/me", methods=["GET"])
def auth_me():

    if not esta_autenticado():
        return jsonify({"autenticado": False})

    user = usuario_actual()

    return jsonify({
        "autenticado": True,
        "usuario_id": user.get("usuario_id"),
        "email": user.get("email"),
        "rol": user.get("rol")
    })