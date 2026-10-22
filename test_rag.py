import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, '.')
from src.priv_audit.rag_chat import ChatRAG

agente = ChatRAG()
preguntas = [
    "Que dice la ISO 27701 sobre la minimizacion de datos?",
    "Cuales son los datos sensibles segun la Ley 29733?",
    "Que controles de seguridad aplican a contrasenas en bases de datos?"
]
for p in preguntas:
    print(f"\nConsulta: {p}")
    print("-" * 50)
    r = agente.preguntar(p)
    print(r)
    print()
