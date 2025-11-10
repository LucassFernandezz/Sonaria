from db import get_connection

def registrar_accion(id_usuario, accion, resultado=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bitacora (id_usuario, accion, resultado) VALUES (%s, %s, %s)",
        (id_usuario, accion, resultado)
    )
    conn.commit()
    cursor.close()
    conn.close()

def obtener_bitacora():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM bitacora ORDER BY fecha_hora DESC")
    logs = cursor.fetchall()
    cursor.close()
    conn.close()
    return logs
