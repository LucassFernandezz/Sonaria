from db import get_connection
import hashlib

def crear_usuario(nombre, email, contraseña, rol='musico'):
    contraseña_hash = hashlib.sha256(contraseña.encode()).hexdigest()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO usuarios (nombre, email, contraseña_hash, rol) VALUES (%s, %s, %s, %s)",
        (nombre, email, contraseña_hash, rol)
    )
    conn.commit()
    cursor.close()
    conn.close()

def obtener_usuario_por_email(email):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()
    return usuario
