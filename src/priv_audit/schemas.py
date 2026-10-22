# src/priv_audit/schemas.py
from pydantic import BaseModel, Field
from typing import List, Literal

class HallazgoAuditoria(BaseModel):
    tabla: str = Field(
        description="Nombre de la tabla analizada."
    )
    campos_afectados: List[str] = Field(
        description="Lista de campos exactos que contienen o podrian contener datos personales."
    )
    descripcion_hallazgo: str = Field(
        description="Descripcion objetiva y formal del hallazgo identificado en el esquema."
    )
    evidencia: str = Field(
        description="Fragmento exacto del esquema SQL que sustenta este hallazgo."
    )
    nivel_riesgo: Literal["ALTO", "MEDIO", "BAJO"] = Field(
        description="Nivel de riesgo segun la escala: ALTO, MEDIO o BAJO."
    )
    riesgo_potencial: str = Field(
        description="Descripcion del impacto potencial sobre la privacidad del titular del dato. Diferenciar que es potencial, no un hecho confirmado."
    )
    informacion_faltante: str = Field(
        description="Informacion adicional que se requiere del responsable del sistema para emitir una conclusion definitiva."
    )
    recomendacion_mitigacion: str = Field(
        description="Medida tecnica u organizativa concreta recomendada para mitigar el riesgo."
    )
    criterio_normativo: str = Field(
        description="OBLIGATORIO: Citar explicitamente la norma que aplica. Ejemplo: 'ISO 27701:2025, control 8.3 - Minimizacion de datos' o 'Ley 29733, Art. 13 - Datos sensibles'."
    )

class InformeAuditoria(BaseModel):
    hallazgos: List[HallazgoAuditoria]
    resumen_ejecutivo: str = Field(
        description="Resumen ejecutivo del estado general de privacidad del sistema. Incluir cantidad de hallazgos por nivel de riesgo."
    )
