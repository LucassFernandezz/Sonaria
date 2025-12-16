from aplicacion.seguridad.digito_verificador import (
    actualizar_dvh_usuario,
    actualizar_dvv_usuarios
)
from persistencia.conexion import obtener_conexion

conn = obtener_conexion()
cursor = conn.cursor()

cursor.execute("SELECT id FROM usuarios")
ids = cursor.fetchall()

for (uid,) in ids:
    actualizar_dvh_usuario(uid)

actualizar_dvv_usuarios()

print("DVH y DVV recalculados correctamente")
