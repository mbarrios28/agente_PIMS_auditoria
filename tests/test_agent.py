"""Pruebas del agente único y utilidades de cliente simulado."""
import json
from types import SimpleNamespace
from unittest import TestCase
from src.priv_audit.agent import RiskAgent, tools_for
REASON = {'motivo': 'Comprobar evidencia antes de concluir.'}

def call(name, args):
    return SimpleNamespace(id='call_' + name, function=SimpleNamespace(name=name, arguments=json.dumps(args)),
                           model_dump=lambda: {'id': 'call_' + name, 'type': 'function',
                                               'function': {'name': name, 'arguments': json.dumps(args)}})


def response(tool):
    return SimpleNamespace(usage=SimpleNamespace(prompt_tokens=20, completion_tokens=10),
                           choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=[tool]))])


class AgentScopeTests(TestCase):
    def test_only_risk_agent_is_available(self):
        for task in ('auditoria','consulta','gestitel'):
            with self.assertRaises(ValueError):
                RiskAgent(task=task)
        agent=RiskAgent()
        self.assertEqual([t['function']['name'] for t in agent.available_tools()], ['cargar_skill'])
        agent.execute('cargar_skill',dict(REASON,nombre='gestion_riesgos'))
        self.assertNotIn('calcular_riesgo',[t['function']['name'] for t in agent.available_tools()])
        for name in ('finalizar_consulta','inspeccionar_esquema','consultar_gestitel'):
            with self.assertRaises(ValueError):
                agent.execute(name, REASON)

    def test_manual_context_is_rejected_by_agent(self):
        for data in ({'fuente':'manual'},{'contexto':'No permitido'},{'metodologia':{}}):
            with self.assertRaises(ValueError):
                RiskAgent(risk_input=data)
