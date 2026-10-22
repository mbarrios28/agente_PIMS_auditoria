# src/priv_audit/rag_loader.py
"""
Carga y fragmenta los documentos de conocimiento:
- skill_privacidad.md
- PDFs en la carpeta ISOS/
Devuelve una lista de chunks con metadatos.
"""
import os
import re
from pypdf import PdfReader

CHUNK_SIZE = 800      # caracteres por chunk
CHUNK_OVERLAP = 150   # solapamiento entre chunks


def limpiar_texto(texto: str) -> str:
    texto = re.sub(r'\s+', ' ', texto)
    texto = texto.replace('\x00', '')
    return texto.strip()


def chunk_texto(texto: str, fuente: str) -> list[dict]:
    chunks = []
    inicio = 0
    while inicio < len(texto):
        fin = inicio + CHUNK_SIZE
        fragmento = texto[inicio:fin]
        if fragmento.strip():
            chunks.append({
                "texto": fragmento.strip(),
                "fuente": fuente,
            })
        inicio += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def cargar_markdown(ruta: str) -> list[dict]:
    with open(ruta, "r", encoding="utf-8") as f:
        contenido = f.read()
    nombre = os.path.basename(ruta)
    return chunk_texto(limpiar_texto(contenido), nombre)


def cargar_pdf(ruta: str) -> list[dict]:
    nombre = os.path.basename(ruta)
    try:
        reader = PdfReader(ruta)
        chunks = []
        for numero, page in enumerate(reader.pages, 1):
            texto = limpiar_texto(page.extract_text() or "")
            for fragmento in chunk_texto(texto, nombre):
                fragmento["pagina"] = numero
                chunks.append(fragmento)
        return chunks
    except Exception as e:
        print(f"[RAG Loader] Advertencia: no se pudo leer {nombre}: {e}")
        return []


def cargar_base_conocimiento() -> list[dict]:
    """Carga todos los documentos de conocimiento disponibles."""
    chunks = []
    base = os.path.dirname(__file__)
    raiz_proyecto = os.path.join(base, "..", "..")

    # 1. Todos los Markdown de la carpeta knowledge/
    carpeta_knowledge = os.path.join(base, "knowledge")
    if os.path.isdir(carpeta_knowledge):
        for archivo in sorted(os.listdir(carpeta_knowledge)):
            if archivo.lower().endswith(".md"):
                ruta_md = os.path.join(carpeta_knowledge, archivo)
                c = cargar_markdown(ruta_md)
                chunks.extend(c)
                print(f"[RAG Loader] {archivo} -> {len(c)} chunks")

    # 2. PDFs de la carpeta ISOS/
    carpeta_isos = os.path.join(raiz_proyecto, "ISOS")
    carpeta_isos = os.path.normpath(carpeta_isos)
    if os.path.isdir(carpeta_isos):
        for archivo in os.listdir(carpeta_isos):
            if archivo.lower().endswith(".pdf"):
                ruta_pdf = os.path.join(carpeta_isos, archivo)
                c = cargar_pdf(ruta_pdf)
                chunks.extend(c)
                print(f"[RAG Loader] {archivo} -> {len(c)} chunks")
    else:
        print(f"[RAG Loader] Carpeta ISOS no encontrada en: {carpeta_isos}")

    print(f"[RAG Loader] Base de conocimiento lista: {len(chunks)} chunks totales.")
    return chunks
