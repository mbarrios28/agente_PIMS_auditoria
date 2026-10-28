"""Descarga explícita de fuentes públicas. No se ejecuta al iniciar ni por el agente."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from pypdf import PdfReader
from io import BytesIO

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'ley_29733_smv_2025.pdf': ('https://www.smv.gob.pe/Uploads/Ley_29733_vigente_2025.pdf', 'SMV, Ley 29733, texto publicado en 2025'),
    'reglamento_016_2024_JUS.pdf': ('https://www3.congreso.gob.pe/Docs/DGP/DIDP/files/ds_016-2024-jus.pdf', 'El Peruano / Congreso, DS 016-2024-JUS'),
    '2309.07864v3.pdf': ('https://arxiv.org/pdf/2309.07864v3', 'Xi et al., 2023, survey de agentes, versión de EC1'),
}

def main():
    manifest = ROOT / 'ISOS/fuentes.json'
    data = json.loads(manifest.read_text()) if manifest.exists() else {}
    for name, (url, title) in SOURCES.items():
        target = ROOT / 'ISOS' / name
        if not target.exists():
            with urlopen(Request(url, headers={'User-Agent': 'PrivAudit-Academic/1.0'}), timeout=90) as response:
                content = response.read(35_000_001)
            if len(content) > 35_000_000 or not content.startswith(b'%PDF'):
                raise ValueError(f'El recurso no es un PDF permitido: {name}')
            PdfReader(BytesIO(content))
            target.write_bytes(content)
        content = target.read_bytes()
        data[name] = {'url': url, 'titulo': title, 'tipo_fuente': 'primaria',
                      'descargado': datetime.now(timezone.utc).isoformat(),
                      'sha256': hashlib.sha256(content).hexdigest(), 'paginas': len(PdfReader(target).pages)}
        manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        print(f'{name}: {data[name]["paginas"]} páginas verificadas')

if __name__ == '__main__':
    main()
