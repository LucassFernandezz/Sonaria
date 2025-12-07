# aplicacion/rutas/admin_metricas.py
from flask import Blueprint, jsonify, request
from aplicacion.seguridad.sesiones import esta_autenticado, usuario_actual
from aplicacion.seguridad.auditoria import registrar_evento
from persistencia.conexion import obtener_conexion
import json

metricas_bp = Blueprint("metricas_bp", __name__, url_prefix="/admin/metricas")


# ======================================================
# SOLO ADMIN
# ======================================================
def require_admin():
    if not esta_autenticado():
        return False, jsonify({"error": "No autenticado"}), 401

    user = usuario_actual()
    if user["rol"] != "admin":
        return False, jsonify({"error": "Solo admin"}), 403

    return True, user, None


# ======================================================
# GET /admin/metricas/
# ======================================================
@metricas_bp.route("/", methods=["GET"])
def obtener_metricas():

    ok, user_or_resp, resp_code = require_admin()
    if not ok:
        return user_or_resp, resp_code
    user = user_or_resp

    conn = obtener_conexion()

    with conn.cursor(dictionary=True) as cursor:
        cursor.execute("""
            SELECT id, tipo, valor, fecha_calculo
            FROM metricas
            ORDER BY fecha_calculo DESC
            LIMIT 20
        """)
        datos = cursor.fetchall()

    conn.close()

    registrar_evento(
        usuario_id=user["usuario_id"],
        accion="admin_ver_metricas",
        detalles={"cant_metricas": len(datos)}
    )

    return jsonify({"ok": True, "metricas": datos})


# ======================================================
# POST /admin/metricas/recalcular
# ======================================================
@metricas_bp.route("/recalcular", methods=["POST"])
def recalcular_metricas():

    ok, user_or_resp, resp_code = require_admin()
    if not ok:
        return user_or_resp, resp_code
    user = user_or_resp

    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)

    resultados = {}

    # ----------------------------------------------
    # MÉTRICA: TOP COLABORADORES
    # ----------------------------------------------
    cursor.execute("""
        SELECT u.id, u.email, COUNT(t.id) AS total_takes
        FROM takes t
        JOIN colaboraciones c ON c.id = t.colaboracion_id
        JOIN usuarios u ON u.id = c.usuario_colaborador_id
        GROUP BY u.id
        ORDER BY total_takes DESC
        LIMIT 10
    """)
    top_colaboradores = cursor.fetchall()
    resultados["top_colaboradores"] = top_colaboradores

    cursor.execute("""
        INSERT INTO metricas (tipo, valor)
        VALUES (%s, %s)
    """, ("top_colaboradores", json.dumps(top_colaboradores, ensure_ascii=False)))


    # ----------------------------------------------
    # MÉTRICA: PROYECTOS MÁS COLABORADOS
    # ----------------------------------------------
    cursor.execute("""
        SELECT p.id, p.titulo, COUNT(c.id) AS colaboraciones
        FROM proyectos_audio p
        LEFT JOIN colaboraciones c ON c.proyecto_id = p.id
        GROUP BY p.id
        ORDER BY colaboraciones DESC
        LIMIT 10
    """)
    proyectos_populares = cursor.fetchall()
    resultados["proyectos_populares"] = proyectos_populares

    cursor.execute("""
        INSERT INTO metricas (tipo, valor)
        VALUES (%s, %s)
    """, ("proyectos_populares", json.dumps(proyectos_populares, ensure_ascii=False)))


    # ----------------------------------------------
    # MÉTRICA: ESTADÍSTICAS GENERALES
    # ----------------------------------------------
    cursor.execute("SELECT COUNT(*) AS total FROM usuarios")
    usuarios = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM proyectos_audio")
    proyectos = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM colaboraciones")
    colaboraciones = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM takes")
    takes = cursor.fetchone()["total"]

    generales = {
        "usuarios": usuarios,
        "proyectos": proyectos,
        "colaboraciones": colaboraciones,
        "takes": takes
    }

    resultados["estadisticas_generales"] = generales

    cursor.execute("""
        INSERT INTO metricas (tipo, valor)
        VALUES (%s, %s)
    """, ("estadisticas_generales", json.dumps(generales, ensure_ascii=False)))

    conn.commit()
    cursor.close()
    conn.close()

    registrar_evento(
        usuario_id=user["usuario_id"],
        accion="admin_recalcular_metricas",
        detalles={"resultados": resultados}
    )

    return jsonify({"ok": True, "mensaje": "Métricas recalculadas", "metricas": resultados})
