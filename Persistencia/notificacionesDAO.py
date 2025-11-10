from db import get_connection

def enviar_notificacion(id_usuario, mensaje, tipo):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notificaciones (id_usuario, mensaje, tipo) VALUES (%s, %s, %s)",
        (id_usuario, mensaje, tipo)
    )
    conn.commit()
    cursor.close()
    conn.close()

def obtener_notificaciones(id_usuario):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM notificaciones WHERE id_usuario = %s ORDER BY fecha_envio DESC", (id_usuario,))
    notis = cursor.fetchall()
    cursor.close()
    conn.close()
    return notis
