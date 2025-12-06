import json
from persistencia.conexion import obtener_conexion
from flask import request

def registrar_evento(usuario_id, accion, detalles=None, ip=None):
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        # Convertir dict a JSON text si corresponde
        if isinstance(detalles, dict):
            detalles = json.dumps(detalles, ensure_ascii=False)

        # Si no pasaron IP, tomar la del request automáticamente
        if ip is None:
            ip = request.remote_addr if request else None

        cursor.execute("""
            INSERT INTO auditoria (usuario_id, accion, detalles, ip)
            VALUES (%s, %s, %s, %s)
        """, (usuario_id, accion, detalles, ip))

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print("ERROR logger:", e)
