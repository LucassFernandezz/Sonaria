from db import get_connection

def crear_proyecto(id_usuario, titulo, descripcion=None, archivo_base=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO proyectos (id_usuario, titulo, descripcion, archivo_base) VALUES (%s, %s, %s, %s)",
        (id_usuario, titulo, descripcion, archivo_base)
    )
    conn.commit()
    cursor.close()
    conn.close()

def obtener_proyectos_por_usuario(id_usuario):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM proyectos WHERE id_usuario = %s", (id_usuario,))
    proyectos = cursor.fetchall()
    cursor.close()
    conn.close()
    return proyectos
