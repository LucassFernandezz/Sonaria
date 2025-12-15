from flask import Blueprint, request, jsonify
from aplicacion.servicios.auth_service import AuthService
from aplicacion.seguridad.sesiones import crear_sesion, cerrar_sesion, esta_autenticado, usuario_actual, rol_actual
from aplicacion.seguridad.auditoria import registrar_evento # esto se añade para hacer las cosas de auditoria

auth_bp = Blueprint("auth_bp", __name__, url_prefix="/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    datos = request.json

    email = datos.get("email")
    password = datos.get("password")

    resultado = AuthService.registrar(email, password)

    # registrar evento si ok
    if resultado.get("ok"):
        registrar_evento(
            usuario_id=resultado["usuario"]["id"],
            accion="registro",
            detalles={"email": email},
            criticidad="media"
        )  # agrego para auditoria
    else:
        registrar_evento(
            usuario_id=None,
            accion="registro_fallido",
            detalles={"email": email, "motivo": resultado.get("error")},
            criticidad="alta"
        )  # agrego para auditoria

    return jsonify(resultado)


@auth_bp.route("/login", methods=["POST"])
def login():
    datos = request.json

    email = datos.get("email")
    password = datos.get("password")

    resultado = AuthService.login(email, password)

    if not resultado["ok"]:
        registrar_evento(
            usuario_id=None,
            accion="login_fallido",
            detalles={"email": email},
            criticidad ="alta"
        )  # agrego para auditoria
        return jsonify(resultado), 400

    usuario = resultado["usuario"]

    crear_sesion(
        usuario_id = usuario["id"],
        rol = usuario["rol"],
        email = usuario["email"]
    )

    registrar_evento(
        usuario_id=usuario["id"],
        accion="login_exitoso",
        detalles={"email": usuario["email"]},
        criticidad="media"
    )  # agrego para auditoria

    return jsonify({
        "ok": True,
        "mensaje": "Inicio de sesión exitoso",
        "usuario_id": usuario["id"],
        "email": usuario["email"],
        "rol": usuario["rol"]
    })


@auth_bp.route("/logout", methods=["POST"])
def logout():
    user = usuario_actual()

    if user:
        registrar_evento(
            usuario_id=user["usuario_id"],
            accion="logout",
            detalles={"email": user["email"]},
            criticidad="alta"
        )  # agrego para auditoria

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