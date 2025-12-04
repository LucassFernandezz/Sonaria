from persistencia.conexion import obtener_conexion

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

        # Si NO existe → crear perfil vacío
        if not perfil:
            cur.execute("""
                INSERT INTO perfiles_artisticos (usuario_id, nombre_artistico, descripcion, genero_principal, habilidades)
                VALUES (%s, '', '', '', '')
            """, (usuario_id,))
            con.commit()

            cur.execute("""
                SELECT * FROM perfiles_artisticos
                WHERE usuario_id = %s
            """, (usuario_id,))
            perfil = cur.fetchone()

        return perfil


    @staticmethod
    def actualizar(usuario_id, datos):
        con = obtener_conexion()
        cur = con.cursor()

        cur.execute("""
            UPDATE perfiles_artisticos
            SET nombre_artistico=%s,
                descripcion=%s,
                genero_principal=%s,
                habilidades=%s
            WHERE usuario_id=%s
        """, (
            datos.get("nombre_artistico", ""),
            datos.get("descripcion", ""),
            datos.get("genero_principal", ""),
            datos.get("habilidades", ""),
            usuario_id
        ))

        con.commit()
