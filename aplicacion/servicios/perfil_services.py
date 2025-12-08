from persistencia.conexion import obtener_conexion
from aplicacion.seguridad.cifrado import cifrar, descifrar


class PerfilService:

    @staticmethod
    def obtener_o_crear(usuario_id):
        con = obtener_conexion()
        cur = con.cursor(dictionary=True)

        cur.execute("""
            SELECT * FROM perfiles_artisticos
            WHERE usuario_id = %s
        """, (usuario_id,))
        perfil = cur.fetchone()

        if not perfil:
            cur.execute("""
                INSERT INTO perfiles_artisticos
                (usuario_id, nombre_artistico, descripcion, genero_principal, habilidades)
                VALUES (%s, %s, '', '', '')
            """, (usuario_id, cifrar("")))
            con.commit()

            cur.execute("""
                SELECT * FROM perfiles_artisticos
                WHERE usuario_id = %s
            """, (usuario_id,))
            perfil = cur.fetchone()

        # DESCIFRAR
        if perfil and perfil["nombre_artistico"]:
            perfil["nombre_artistico"] = descifrar(perfil["nombre_artistico"])

        return perfil


    @staticmethod
    def actualizar(usuario_id, datos):
        con = obtener_conexion()
        cur = con.cursor(dictionary=True)

        # OBTENER EL VALOR ACTUAL (para evitar sobreescribir mal)
        cur.execute("""
            SELECT nombre_artistico
            FROM perfiles_artisticos
            WHERE usuario_id = %s
        """, (usuario_id,))
        actual = cur.fetchone()

        actual_valor = actual["nombre_artistico"] if actual else ""

        # LO NUEVO QUE VIENE DEL CLIENTE
        nuevo_valor = datos.get("nombre_artistico", "")

        # SI VIENE DESDE PERFIL: SI YA ESTÁ CIFRADO, NO TOCAR
        if nuevo_valor.startswith("gAAAAA"):
            nombre_cifrado = nuevo_valor
        else:
            nombre_cifrado = cifrar(nuevo_valor)

        cur = con.cursor()

        cur.execute("""
            UPDATE perfiles_artisticos
            SET nombre_artistico=%s,
                descripcion=%s,
                genero_principal=%s,
                habilidades=%s
            WHERE usuario_id=%s
        """, (
            nombre_cifrado,
            datos.get("descripcion", ""),
            datos.get("genero_principal", ""),
            datos.get("habilidades", ""),
            usuario_id
        ))

        con.commit()
