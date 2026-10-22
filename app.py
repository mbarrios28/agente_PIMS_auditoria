# app.py
import os
import sys

def modo_auditoria():
    from src.priv_audit.graph import app_grafo
    from src.priv_audit.pdf_report import generar_pdf

    print("--- INICIANDO AUDITORIA DE PRIVACIDAD ---")
    print("Marco normativo: ISO 27701:2025 | ISO 27001:2022 | ISO 42001:2023 | Ley 29733")
    print("-" * 60)

    sql_demo = """
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
    """

    estado_inicial = {
        "esquema_sql": sql_demo,
        "tablas_extraidas": [],
        "hallazgos": [],
        "errores": None,
        "iteraciones": 0,
        "informe_aprobado": False,
        "resumen_ejecutivo": ""
    }

    resultado = app_grafo.invoke(estado_inicial)

    print("\n" + "=" * 60)
    print("RESULTADO DE LA AUDITORIA")
    print("=" * 60)

    hallazgos  = resultado.get("hallazgos", [])
    resumen    = resultado.get("resumen_ejecutivo", "Sin resumen disponible.")
    aprobado   = resultado.get("informe_aprobado", False)
    iteraciones = resultado.get("iteraciones", 0)

    print(f"Estado      : {'APROBADO' if aprobado else 'EMITIDO CON ADVERTENCIAS'}")
    print(f"Iteraciones : {iteraciones}")
    print(f"Hallazgos   : {len(hallazgos)}")
    print(f"Tablas      : {resultado.get('tablas_extraidas', [])}")

    ruta_pdf = os.path.join(os.path.dirname(__file__), "informe_auditoria_pims.pdf")
    generar_pdf(
        hallazgos=hallazgos,
        resumen_ejecutivo=resumen,
        ruta_salida=ruta_pdf,
        aprobado=aprobado
    )

    print(f"\nInforme PDF generado en: {ruta_pdf}")
    print("Auditoria completada.")


def modo_chat():
    from src.priv_audit.rag_chat import ChatRAG

    agente = ChatRAG()

    print("Modo de consulta activo.")
    print("Escriba su pregunta y presione Enter. Escriba 'salir' para terminar.")
    print("=" * 60)

    while True:
        try:
            pregunta = input("\nConsulta: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSesion terminada.")
            break

        if not pregunta:
            continue

        if pregunta.lower() in ("salir", "exit", "quit"):
            print("Sesion terminada.")
            break

        print()
        respuesta = agente.preguntar(pregunta)
        print("-" * 60)
        print(respuesta)
        print("-" * 60)


def main():
    print("=" * 60)
    print("  PrivAudit AI - Agente de Auditoria de Privacidad")
    print("  PIMS | ISO 27701:2025 | ISO 27001:2022 | Ley 29733")
    print("=" * 60)
    print()
    print("Seleccione el modo de operacion:")
    print("  1. Auditoria autonoma de esquema SQL -> genera informe PDF")
    print("  2. Chat con RAG -> consultas sobre normas ISO y privacidad")
    print()

    opcion = input("Opcion (1 o 2): ").strip()

    if opcion == "1":
        modo_auditoria()
    elif opcion == "2":
        modo_chat()
    else:
        print("Opcion no valida. Ejecutando modo auditoria por defecto.")
        modo_auditoria()


if __name__ == "__main__":
    main()
