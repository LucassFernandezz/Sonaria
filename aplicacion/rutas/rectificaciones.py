# aplicacion/rutas/rectificaciones.py
from flask import Blueprint, request, jsonify
from aplicacion.seguridad.sesiones import esta_autenticado, usuario_actual
from aplicacion.seguridad.auditoria import registrar_evento
from persistencia.conexion import obtener_conexion

rectificaciones_bp = Blueprint("rectificaciones_bp", __name__, url_prefix="/rectificaciones")


# ==========================================================
# 1) USUARIO: crear solicitud de rectificación
# ==========================================================
@rectificaciones_bp.post("/solicitar")
def solicitar_rectificacion():

    if not esta_autenticado():
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()
    uid = user["usuario_id"]

    data = request.json
    campo = data.get("campo")
    valor_nuevo = data.get("valor_nuevo")

    if not campo or not valor_nuevo:
        return jsonify({"ok": False, "error": "Faltan datos"}), 400

    # Validar campos permitidos
    campos_validos = ["nombre_artistico", "descripcion", "genero_principal", "habilidades"]

    if campo not in campos_validos:
        return jsonify({"ok": False, "error": "Campo no permitido"}), 400

    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)

    # Obtener valor anterior
    cursor.execute(f"""
        SELECT {campo}
        FROM perfiles_artisticos
        WHERE usuario_id = %s
    """, (uid,))

    fila = cursor.fetchone()

    if not fila:
        cursor.close()
        conn.close()
        return jsonify({"ok": False, "error": "No tenés perfil artístico creado"}), 404

    valor_anterior = fila[campo]

    # Insertar solicitud
    cursor.execute("""
        INSERT INTO rectificaciones (usuario_id, campo, valor_anterior, valor_nuevo)
        VALUES (%s, %s, %s, %s)
    """, (uid, campo, valor_anterior, valor_nuevo))

    conn.commit()
    cursor.close()
    conn.close()

    registrar_evento(
        usuario_id=uid,
        accion="usuario_solicita_rectificacion",
        detalles={"campo": campo, "valor_nuevo": valor_nuevo}
    )

    return jsonify({"ok": True, "mensaje": "Solicitud enviada"}) , 200



# ==========================================================
# 2) USUARIO: ver sus solicitudes enviadas
# ==========================================================
@rectificaciones_bp.get("/mias")
def rectificaciones_mias():

    if not esta_autenticado():
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    user = usuario_actual()
    uid = user["usuario_id"]

    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, campo, valor_anterior, valor_nuevo, estado, fecha_solicitud
        FROM rectificaciones
        WHERE usuario_id = %s
        ORDER BY fecha_solicitud DESC
    """, (uid,))

    datos = cursor.fetchall()

    cursor.close()
    conn.close()

    registrar_evento(
        usuario_id=uid,
        accion="usuario_ve_rectificaciones",
        detalles={"cantidad": len(datos)}
    )

    return jsonify({"ok": True, "rectificaciones": datos})
