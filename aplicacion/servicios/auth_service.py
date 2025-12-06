from persistencia.conexion import obtener_conexion
from aplicacion.seguridad.hashing import generar_hash, verificar_hash
from aplicacion.seguridad.auditoria import registrar_evento
from datetime import datetime, timedelta


# Seguridad del login
MAX_INTENTOS = 5
BLOQUEO_MINUTOS = 10


class AuthService:

    # ============================================================
    # REGISTRO DE USUARIO
    # ============================================================
    @staticmethod
    def registrar(email, password):

        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)

        # ¿Existe ya el email?
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        existe = cursor.fetchone()

        if existe:
            cursor.close()
            conn.close()
            return {"ok": False, "error": "Email ya registrado"}

        # Hash de contraseña (tu hashing.py)
        hash_pw = generar_hash(password)

        cursor.execute("""
            INSERT INTO usuarios (email, password_hash, rol)
            VALUES (%s, %s, 'registrado')
        """, (email, hash_pw))

        conn.commit()

        # Obtener usuario insertado
        cursor.execute("""
            SELECT id, email, rol 
            FROM usuarios 
            WHERE email = %s
        """, (email,))
        
        usuario = cursor.fetchone()

        cursor.close()
        conn.close()

        return {"ok": True, "usuario": usuario}


    # ============================================================
    # LOGIN CON BLOQUEO E INTENTOS
    # ============================================================
    @staticmethod
    def login(email, password):

        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)

        ahora = datetime.now()

        # --------------------------------------------------------------------
        # 1) OBTENER ESTADO DE INTENTOS PREVIOS
        # --------------------------------------------------------------------
        cursor.execute("""
            SELECT intentos, bloqueado_hasta
            FROM intentos_login
            WHERE email = %s
        """, (email,))
        intento = cursor.fetchone()

        # SI ESTÁ BLOQUEADO, SALIR
        if intento and intento["bloqueado_hasta"] and intento["bloqueado_hasta"] > ahora:
            segundos = int((intento["bloqueado_hasta"] - ahora).total_seconds())

            registrar_evento(
                usuario_id=None,
                accion="login_bloqueado",
                detalles={"email": email, "segundos_restantes": segundos}
            )

            cursor.close()
            conn.close()

            return {"ok": False, "error": f"Cuenta bloqueada. Espera {segundos} segundos."}

        # --------------------------------------------------------------------
        # 2) BUSCAR USUARIO
        # --------------------------------------------------------------------
        cursor.execute("""
            SELECT id, email, password_hash, rol
            FROM usuarios
            WHERE email = %s
        """, (email,))
        usuario = cursor.fetchone()

        # --------------------------------------------------------------------
        # 3) SI FALTA USUARIO O CONTRASEÑA INCORRECTA → FALLA
        # --------------------------------------------------------------------
        if not usuario or not verificar_hash(password, usuario["password_hash"]):

            # Registrar (o incrementar) intentos fallidos
            if not intento:
                cursor.execute("""
                    INSERT INTO intentos_login (email, intentos, ultimo_intento)
                    VALUES (%s, 1, NOW())
                """, (email,))
            else:
                nuevos = intento["intentos"] + 1
                bloqueo = None

                # ¿Llega al máximo?
                if nuevos >= MAX_INTENTOS:
                    bloqueo = ahora + timedelta(minutes=BLOQUEO_MINUTOS)

                cursor.execute("""
                    UPDATE intentos_login
                    SET intentos = %s,
                        ultimo_intento = NOW(),
                        bloqueado_hasta = %s
                    WHERE email = %s
                """, (nuevos, bloqueo, email))

            conn.commit()

            registrar_evento(
                usuario_id=None,
                accion="login_fallido",
                detalles={"email": email}
            )

            cursor.close()
            conn.close()

            return {"ok": False, "error": "Email o contraseña incorrectos"}

        # --------------------------------------------------------------------
        # 4) LOGIN CORRECTO → RESET INTENTOS
        # --------------------------------------------------------------------
        cursor.execute("DELETE FROM intentos_login WHERE email = %s", (email,))
        conn.commit()

        registrar_evento(
            usuario_id=usuario["id"],
            accion="login_exitoso",
            detalles={"email": usuario["email"]}
        )

        # Devolver usuario sin hash
        datos_usuario = {
            "id": usuario["id"],
            "email": usuario["email"],
            "rol": usuario["rol"]
        }

        cursor.close()
        conn.close()

        return {"ok": True, "usuario": datos_usuario}
