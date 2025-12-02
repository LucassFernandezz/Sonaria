import socket

def iniciar_servidor_tcp():
    host = "127.0.0.1"
    port = 5050

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind((host, port))
    servidor.listen(5)

    print(f"[TCP] Servidor TCP escuchando en {host}:{port}")

    while True:
        conexion, direccion = servidor.accept()
        print(f"[TCP] Cliente conectado desde {direccion}")

        mensaje = conexion.recv(1024).decode("utf-8")
        print("[TCP] Mensaje recibido:", mensaje)

        conexion.send("Mensaje recibido correctamente".encode("utf-8"))
        conexion.close()
