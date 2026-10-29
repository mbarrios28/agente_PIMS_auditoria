-- DEMOSTRACION ACADEMICA DE PRIVAUDIT / AGENTARCH-PIMS
-- Dialecto: PostgreSQL. Importar como archivo en Auditoria de privacidad.
-- Esquema ficticio inspirado en procesos PIMS; NO es un volcado de GESTITEL.
-- No contiene registros personales, INSERT, credenciales ni conexion remota.
-- La aplicacion interpreta este texto: no ejecuta estas sentencias.
-- Campos elegidos para observar limites de las reglas y discutir evidencia faltante.

CREATE TABLE titular_demo (
    id BIGINT PRIMARY KEY,
    dni VARCHAR(8) NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    correo VARCHAR(150),
    telefono VARCHAR(20),
    fecha_nacimiento DATE,
    salud TEXT
);

CREATE TABLE usuario_demo (
    id BIGINT PRIMARY KEY,
    titular_id BIGINT REFERENCES titular_demo(id),
    username VARCHAR(60) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    ultimo_acceso TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE consentimiento_demo (
    id BIGINT PRIMARY KEY,
    titular_id BIGINT NOT NULL REFERENCES titular_demo(id),
    finalidad VARCHAR(300) NOT NULL,
    version_aviso VARCHAR(30),
    fecha_otorgamiento TIMESTAMP NOT NULL,
    fecha_revocacion TIMESTAMP,
    plazo_conservacion_dias INTEGER
);

CREATE TABLE solicitud_arcop_demo (
    id BIGINT PRIMARY KEY,
    titular_id BIGINT NOT NULL REFERENCES titular_demo(id),
    derecho_solicitado VARCHAR(40) NOT NULL,
    descripcion TEXT,
    fecha_recepcion TIMESTAMP NOT NULL,
    fecha_limite TIMESTAMP,
    fecha_respuesta TIMESTAMP,
    estado VARCHAR(30) NOT NULL
);

CREATE TABLE incidente_demo (
    id BIGINT PRIMARY KEY,
    titular_afectado_id BIGINT REFERENCES titular_demo(id),
    descripcion TEXT NOT NULL,
    datos_expuestos TEXT,
    fecha_deteccion TIMESTAMP NOT NULL,
    estado VARCHAR(30) NOT NULL
);

CREATE TABLE acceso_demo (
    id BIGINT PRIMARY KEY,
    usuario_id BIGINT NOT NULL REFERENCES usuario_demo(id),
    recurso VARCHAR(120) NOT NULL,
    accion VARCHAR(30) NOT NULL,
    fecha_hora TIMESTAMP NOT NULL,
    ip_origen VARCHAR(45)
);

CREATE TABLE evaluacion_control_demo (
    id BIGINT PRIMARY KEY,
    codigo_control VARCHAR(30) NOT NULL,
    evidencia TEXT,
    nivel_actual INTEGER,
    nivel_objetivo INTEGER,
    accion_mejora TEXT,
    fecha_revision DATE
);
