import socket

def enviar_notificacion_tcp(mensaje: str):
    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect(("127.0.0.1", 5050))
        cliente.send(mensaje.encode("utf-8"))
        cliente.close()
    except Exception as e:
        print("[TCP] No se pudo enviar notificación:", e)
