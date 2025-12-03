from persistencia.conexion import obtener_conexion
from aplicacion.seguridad.hashing import generar_hash, verificar_hash

class AuthService:

    @staticmethod
    def registrar(email, password):
        con = obtener_conexion()
        cur = con.cursor()

        cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
        existe = cur.fetchone()

        if existe:
            return {"ok": False, "error": "Email ya registrado"}

        hash_pw = generar_hash(password)

        cur.execute("""
            INSERT INTO usuarios (email, password_hash, rol)
            VALUES (%s, %s, 'registrado')
        """, (email, hash_pw))

        con.commit()

        return {"ok": True}

    @staticmethod
    def login(email, password):
        con = obtener_conexion()
        cur = con.cursor(dictionary=True)

        cur.execute("""
            SELECT id, email, password_hash, rol
            FROM usuarios
            WHERE email=%s
        """, (email,))

        usuario = cur.fetchone()

        if not usuario:
            return {"ok": False, "error": "Usuario no existe"}

        if not verificar_hash(password, usuario["password_hash"]):
            return {"ok": False, "error": "Contraseña incorrecta"}

        return {
            "ok": True,
            "usuario": {
                "id": usuario["id"],
                "email": email,
                "rol": usuario["rol"]
            }
        }
