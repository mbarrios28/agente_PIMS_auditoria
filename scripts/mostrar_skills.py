"""Demuestra las skills y su carga real sin llamar a IA ni a GESTITEL."""
import argparse
from pathlib import Path
import sys
from typing import get_args

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.priv_audit.agent import LoadSkill, RiskAgent, SKILLS, TOOL_SPECS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--completa', action='store_true', help='Mostrar todas las instrucciones cargadas.')
    args = parser.parse_args()
    allowed = get_args(LoadSkill.__annotations__['nombre'])
    print('SKILLS DEL REPOSITORIO')
    for path in sorted(SKILLS.glob('*.md')):
        print(f"  {path.stem:22} {'ACTIVA' if path.stem in allowed else 'histórica; no habilitada'}")
    agent = RiskAgent()
    print('\nHERRAMIENTAS ANTES DE CARGAR:')
    print('  ' + ', '.join(t['function']['name'] for t in agent.available_tools()))
    result = agent.execute('cargar_skill', dict(motivo='Demostrar carga del procedimiento', nombre=agent.required_skill()))
    print('\nCARGA REAL DESDE ARCHIVO: ' + result['skill'])
    print(result['instrucciones'] if args.completa else '\n'.join(result['instrucciones'].splitlines()[:12]))
    print('\nHERRAMIENTAS DESPUÉS DE CARGAR:')
    print('  ' + ', '.join(t['function']['name'] for t in agent.available_tools()))
    print('\nCATÁLOGO COMPLETO (su disponibilidad depende de la fase):')
    for name in TOOL_SPECS:
        print('  ' + name)
    print('\nDemostración local: no se consultó GESTITEL ni se consumió cuota de IA.')


if __name__ == '__main__':
    main()
