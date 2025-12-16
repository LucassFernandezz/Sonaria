# aplicacion/seguridad/digito_verificador.py

from persistencia.conexion import obtener_conexion

# --------------------------------------------------
# DVH – cálculo de un registro
# --------------------------------------------------
def calcular_dvh(valores: list[str]) -> int:
    """
    Calcula el DVH sumando el peso ASCII de cada caracter.
    """
    total = 0
    for valor in valores:
        for c in str(valor):
            total += ord(c)
    return total


# --------------------------------------------------
# Recalcular DVH de un usuario
# --------------------------------------------------
def actualizar_dvh_usuario(usuario_id: int):
    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT email, rol, estado
        FROM usuarios
        WHERE id = %s
    """, (usuario_id,))
    u = cursor.fetchone()

    if not u:
        cursor.close()
        conn.close()
        return

    dvh = calcular_dvh([u["email"], u["rol"], u["estado"]])

    cursor.execute("""
        UPDATE usuarios
        SET dvh = %s
        WHERE id = %s
    """, (dvh, usuario_id))

    conn.commit()
    cursor.close()
    conn.close()


# --------------------------------------------------
# Recalcular DVV de la tabla usuarios
# --------------------------------------------------
def actualizar_dvv_usuarios():
    conn = obtener_conexion()
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(dvh) FROM usuarios")
    suma = cursor.fetchone()[0] or 0

    cursor.execute("""
        INSERT INTO digitos_verificadores (tabla, dvv)
        VALUES ('usuarios', %s)
        ON DUPLICATE KEY UPDATE dvv = %s
    """, (suma, suma))

    conn.commit()
    cursor.close()
    conn.close()


# --------------------------------------------------
# Verificar integridad de usuarios
# --------------------------------------------------
def verificar_integridad_usuarios():
    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)

    errores = []

    cursor.execute("""
        SELECT id, email, rol, estado, dvh
        FROM usuarios
    """)
    usuarios = cursor.fetchall()

    for u in usuarios:
        dvh_calculado = calcular_dvh([u["email"], u["rol"], u["estado"]])
        if dvh_calculado != u["dvh"]:
            errores.append({
                "tabla": "usuarios",
                "registro_id": u["id"]
            })

    cursor.execute("""
        SELECT dvv FROM digitos_verificadores
        WHERE tabla = 'usuarios'
    """)
    dvv_guardado = cursor.fetchone()

    dvv_guardado = dvv_guardado["dvv"] if dvv_guardado else 0
    suma_actual = sum(u["dvh"] for u in usuarios)

    cursor.close()
    conn.close()

    return {
        "errores": errores,
        "dvv_ok": suma_actual == dvv_guardado,
        "dvv_actual": suma_actual,
        "dvv_guardado": dvv_guardado
    }

def inicializar_digitos_verificadores_usuarios():
    from persistencia.conexion import obtener_conexion

    conn = obtener_conexion()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM usuarios")
    ids = cursor.fetchall()

    cursor.close()
    conn.close()

    for (uid,) in ids:
        actualizar_dvh_usuario(uid)

    actualizar_dvv_usuarios()
