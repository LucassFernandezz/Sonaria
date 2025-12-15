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
    # LOGIN CON BLOQUEO E INTENTOS + ESTADO (activo/bloqueado)
    # ============================================================
    @staticmethod
    def login(email, password):

        conn = obtener_conexion()
        cursor = conn.cursor(dictionary=True)

        ahora = datetime.now()

        # --------------------------------------------------------------------
        # 1) OBTENER ESTADO DEL USUARIO (activo / bloqueado)
        # --------------------------------------------------------------------
        cursor.execute("""
            SELECT id, email, password_hash, rol, estado
            FROM usuarios
            WHERE email = %s
        """, (email,))
        usuario = cursor.fetchone()

        # Si no existe el usuario → error normal
        if not usuario:
            return {"ok": False, "error": "Email o contraseña incorrectos"}
        
        # --------------------------------------------------------------------
        # 🚫 SI EL USUARIO ESTÁ ELIMINADO → NO EXISTE PARA EL SISTEMA
        # --------------------------------------------------------------------
        if usuario["estado"] == "eliminado":
            registrar_evento(
                usuario_id=usuario["id"],
                accion="login_usuario_eliminado",
                detalles={"email": email},
                criticidad="alta"
            )
            return {"ok": False, "error": "Cuenta eliminada"}


        # --------------------------------------------------------------------
        # 🚫 SI ESTÁ BLOQUEADO POR EL ADMIN → NO PERMITIR LOGIN
        # --------------------------------------------------------------------
        if usuario["estado"] == "bloqueado":
            registrar_evento(
                usuario_id=usuario["id"],
                accion="login_usuario_bloqueado",
                detalles={"email": email}
            )
            return {"ok": False, "error": "Cuenta bloqueada por el administrador"}

        # --------------------------------------------------------------------
        # 2) OBTENER ESTADO DE INTENTOS PREVIOS (tu tabla intentos_login)
        # --------------------------------------------------------------------
        cursor.execute("""
            SELECT intentos, bloqueado_hasta
            FROM intentos_login
            WHERE email = %s
        """, (email,))
        intento = cursor.fetchone()

        # Si está bloqueado temporalmente
        if intento and intento["bloqueado_hasta"] and intento["bloqueado_hasta"] > ahora:
            segundos = int((intento["bloqueado_hasta"] - ahora).total_seconds())

            registrar_evento(
                usuario_id=usuario["id"],
                accion="login_bloqueado_temporal",
                detalles={"segundos_restantes": segundos}
            )

            return {"ok": False, "error": f"Cuenta bloqueada. Espera {segundos} segundos."}

        # --------------------------------------------------------------------
        # 3) VALIDAR CONTRASEÑA
        # --------------------------------------------------------------------
        if not verificar_hash(password, usuario["password_hash"]):

            # Registrar incrementos
            if not intento:
                cursor.execute("""
                    INSERT INTO intentos_login (email, intentos, ultimo_intento)
                    VALUES (%s, 1, NOW())
                """, (email,))
            else:
                nuevos = intento["intentos"] + 1
                bloqueo = None

                if nuevos >= MAX_INTENTOS:
                    bloqueo = ahora + timedelta(minutes=BLOQUEO_MINUTOS)

                cursor.execute("""
                    UPDATE intentos_login
                    SET intentos=%s, ultimo_intento=NOW(), bloqueado_hasta=%s
                    WHERE email=%s
                """, (nuevos, bloqueo, email))

            conn.commit()

            registrar_evento(
                usuario_id=usuario["id"],
                accion="login_fallido",
                detalles={"email": email}
            )

            return {"ok": False, "error": "Email o contraseña incorrectos"}

        # --------------------------------------------------------------------
        # 4) LOGIN CORRECTO → RESET DE INTENTOS
        # --------------------------------------------------------------------
        cursor.execute("DELETE FROM intentos_login WHERE email=%s", (email,))
        conn.commit()

        registrar_evento(
            usuario_id=usuario["id"],
            accion="login_exitoso",
            detalles={"email": usuario["email"]})
        
        # Construcción de datos a devolver
        datos_usuario = {
            "id": usuario["id"],
            "email": usuario["email"],
            "rol": usuario["rol"],
            "estado": usuario["estado"]
        }

        cursor.close()
        conn.close()

        return {"ok": True, "usuario": datos_usuario}
