"""Corpus local con procedencia, identificadores y diagnóstico de extracción. Sin OCR."""
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
PUBLIC = {
    'iso_27001_alcance.md': 'https://www.iso.org/standard/27001',
    'iso_27005_alcance.md': 'https://www.iso.org/standard/80585.html',
    'iso_27701_2025.md': 'https://www.iso.org/standard/27701',
    'iso_42001_2023.md': 'https://www.iso.org/standard/42001',
    'ley_29733_peru.md': 'https://www.gob.pe/institucion/anpd/normas-legales/6554453-16-2024-jus',
}

# El resto del corpus se conserva para otros usos, fuera del agente de riesgos.
RISK_NORMATIVE_SOURCE = 'ISO-IEC-27701-2025-OCR.pdf'


def limpiar_texto(texto):
    return re.sub(r'\s+', ' ', texto.replace('\x00', '')).strip()


def chunk_texto(texto, fuente):
    return [{'texto': texto[start:start + CHUNK_SIZE].strip(), 'fuente': fuente}
            for start in range(0, len(texto), CHUNK_SIZE - CHUNK_OVERLAP)
            if texto[start:start + CHUNK_SIZE].strip()]


def cargar_markdown(ruta):
    path = Path(ruta)
    return chunk_texto(limpiar_texto(path.read_text(encoding='utf-8')), path.name)


def cargar_pdf(ruta):
    path = Path(ruta)
    chunks = []
    for number, page in enumerate(PdfReader(path).pages, 1):
        for chunk in chunk_texto(limpiar_texto(page.extract_text() or ''), path.name):
            chunks.append(dict(chunk, pagina=number))
    return chunks


def archivos_corpus():
    return sorted([p for folder in (ROOT / 'ISOS', ROOT / 'src/priv_audit/knowledge')
                   for p in folder.glob('*') if p.suffix.lower() in ('.pdf', '.md')
                   and p.name != 'skill_privacidad.md'])


def _signature():
    paths = archivos_corpus() + [ROOT / 'ISOS/fuentes.json']
    return tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in paths if p.exists())


@lru_cache(maxsize=1)
def _load(signature):
    manifest_path = ROOT / 'ISOS/fuentes.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    chunks, documents = [], []
    for path in archivos_corpus():
        error = None
        info = manifest.get(path.name, {})
        replacement = info.get('sustituido_por')
        replaced = bool(replacement and (path.parent / replacement).is_file())
        try:
            if replaced:
                extracted = []
                error = 'Original conservado. Texto consultable en ' + replacement
            elif path.name == 'Ley Nº 29733.pdf.pdf' and (ROOT / 'ISOS/ley_29733_smv_2025.pdf').exists():
                extracted = []
            else:
                extracted = cargar_pdf(path) if path.suffix.lower() == '.pdf' else cargar_markdown(path)
        except Exception:
            extracted, error = [], 'No se pudo extraer texto de este archivo.'
        historical = path.name == 'Ley Nº 29733.pdf.pdf' and (ROOT / 'ISOS/ley_29733_smv_2025.pdf').exists()
        if historical:
            extracted = []
            error = 'Copia histórica excluida: se consulta el texto SMV y el nuevo reglamento oficial.'
        info = manifest.get(path.name, {})
        url = info.get('url') or PUBLIC.get(path.name)
        if info.get('tipo_fuente') == 'norma_aportada_ocr':
            error = 'Texto OCR: verificar citas y tablas contra la imagen original.'
        kind = info.get('tipo_fuente', 'ficha_publica' if path.name in PUBLIC else 'sin_verificar')
        for index, chunk in enumerate(extracted):
            identity = f"{path.name}:{chunk.get('pagina', 0)}:{index}:{chunk['texto']}"
            chunk.update(id=hashlib.sha256(identity.encode()).hexdigest()[:16], url=url, tipo_fuente=kind)
        chunks.extend(extracted)
        documents.append(dict(nombre=path.name, tipo=path.suffix[1:].upper(), bytes=path.stat().st_size,
                              fragmentos=len(extracted), indexado=bool(extracted), url=url,
                              tipo_fuente=kind, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                              aviso=error or (None if extracted else 'Sin texto extraíble; necesita OCR o una copia con texto.')))
    return chunks, documents


def cargar_base_conocimiento():
    return _load(_signature())[0]


def diagnostico_documentos():
    return _load(_signature())[1]


@lru_cache(maxsize=1)
def _retriever(signature, sources=None):
    from .rag_retriever import Retriever
    chunks = _load(signature)[0]
    if sources is not None:
        chunks = [c for c in chunks if c['fuente'] in sources]
    return Retriever(chunks)


def obtener_retriever(sources=None):
    return _retriever(_signature(), tuple(sorted(sources)) if sources is not None else None)
