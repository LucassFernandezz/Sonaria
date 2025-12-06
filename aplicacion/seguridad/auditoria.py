# aplicacion/seguridad/auditoria.py
from flask import request
from persistencia.conexion import obtener_conexion
import json
import traceback

def _safe_json(d):
    """
    Serializa 'detalles' sin romper la app si contiene tipos raros.
    """
    try:
        return json.dumps(d, default=str, ensure_ascii=False)
    except Exception:
        return json.dumps({"_error_serializing_detalles": str(d)}, ensure_ascii=False)

def registrar_evento(usuario_id=None, accion=None, detalles=None, ip=None):
    """
    Registra una línea en la tabla auditoria.
    - Nunca debe romper la ejecución del endpoint.
    - Acepta detalles dict o string.
    - Si no hay request, handlea IP = None.
    """

    # Obtener IP de forma segura
    if ip is None:
        try:
            ip = request.remote_addr
        except:
            ip = None

    # Normalizar detalles a JSON
    if detalles is None:
        detalles_json = None
    elif isinstance(detalles, str):
        detalles_json = json.dumps({"msg": detalles}, ensure_ascii=False)
    else:
        detalles_json = _safe_json(detalles)

    # Insertar en DB
    try:
        conn = obtener_conexion()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO auditoria (usuario_id, accion, detalles, ip)
                VALUES (%s, %s, %s, %s)
            """, (usuario_id, accion, detalles_json, ip))

        conn.commit()
        conn.close()

    except Exception as e:
        print("ERROR registrar_evento:", e)
        traceback.print_exc()
        try:
            conn.close()
        except:
            pass


# ----------------------------------------------------------
# Decorador opcional para auditar endpoints automáticamente
# ----------------------------------------------------------
from functools import wraps

def auditar(accion):
    """
    Decorador para auditar inicio/ok/error de un endpoint.
    """
    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):

            registrar_evento(
                accion=f"{accion}_inicio",
                detalles={"args": kwargs}
            )

            try:
                resp = f(*args, **kwargs)

                registrar_evento(
                    accion=f"{accion}_ok"
                )
                return resp

            except Exception as e:
                registrar_evento(
                    accion=f"{accion}_error",
                    detalles={"error": str(e)}
                )
                raise

        return wrapper
    return deco
