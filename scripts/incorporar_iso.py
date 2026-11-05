"""Incorpora una copia ISO aportada por el usuario al corpus local, sin descargarla."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pypdf import PdfReader

EDITIONS={'27001':'2022','27002':'2022','27005':'2022','27701':'2025'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--norma',required=True,choices=EDITIONS)
    parser.add_argument('--archivo',required=True,type=Path)
    args=parser.parse_args()
    if args.archivo.suffix.lower()!='.pdf' or not args.archivo.is_file():
        parser.error('Selecciona un PDF existente.')
    reader=PdfReader(args.archivo)
    text=' '.join(page.extract_text() or '' for page in reader.pages)
    if len(text.strip())<500:
        parser.error('PDF sin texto suficiente. Obtén una copia con texto u OCR antes de incorporarlo.')
    if args.norma not in text or EDITIONS[args.norma] not in text:
        parser.error('No se reconoció la norma y edición esperadas; revisa el archivo.')
    filename=f'ISO-IEC-{args.norma}-{EDITIONS[args.norma]}-aportada.pdf'
    target=ROOT/'ISOS'/filename
    if target.exists():
        parser.error('La norma ya está incorporada. Revisa su versión antes de sustituirla.')
    shutil.copyfile(args.archivo,target)
    manifest=ROOT/'ISOS/fuentes.json'
    data=json.loads(manifest.read_text())
    data[filename]=dict(titulo=f'ISO/IEC {args.norma}:{EDITIONS[args.norma]} — copia aportada',
        tipo_fuente='norma_aportada',paginas=len(reader.pages),
        sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        verificacion='Pendiente de contraste humano de edición, integridad y procedencia.')
    manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(f'Incorporada: {filename}. Disponible para búsqueda local. Pendiente contraste humano del contenido.')

if __name__=='__main__':main()
