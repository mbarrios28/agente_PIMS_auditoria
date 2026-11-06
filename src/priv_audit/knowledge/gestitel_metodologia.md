# Metodología documentada de GESTITEL

Fuente técnica del profesor: profesor/Anexo_04_Procedimientos_SQL_y_Scripts.pdf, páginas PDF 6 y 10.
El método RiskEvaluation._compute_controlled multiplica controlled_probability por controlled_impact
usando Decimal y conserva dos decimales. resolve_severity redondea con ROUND_HALF_UP y compara
con las bandas de la matriz activa. Para entradas enteras P e I el producto también es entero.
El Anexo 02 (Diccionario de Datos) describe las escalas de entrada y los campos de riesgo.
Estos anexos documentan una versión de GESTITEL; no prueban qué código está instalado en producción.
El agente recupera la matriz actual y calcula propuestas con esa fórmula documentada. No asigna
aceptación de riesgo ni riesgo residual por el solo hecho de recomendar un control.
No son una fuente normativa ISO ni un certificado de cumplimiento.
