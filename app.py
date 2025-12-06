# sonaria/app.py

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_session import Session
from threading import Thread

# Importar blueprints
from aplicacion.rutas.auth import auth_bp
from aplicacion.rutas.perfiles import perfiles_bp
from aplicacion.rutas.proyectos import proyectos_bp
from aplicacion.rutas.colaboraciones import colaboraciones_bp
from aplicacion.rutas.admin_auditoria import auditoria_bp
from aplicacion.rutas.admin_integridad import integridad_bp
from aplicacion.rutas.admin_metricas import metricas_bp
from aplicacion.rutas.notificaciones import notificaciones_bp

# Servidor TCP
from aplicacion.sockets.tcp_server import iniciar_servidor_tcp


def crear_app():
    app = Flask(__name__)

    # Clave para sesiones
    app.secret_key = "clave_super_secreta_de_sonaria"

    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = False
    Session(app)

    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

    # Indico dónde se guardan los audios
    app.config["UPLOAD_FOLDER"] = "uploads"

    # Ruta para servir archivos del frontend
    @app.route('/presentacion/<path:archivo>')
    def servir_frontend(archivo):
        return send_from_directory("presentacion", archivo)
    
    # Ruta para servir audios subidos
    @app.route('/uploads/<path:filename>')
    def servir_uploads(filename):
        return send_from_directory("uploads", filename)

    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(perfiles_bp)
    app.register_blueprint(proyectos_bp)
    app.register_blueprint(colaboraciones_bp)
    app.register_blueprint(auditoria_bp)
    app.register_blueprint(integridad_bp)
    app.register_blueprint(metricas_bp)
    app.register_blueprint(notificaciones_bp)

    return app


if __name__ == "__main__":
    from werkzeug.serving import is_running_from_reloader

    # Crear instancia real de Flask
    app = crear_app()

    # Arrancar servidor TCP solo una vez
    if not is_running_from_reloader():
        hilo_tcp = Thread(target=iniciar_servidor_tcp, daemon=True)
        hilo_tcp.start()

    # Arrancar Flask
    app.run(debug=True, host="localhost", port=5000)
