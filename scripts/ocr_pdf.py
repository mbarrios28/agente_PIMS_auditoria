"""OCR reproducible de un PDF escaneado con Poppler y Tesseract; conserva el original."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from pypdf import PdfReader, PdfWriter


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--tessdata',required=True,type=Path)
    parser.add_argument('--languages',default='eng+spa')
    parser.add_argument('--dpi',type=int,default=220)
    parser.add_argument('--workers',type=int,default=4)
    parser.add_argument('--metadata',type=Path)
    args=parser.parse_args()
    if args.source.resolve()==args.output.resolve() or args.output.exists():
        parser.error('Usa una salida nueva; no se sobrescribe el original ni un OCR existente.')
    if not 150<=args.dpi<=400 or not 1<=args.workers<=8:
        parser.error('DPI entre 150 y 400; workers entre 1 y 8.')
    for lang in args.languages.split('+'):
        if not (args.tessdata/(lang+'.traineddata')).is_file():parser.error('Falta el modelo de idioma '+lang)
    count=len(PdfReader(args.source).pages)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='pims-ocr-') as folder:
        temp=Path(folder)
        def process(number):
            prefix=temp/f'page-{number:03}'
            subprocess.run(['pdftoppm','-f',str(number),'-l',str(number),'-r',str(args.dpi),
                            '-gray','-singlefile','-png',str(args.source),str(prefix)],check=True,capture_output=True)
            subprocess.run(['tesseract',str(prefix)+'.png',str(prefix),'--tessdata-dir',str(args.tessdata),
                            '-l',args.languages,'--psm','3','-c','tessedit_create_pdf=1',
                            '-c','tessedit_create_txt=1','-c','tessedit_create_tsv=1'],check=True,capture_output=True,
                            env=dict(os.environ,OMP_THREAD_LIMIT='1'))
            text=prefix.with_suffix('.txt').read_text()
            rows=prefix.with_suffix('.tsv').read_text().splitlines()[1:]
            confidence=[]
            for row in rows:
                parts=row.split('\t')
                if len(parts)>11 and parts[11].strip():
                    try:
                        value=float(parts[10])
                        if value>=0:confidence.append(value)
                    except ValueError:pass
            return dict(pagina_pdf=number,caracteres=len(text.strip()),palabras=len(confidence),
                        confianza_media=round(sum(confidence)/len(confidence),2) if confidence else None)
        pages=[]
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures=[pool.submit(process,n) for n in range(1,count+1)]
            for future in as_completed(futures):
                result=future.result();pages.append(result)
                print(f"OCR {len(pages)}/{count}: página {result['pagina_pdf']}, {result['caracteres']} caracteres",flush=True)
        writer=PdfWriter()
        for n in range(1,count+1):writer.append(str(temp/f'page-{n:03}.pdf'))
        writer.add_metadata({'/Title':args.source.stem+' — derivado OCR','/Subject':'Texto reconocido automáticamente; verificar contra imágenes del original.'})
        with args.output.open('wb') as out:writer.write(out)
        writer.close()
    pages.sort(key=lambda p:p['pagina_pdf'])
    meta=dict(original=args.source.name,sha256_original=sha(args.source),archivo_ocr=args.output.name,
              sha256_ocr=sha(args.output),creado_en=datetime.now(timezone.utc).isoformat(),dpi=args.dpi,
              idiomas=args.languages,tesseract=subprocess.check_output(['tesseract','--version'],text=True).splitlines()[0],
              modelos={l:sha(args.tessdata/(l+'.traineddata')) for l in args.languages.split('+')},
              paginas=pages,advertencia='La confianza OCR no acredita corrección normativa. Verificar las citas contra la imagen original.')
    target=args.metadata or args.output.with_suffix('.ocr.json')
    target.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print('OCR terminado:',args.output,flush=True)

if __name__=='__main__':main()
