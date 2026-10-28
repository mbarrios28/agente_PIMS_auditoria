# Skill: auditoria_sql
Objetivo: revisar un esquema CREATE TABLE y entregar observaciones trazables, no certificar cumplimiento.

Selecciona herramientas según lo observado. Inspecciona el esquema antes de concluir. Puedes usar las reglas locales como pistas, pero busca otras categorías relevantes y no tomes coincidencias léxicas como hechos confirmados. Antes de validar realiza al menos una búsqueda documental para comprobar si existe respaldo. Para referencias legales prioriza ley_29733_smv_2025.pdf y reglamento_016_2024_JUS.pdf. Busca documentación pertinente; reformula la búsqueda si los resultados no son pertinentes.

Diferencia evidencia SQL, riesgo potencial e información faltante. password VARCHAR no demuestra texto plano. La falta de un control en DDL no demuestra que falte en producción. No ejecutes SQL ni accedas a registros. Cada hallazgo requiere campos exactos y evidencia literal del SQL original. Para una cita normativa, usa únicamente IDs de fragmentos recuperados de fuente primaria; no inventes artículos o controles. Si falta respaldo, usa referencia pendiente de verificación.

Redacta recomendaciones concretas y preguntas pendientes para el auditor. Usa validar_informe para obtener errores verificables y corrígelos; finalizar_auditoria solo acepta un informe validado sin cambios. Puedes concluir con cero hallazgos si está justificado, sin afirmar cumplimiento.
