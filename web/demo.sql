
    -- Tabla de personas/titulares de datos
    CREATE TABLE persona (
        id_persona       INT PRIMARY KEY AUTO_INCREMENT,
        dni              VARCHAR(8) NOT NULL,
        nombres          VARCHAR(100) NOT NULL,
        apellidos        VARCHAR(100) NOT NULL,
        fecha_nacimiento DATE,
        correo           VARCHAR(150),
        telefono         VARCHAR(15),
        direccion        VARCHAR(250),
        religion         VARCHAR(80),
        discapacidad     VARCHAR(100),
        created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Tabla de usuarios del sistema
    CREATE TABLE usuario (
        id_usuario       INT PRIMARY KEY AUTO_INCREMENT,
        id_persona       INT NOT NULL,
        username         VARCHAR(60) UNIQUE NOT NULL,
        password         VARCHAR(255) NOT NULL,
        rol              ENUM('admin','auditor','operador') NOT NULL,
        ultimo_acceso    DATETIME,
        ip_ultimo_acceso VARCHAR(45),
        activo           BOOLEAN DEFAULT TRUE,
        FOREIGN KEY (id_persona) REFERENCES persona(id_persona)
    );

    -- Tabla de consentimientos
    CREATE TABLE consentimiento (
        id_consentimiento INT PRIMARY KEY AUTO_INCREMENT,
        id_persona        INT NOT NULL,
        finalidad         VARCHAR(300),
        fecha_otorgamiento DATETIME,
        fecha_revocacion  DATETIME,
        canal             VARCHAR(80),
        FOREIGN KEY (id_persona) REFERENCES persona(id_persona)
    );

    -- Tabla de incidentes de privacidad
    CREATE TABLE incidente_privacidad (
        id_incidente       INT PRIMARY KEY AUTO_INCREMENT,
        descripcion        TEXT,
        fecha_deteccion    DATETIME,
        id_persona_afectada INT,
        datos_expuestos    TEXT,
        estado             VARCHAR(50),
        FOREIGN KEY (id_persona_afectada) REFERENCES persona(id_persona)
    );

    -- Tabla de log de acceso a datos
    CREATE TABLE log_acceso (
        id_log         INT PRIMARY KEY AUTO_INCREMENT,
        id_usuario     INT NOT NULL,
        tabla_accedida VARCHAR(100),
        accion         ENUM('SELECT','INSERT','UPDATE','DELETE'),
        fecha_hora     DATETIME,
        ip_origen      VARCHAR(45),
        FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
    );

    -- Tabla de tratamiento de datos (registro de actividades)
    CREATE TABLE tratamiento_dato (
        id_tratamiento              INT PRIMARY KEY AUTO_INCREMENT,
        nombre                      VARCHAR(200),
        finalidad                   VARCHAR(500),
        base_legal                  VARCHAR(200),
        responsable                 VARCHAR(150),
        destinatarios               TEXT,
        transferencia_internacional BOOLEAN DEFAULT FALSE,
        pais_destino                VARCHAR(100),
        plazo_conservacion          VARCHAR(100),
        medidas_seguridad           TEXT
    );
    