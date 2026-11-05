"""Ensayo real del caso autorizado EC2-DEMO; consulta GESTITEL y consume cuota de IA."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dotenv import load_dotenv
from src.priv_audit.agent import RiskAgent
from src.priv_audit import history

OBJECTIVE=('Evalúa solo ACT-HW-001, caso ficticio EC2-DEMO registrado en GESTITEL. '
 'Prepara el contexto y consulta annex-a-controls con registro_id 72. '
 'Propón un único riesgo de indisponibilidad por falla de almacenamiento sin prueba de restauración. '
 'Justifica P e I como estimaciones del ejercicio y calcula una vez. '
 'Finaliza copiando exactamente el código del activo, los IDs de referencia y calculo_id ofrecidos por las herramientas. '
 'Incluye control recuperado, acciones y evidencia a solicitar. No busques textos ISO aún no incorporados ni certifiques cumplimiento.')

def main():
    load_dotenv(ROOT/'.env')
    agent=RiskAgent(objective=OBJECTIVE,on_event=lambda e:print(e['herramienta'],e['estado'],e['resultado'][:250],flush=True))
    try:
        result=agent.run()
    except ValueError as exc:
        history.save('riesgos',OBJECTIVE,dict(error=str(exc),traza=agent.trace),status='error')
        print('ERROR:',str(exc),flush=True)
        return 1
    key=history.save('riesgos',OBJECTIVE,result)
    target=ROOT/'data/ejecucion_ec2.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(dict(id=key,resultado=result),ensure_ascii=False,indent=2))
    print('RESULTADO',key,result['estado_respuesta'],len(result['riesgos']),result['turnos'],flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
