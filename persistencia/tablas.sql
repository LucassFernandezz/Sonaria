DROP DATABASE IF EXISTS sonaria;
CREATE DATABASE sonaria;
USE sonaria;

-- Tablas
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol ENUM('visitante', 'registrado', 'admin') NOT NULL DEFAULT 'registrado',
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE perfiles_artisticos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    nombre_artistico VARCHAR(100),
    descripcion TEXT,
    genero_principal VARCHAR(50),
    habilidades VARCHAR(255), -- Ej: "voz,guitarra,mezcla"
    imagen_perfil VARCHAR(255),
    
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE CASCADE
);

CREATE TABLE proyectos_audio (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    titulo VARCHAR(120) NOT NULL,
    descripcion TEXT,
    genero VARCHAR(50),
    archivo_audio VARCHAR(255) NOT NULL,
    necesita VARCHAR(50), -- Ej: "voz","bajo","guitarra"
    estado ENUM('abierto','en_proceso','completado') DEFAULT 'abierto',
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE CASCADE
);

CREATE TABLE colaboraciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    proyecto_id INT NOT NULL,
    usuario_colaborador_id INT NOT NULL,
    mensaje TEXT,
    estado ENUM('pendiente','aceptada','rechazada') DEFAULT 'pendiente',
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (proyecto_id) REFERENCES proyectos_audio(id)
        ON DELETE CASCADE,
        
    FOREIGN KEY (usuario_colaborador_id) REFERENCES usuarios(id)
        ON DELETE CASCADE
);

CREATE TABLE takes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    colaboracion_id INT NOT NULL,
    archivo_audio VARCHAR(255) NOT NULL,
    comentarios TEXT,
    fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (colaboracion_id) REFERENCES colaboraciones(id)
        ON DELETE CASCADE
);

CREATE TABLE auditoria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    accion VARCHAR(120) NOT NULL,
    detalles JSON,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip VARCHAR(50),

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE SET NULL
);

CREATE TABLE notificaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    tipo VARCHAR(50) NOT NULL,        -- Ej: "colaboracion_nueva"
    payload JSON,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    entregada BOOLEAN DEFAULT FALSE,

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE CASCADE
);

CREATE TABLE metricas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(100) NOT NULL,       -- Ej: "ranking-colaboradores"
    valor JSON,
    fecha_calculo DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rectificaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entidad VARCHAR(100) NOT NULL,      -- Ej: "proyectos_audio"
    entidad_id INT,
    error_detectado TEXT,
    accion_realizada TEXT,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE secretos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    clave_cifrada VARCHAR(255) NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON DELETE CASCADE
);
