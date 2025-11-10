from db import get_connection

def agregar_colaboracion(id_proyecto, id_usuario, archivo_pista, comentario=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO colaboraciones (id_proyecto, id_usuario, archivo_pista, comentario) VALUES (%s, %s, %s, %s)",
        (id_proyecto, id_usuario, archivo_pista, comentario)
    )
    conn.commit()
    cursor.close()
    conn.close()

def obtener_colaboraciones_proyecto(id_proyecto):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM colaboraciones WHERE id_proyecto = %s", (id_proyecto,))
    colabs = cursor.fetchall()
    cursor.close()
    conn.close()
    return colabs
