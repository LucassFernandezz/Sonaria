import bcrypt

def generar_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hash_final = bcrypt.hashpw(password_bytes, salt)
    return hash_final.decode("utf-8")

def verificar_hash(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
