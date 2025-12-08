# aplicacion/seguridad/cifrado.py

from cryptography.fernet import Fernet
import os

# ============================================================
# 1) Cargar o generar la clave de cifrado
# ============================================================

RUTA_KEY = "clave_aes.key"

def obtener_fernet():
    """
    Carga la clave AES/Fernet desde archivo.
    Si no existe, la genera.
    (En producción NO se sube el archivo clave al repositorio)
    """
    if not os.path.exists(RUTA_KEY):
        clave = Fernet.generate_key()
        with open(RUTA_KEY, "wb") as f:
            f.write(clave)
    else:
        with open(RUTA_KEY, "rb") as f:
            clave = f.read()

    return Fernet(clave)


fernet = obtener_fernet()


# ============================================================
# 2) Funciones públicas
# ============================================================

def cifrar(texto: str) -> str:
    """
    Recibe texto normal y devuelve texto cifrado (str).
    """
    if texto is None:
        return None

    cifrado = fernet.encrypt(texto.encode("utf-8"))
    return cifrado.decode("utf-8")


def descifrar(texto_cifrado: str) -> str:
    """
    Recibe texto cifrado (str) y devuelve texto plano.
    """
    if texto_cifrado is None:
        return None

    plano = fernet.decrypt(texto_cifrado.encode("utf-8"))
    return plano.decode("utf-8")
