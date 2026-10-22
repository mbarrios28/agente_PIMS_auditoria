# src/priv_audit/rag_chat.py
"""
Modulo de chat con RAG.
El usuario escribe preguntas y el agente responde usando
los documentos indexados (skill + ISOs) como contexto.
Si no encuentra contexto relevante, responde con el conocimiento
propio del LLM indicandolo explicitamente.
"""
from .rag_loader import cargar_base_conocimiento
from .rag_retriever import Retriever
from .llm import llm_chat as llm

SYSTEM_PROMPT = """Eres PrivAudit, un agente especializado en auditoria de privacidad de datos y seguridad de la informacion.
Tu conocimiento se basa en las normas ISO 27701:2025, ISO 27001:2022, ISO 42001:2023 y la Ley 29733 de Peru.
Respondes en castellano formal. Sin emojis. Tus respuestas son precisas, tecnicas y citas las normas cuando aplica."""


def construir_prompt_rag(pregunta: str, contextos: list[dict]) -> str:
    if contextos:
        bloques = []
        for ctx in contextos:
            bloques.append(
                f"[Fuente: {ctx['fuente']} | Relevancia: {ctx['score']:.2f}]\n{ctx['texto']}"
            )
        contexto_str = "\n\n---\n\n".join(bloques)

        return f"""{SYSTEM_PROMPT}

A continuacion se incluyen fragmentos de los documentos de referencia que son relevantes para la siguiente pregunta.
Usa esta informacion como base para tu respuesta. Si la informacion no es suficiente, complementa con tu conocimiento
y explicita cuando lo haces.

FRAGMENTOS DE REFERENCIA:
{contexto_str}

PREGUNTA DEL USUARIO:
{pregunta}

INSTRUCCIONES:
- Responde directamente a la pregunta.
- Cita el numero de control o articulo de la norma cuando sea pertinente.
- Si un fragmento no es relevante, ignoralo.
- Usa castellano formal. Sin emojis.
"""
    else:
        return f"""{SYSTEM_PROMPT}

No se encontraron fragmentos relevantes en la base de conocimiento para esta pregunta.
Responde utilizando tu conocimiento propio e indica al inicio de tu respuesta:
"Respuesta basada en conocimiento del modelo (no se encontro contexto en los documentos cargados)."

PREGUNTA DEL USUARIO:
{pregunta}
"""


class ChatRAG:
    def __init__(self):
        print("[Chat RAG] Cargando base de conocimiento...")
        chunks = cargar_base_conocimiento()
        self.retriever = Retriever(chunks)
        self.historial = []   # lista de {"rol": ..., "contenido": ...}
        print("[Chat RAG] Listo para recibir consultas.")
        print("-" * 60)

    def preguntar(self, pregunta: str) -> str:
        # 1. Recuperar contexto relevante
        contextos = self.retriever.recuperar(pregunta, top_k=5)

        fuentes_usadas = list({c["fuente"] for c in contextos}) if contextos else []
        if fuentes_usadas:
            print(f"  [RAG] Contexto recuperado de: {', '.join(fuentes_usadas)}")
        else:
            print("  [RAG] Sin contexto en documentos. Usando conocimiento del modelo.")

        # 2. Construir prompt con contexto
        prompt = construir_prompt_rag(pregunta, contextos)

        # 3. Invocar LLM
        respuesta = llm.invoke(prompt)

        contenido = respuesta.content
        # Normalizar espacios Unicode que rompen la consola Windows
        contenido = contenido.replace('\u202f', ' ').replace('\u00a0', ' ')

        # 4. Guardar en historial
        self.historial.append({"rol": "usuario", "contenido": pregunta})
        self.historial.append({"rol": "agente", "contenido": contenido})

        return contenido
