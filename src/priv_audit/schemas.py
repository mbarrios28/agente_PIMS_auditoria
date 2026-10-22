# src/priv_audit/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Literal

class HallazgoAuditoria(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, str_min_length=1, str_max_length=20000)
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
        description="Referencia sustentada en documentos. Si no puede verificarse el artículo o control, indicar explícitamente que está pendiente de verificación."
    )

class InformeAuditoria(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, str_min_length=1, str_max_length=30000)
    hallazgos: List[HallazgoAuditoria] = Field(max_length=300)
    resumen_ejecutivo: str = Field(
        description="Resumen ejecutivo del estado general de privacidad del sistema. Incluir cantidad de hallazgos por nivel de riesgo."
    )
