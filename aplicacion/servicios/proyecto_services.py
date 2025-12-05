from persistencia.conexion import obtener_conexion

class ProyectoService:

    @staticmethod
    def crear(usuario_id, titulo, descripcion, genero, necesita, archivo_audio):
        con = obtener_conexion()
        cur = con.cursor()

        cur.execute("""
            INSERT INTO proyectos_audio (usuario_id, titulo, descripcion, genero, necesita, archivo_audio)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (usuario_id, titulo, descripcion, genero, necesita, archivo_audio))

        con.commit()

        return cur.lastrowid
