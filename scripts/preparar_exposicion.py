"""Verificación de exposición: no modifica GESTITEL ni muestra credenciales."""
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dotenv import load_dotenv
from pypdf import PdfReader
from src.priv_audit.gestitel import GestitelClient, configured


def main():
    load_dotenv(ROOT/'.env')
    checks=dict(ia_configurada=bool(os.getenv('GROQ_API_KEY')),gestitel_configurado=configured())
    pdf=ROOT/'docs/entrega_ec2/main.pdf'
    checks['hoja_una_pagina']=pdf.is_file() and len(PdfReader(pdf).pages)==1
    checks['guion_disponible']=(ROOT/'docs/entrega_ec2/guion_exposicion.md').is_file()
    checks['normas_pendientes']=[] if (ROOT/'ISOS/ISO-IEC-27701-2025-OCR.pdf').is_file() else ['ISO/IEC 27701:2025 con OCR']
    checks['recursos']={}
    if configured():
        client=GestitelClient()
        for module in ('assets','processes','evaluation-matrices'):
            try:
                r=client.read(module,risk=True)
                checks['recursos'][module]=dict(total=r['total'],consultado_en=r['consultado_en'])
            except ValueError as exc:
                checks['recursos'][module]=dict(error=str(exc))
    print(json.dumps(checks,ensure_ascii=False,indent=2))
    return 0 if all(checks[k] for k in ('ia_configurada','gestitel_configurado','hoja_una_pagina','guion_disponible')) and checks['recursos'].get('assets',{}).get('total',0)>0 else 1

if __name__=='__main__':raise SystemExit(main())
