import mysql.connector

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "root"
DB_NAME = "sonaria"

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
        nombre VARCHAR(40) NOT NULL,
        email VARCHAR(50) NOT NULL UNIQUE,
        contraseña_hash VARCHAR(100) NOT NULL, 
        rol ENUM('musico', 'admin') NOT NULL DEFAULT 'musico',
        fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proyectos (
        id_proyecto INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
        id_usuario INT UNSIGNED NOT NULL,
        titulo VARCHAR(150) NOT NULL,
        descripcion TEXT,
        archivo_base VARCHAR(150),
        fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS colaboraciones (
        id_colaboracion INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
        id_proyecto INT UNSIGNED NOT NULL,
        id_usuario INT UNSIGNED NOT NULL,
        archivo_pista VARCHAR(200) NOT NULL,
        comentario VARCHAR(200),
        fecha_colaboracion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_proyecto) REFERENCES proyectos(id_proyecto),
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bitacora (
        id_bitacora INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
        id_usuario INT UNSIGNED,
        accion VARCHAR(200) NOT NULL,
        resultado VARCHAR(50),
        fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notificaciones (
        id_notificacion INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
        id_usuario INT UNSIGNED NOT NULL,
        mensaje VARCHAR(200) NOT NULL,
        tipo ENUM('colaboracion', 'sistema', 'mensaje') NOT NULL,
        fecha_envio DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        leida BOOLEAN NOT NULL DEFAULT FALSE,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS estadisticas (
        id_estadistica INT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
        nombre VARCHAR(100) NOT NULL UNIQUE,
        valor INT UNSIGNED NOT NULL DEFAULT 0,
        fecha_actualizacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Base de datos inicializada correctamente ✅")

if __name__ == "__main__":
    init_db()
