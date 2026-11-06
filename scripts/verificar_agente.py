"""Prueba real optativa: consume cuota de Groq. Nunca muestra la API key."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
from src.priv_audit.agent import RiskAgent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tarea', choices=['riesgos'], nargs='?', default='riesgos')
    parser.add_argument('--salida', type=Path, help='Guardar resultado JSON; puede contener registros recuperados de GESTITEL.')
    args = parser.parse_args()
    load_dotenv(ROOT / '.env')
    def event(e):
        print(f"{e['segundos']:6.1f}s · {e['herramienta']} · {e['estado']} · {e['resultado']}", flush=True)
    result = RiskAgent(objective='Consulta activos y matriz activa. Propón riesgos con referencias; si faltan activos, declara evidencia insuficiente.', on_event=event).run()
    print(result['estado_respuesta'])
    if args.salida:
        args.salida.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print('Pasos:', result['turnos'], 'Uso:', result['uso'])

if __name__ == '__main__':
    main()
