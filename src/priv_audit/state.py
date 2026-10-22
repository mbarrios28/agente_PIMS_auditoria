# src/priv_audit/state.py
from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    esquema_sql: str
    tablas_extraidas: List[str]
    hallazgos: List[dict]
    errores: Optional[str]
    iteraciones: int
    informe_aprobado: bool
    resumen_ejecutivo: str
