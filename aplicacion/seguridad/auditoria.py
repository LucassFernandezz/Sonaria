from flask import request
from persistencia.conexion import obtener_conexion
import json

def registrar_evento(usuario_id, accion, detalles=None):
    """
    Inserta una línea en la tabla auditoria.
    """
    conn = obtener_conexion()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO auditoria (usuario_id, accion, detalles, ip)
        VALUES (%s, %s, %s, %s)
    """, (
        usuario_id,
        accion,
        json.dumps(detalles) if detalles else None,
        request.remote_addr
    ))

    conn.commit()
    cursor.close()
    conn.close()
