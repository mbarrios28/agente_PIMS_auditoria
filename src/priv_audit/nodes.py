# src/priv_audit/nodes.py
import os
import json
from .state import AgentState
from .llm import llm

SCHEMA_HALLAZGO = """{
  "hallazgos": [
    {
      "tabla": "nombre_tabla",
      "campos_afectados": ["campo1", "campo2"],
      "descripcion_hallazgo": "Descripcion formal del hallazgo.",
      "evidencia": "Fragmento SQL que lo demuestra.",
      "nivel_riesgo": "ALTO|MEDIO|BAJO",
      "riesgo_potencial": "Impacto potencial sobre la privacidad.",
      "informacion_faltante": "Que falta saber para dar conclusion definitiva.",
      "recomendacion_mitigacion": "Medida tecnica concreta.",
      "criterio_normativo": "ISO 27701:2025, control X.X - Nombre del control."
    }
  ],
  "resumen_ejecutivo": "Resumen formal con cantidad de hallazgos por nivel de riesgo."
}"""


def nodo_validar(state: AgentState) -> dict:
    print("[Nodo] Validando entrada...")
    sql = state.get("esquema_sql", "")
    if not sql.strip():
        return {"errores": "No se proporciono esquema SQL para analizar."}
    return {"errores": None, "iteraciones": 0, "informe_aprobado": False, "resumen_ejecutivo": ""}


def nodo_extraer(state: AgentState) -> dict:
    print("[Nodo] Extrayendo tablas del esquema...")
    sql = state.get("esquema_sql", "")
    tablas = []
    for linea in sql.upper().split("\n"):
        if "CREATE TABLE" in linea:
            partes = linea.strip().split()
            try:
                idx = partes.index("TABLE")
                if idx + 1 < len(partes):
                    nombre = partes[idx + 1].strip("(").strip("`").strip('"')
                    tablas.append(nombre)
            except ValueError:
                pass
    if not tablas:
        tablas = ["(no se identificaron tablas con CREATE TABLE)"]
    print(f"[Nodo] Tablas encontradas: {tablas}")
    return {"tablas_extraidas": tablas}


def nodo_evaluar(state: AgentState) -> dict:
    intentos = state.get("iteraciones", 0) + 1
    print(f"[Nodo] Intento {intentos} - Evaluando esquema con el agente de IA...")

    sql = state.get("esquema_sql", "")

    ruta_md = os.path.join(os.path.dirname(__file__), "knowledge", "skill_privacidad.md")
    with open(ruta_md, "r", encoding="utf-8") as f:
        skill_contexto = f.read()

    prompt = f"""{skill_contexto}

ESQUEMA SQL A ANALIZAR:
{sql}

INSTRUCCIONES DE SALIDA:
- Devuelve UNICAMENTE un objeto JSON valido con la siguiente estructura exacta:
{SCHEMA_HALLAZGO}

- Genera un hallazgo por cada tabla que contenga campos con riesgo de privacidad.
- El campo "criterio_normativo" DEBE citar la norma con numero de control (ejemplo: "ISO 27701:2025, control 8.3 - Minimizacion de datos").
- El campo "nivel_riesgo" DEBE ser exactamente "ALTO", "MEDIO" o "BAJO".
- Usa castellano formal. Sin emojis.
"""

    if intentos > 1:
        prompt += "\n\nADVERTENCIA DEL SISTEMA DE CALIDAD: El reporte anterior fue rechazado porque el campo 'criterio_normativo' no cito el numero de control de la norma. Corrige esto en todos los hallazgos."

    respuesta = llm.invoke(prompt)
    contenido = respuesta.content

    try:
        datos = json.loads(contenido)
    except json.JSONDecodeError:
        # Intentar extraer JSON si viene con texto adicional
        import re
        match = re.search(r'\{.*\}', contenido, re.DOTALL)
        if match:
            datos = json.loads(match.group())
        else:
            datos = {"hallazgos": [], "resumen_ejecutivo": "Error al parsear respuesta del modelo."}

    hallazgos = datos.get("hallazgos", [])
    resumen = datos.get("resumen_ejecutivo", "")

    return {
        "hallazgos": hallazgos,
        "iteraciones": intentos,
        "resumen_ejecutivo": resumen
    }


def nodo_autoevaluar(state: AgentState) -> dict:
    """El agente verifica la calidad de su propio informe antes de aprobarlo."""
    print("[Nodo] Auto-evaluando calidad del informe...")
    hallazgos = state.get("hallazgos", [])

    if not hallazgos:
        print("[Nodo] Sin hallazgos. Rechazado.")
        return {"informe_aprobado": False}

    rechazados = []
    for h in hallazgos:
        criterio = h.get("criterio_normativo", "").upper()
        nivel = h.get("nivel_riesgo", "")

        cita_norma = any(k in criterio for k in ["27701", "27001", "29733", "42001"])
        nivel_valido = nivel in ("ALTO", "MEDIO", "BAJO")

        if not cita_norma or not nivel_valido:
            rechazados.append(h.get("tabla", "desconocida"))

    if rechazados:
        print(f"[Nodo] Control de calidad RECHAZADO en tablas: {rechazados}")
        return {"informe_aprobado": False}

    print("[Nodo] Control de calidad APROBADO. Todos los hallazgos citan normas correctamente.")
    return {"informe_aprobado": True}
