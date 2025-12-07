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
# → Obtener SOLO las últimas 3 métricas por tipo
# ======================================================
@metricas_bp.route("/", methods=["GET"])
def obtener_metricas():

    ok, user_or_resp, resp_code = require_admin()
    if not ok:
        return user_or_resp, resp_code
    user = user_or_resp

    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)

    # 1) Obtener los tipos disponibles
    cursor.execute("SELECT DISTINCT tipo FROM metricas")
    tipos = [fila["tipo"] for fila in cursor.fetchall()]

    metricas_finales = []

    # 2) Para cada tipo, traer solo las últimas 3
    for tipo in tipos:
        cursor.execute("""
            SELECT id, tipo, valor, fecha_calculo
            FROM metricas
            WHERE tipo = %s
            ORDER BY fecha_calculo DESC
            LIMIT 3
        """, (tipo,))
        registros = cursor.fetchall()
        metricas_finales.extend(registros)

    cursor.close()
    conn.close()

    metricas_finales = sorted(
        metricas_finales,
        key=lambda x: x["fecha_calculo"],
        reverse=True
    )

    registrar_evento(
        usuario_id=user["usuario_id"],
        accion="admin_ver_metricas",
        detalles={"metricas_mostradas": len(metricas_finales)}
    )

    return jsonify({"ok": True, "metricas": metricas_finales})



# ======================================================
# POST /admin/metricas/recalcular
# Generar una nueva ejecución de métricas
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
    # MÉTRICA: PROYECTOS POPULARES
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
