# Verificación final de EC2 — Grupo 1

Fecha: 5 de noviembre de 2026. Esta sección sustituye el diagnóstico de la primera versión.

## Caso autorizado en GESTITEL

Con autorización explícita del usuario se registraron únicamente:

- Proceso `EC2-DEMO`, ID 1: «EC2-DEMO · Matrículas».
- Activo `ACT-HW-001`, ID 1: «EC2-DEMO-001 · Servidor de matrículas de prueba».

Ambos están identificados como ficticios y no contienen datos personales. El activo declara copias
diarias sin acta de restauración y fallos simulados; no son incidentes de la universidad.
No se crearon evaluaciones de riesgo, controles ni tratamientos en GESTITEL. El agente sigue siendo de solo lectura.

## Ejecución real completa

ID persistido: `5b333a75-8168-4cde-b786-56b3a6eabeda`.
Proveedor: Groq, modelo `openai/gpt-oss-120b`. Resultado: `propuesta`, un escenario.
Cinco decisiones del modelo, 61,71 segundos incluyendo pausas de cuota.

1. Cargó la skill de riesgos.
2. Preparó contexto: página 1 de activos, procesos y matriz; seleccionó la matriz activa 4×4.
3. Consultó el control `annex-a-controls:72`, A.8.13, mediante detalle por ID.
4. Calculó una estimación P=3, I=4, puntaje=12 y nivel CRÍTICO, según los rangos recuperados.
5. Entregó una propuesta con referencias reales, hipótesis, información faltante, acciones,
   función responsable, plazo y evidencia a solicitar. El riesgo residual quedó sin asignar.

El resultado original, las fuentes y la traza están en `evidencia_ejecucion.json`; el informe legible
está en `informe_caso_ec2.pdf`. También se recupera desde Historial en la aplicación local.
La ejecución usó API real y modelo real; no es una respuesta preparada ni un cliente simulado.
Las claves y tokens no están incluidos en los archivos de entrega.

## Lectura crítica del resultado

La propuesta es un apoyo, no una decisión aprobada. P=3 es una estimación basada en el ejercicio:
no se recuperó una regla numérica que convierta tres fallos anuales en categoría alta. Del mismo
modo, CID de disponibilidad=4 no demuestra por sí solo impacto de escenario=4; debe justificarse
con las consecuencias del proceso. Los supuestos de la propuesta requieren revisión del responsable.
El tiempo máximo de cuatro horas debe concretarse como objetivo de recuperación (RTO), no
confundirse con todo el SLA. La skill incorpora estas distinciones para las ejecuciones siguientes.

## Comprobaciones técnicas

- 48 pruebas automáticas correctas: ciclo, fases, referencias, matriz, controles, minimización,
  contexto exclusivo GESTITEL, revisión local, PDF con escape de texto y fuentes ISO aportadas.
- Sintaxis de ambos archivos JavaScript correcta.
- Preparación de contexto con páginas fijas y consulta de detalle para limitar tamaño de respuestas.
- Identificadores ofrecidos al modelo limitados a activos, referencias, controles y cálculos recuperados.
- Revisión local con eventos acumulativos y huella del resultado. No es autenticación de identidad
  ni aceptación corporativa; las pruebas de revisión se ejecutan en bases temporales.
- `main.pdf` generado mediante UNSAReport y comprobado con una única página; inspección visual realizada.
- `scripts/preparar_exposicion.py` comprueba configuración, conexión, activos y material de presentación.

## Limitaciones externas y normativa

La aplicación se presenta en PC y consume la API de GESTITEL. No se instala dentro del frontend externo.
Groq puede imponer pausas; el flujo las respeta dentro de su presupuesto. Gemini es un respaldo ante
otros fallos temporales, cuya disponibilidad no puede garantizarse. El ensayo completo registrado terminó con Groq.
Las pruebas anteriores detectaron cuotas, indisponibilidad del respaldo y errores de referencias;
se corrigieron el tamaño de contexto, consultas, identificadores y oferta de herramientas por fase.

Pendiente académico: incorporar las ISO autorizadas y contrastar la correspondencia ya preparada
con sus textos. No se afirma cumplimiento, exhaustividad ni implementación de controles.
El grupo realiza la subida de la hoja a Moodle y la presentación personal.
