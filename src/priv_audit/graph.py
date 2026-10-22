# src/priv_audit/graph.py
from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import nodo_validar, nodo_extraer, nodo_evaluar, nodo_autoevaluar

def decidir_ruta_validacion(state: AgentState) -> str:
    if state.get("errores") is not None:
        return END
    return "extraer"

def decidir_ruta_calidad(state: AgentState) -> str:
    """Esta función decide si damos otra vuelta o si terminamos."""
    aprobado = state.get("informe_aprobado", False)
    intentos = state.get("iteraciones", 0)
    
    if aprobado:
        return END # Todo perfecto, terminamos.
        
    if intentos >= 3:
        print("[Router] 🛑 Límite de 3 intentos alcanzado. Terminando para evitar loop infinito.")
        return END
        
    print("[Router] 🔄 Devolviendo el flujo al nodo de Evaluación para que la IA mejore.")
    return "evaluar" # ¡Aquí ocurre el ciclo (loop)!

workflow = StateGraph(AgentState)

# Añadimos los 4 nodos
workflow.add_node("validar", nodo_validar)
workflow.add_node("extraer", nodo_extraer)
workflow.add_node("evaluar", nodo_evaluar)
workflow.add_node("autoevaluar", nodo_autoevaluar) # NUEVO NODO

# Conectamos las rutas
workflow.add_edge(START, "validar")
workflow.add_conditional_edges("validar", decidir_ruta_validacion)
workflow.add_edge("extraer", "evaluar")
workflow.add_edge("evaluar", "autoevaluar")

# EL BUCLE (LOOP) DEL AGENTE
workflow.add_conditional_edges("autoevaluar", decidir_ruta_calidad)

app_grafo = workflow.compile()