"""Prueba real optativa: consume cuota de Groq. Nunca muestra la API key."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
from src.priv_audit.agent import PrivacyAgent
from src.priv_audit.service import audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tarea', choices=['consulta', 'auditoria'])
    parser.add_argument('--salida', type=Path, help='Guardar resultado JSON; puede contener el SQL y fragmentos de la tarea.')
    args = parser.parse_args()
    load_dotenv(ROOT / '.env')
    def event(e):
        print(f"{e['segundos']:6.1f}s · {e['herramienta']} · {e['estado']} · {e['resultado']}", flush=True)
    if args.tarea == 'consulta':
        result = PrivacyAgent(task='consulta', objective='Según Xi et al., ¿cuáles son los tres componentes generales de un agente LLM? Respuesta breve.', on_event=event).run()
        print(result['estado_respuesta'])
    else:
        result = audit((ROOT / 'web/demo.sql').read_text(), 'ai', objective='Revisa las seis tablas y agrupa observaciones para preparar un informe breve. Distingue riesgo e información faltante.', on_event=event)
        print(result['conteo'])
    if args.salida:
        args.salida.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print('Pasos:', result['turnos'], 'Uso:', result['uso'])

if __name__ == '__main__':
    main()
