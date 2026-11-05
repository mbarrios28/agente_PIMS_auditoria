# Guion común de exposición — Grupo 1 — máximo 15 minutos

Nombre: RIESGO-GESTITEL. Integrantes: Barrios Medina Matias Alonso; Carbajal Gonzales Diego Alejandro;
Cari Lipe Paul Andree; Mamani Huarsaya Jorge Luis. Cualquiera debe poder ejecutar este guion.

| Tiempo | Pantalla y explicación |
|---|---|
| 0:00–1:00 | Presentar objetivo: apoyar evaluación y tratamiento de riesgos usando solo contexto de GESTITEL. |
| 1:00–2:30 | Mostrar en GESTITEL proceso EC2-DEMO, activo ACT-HW-001 y matriz activa. Aclarar caso ficticio autorizado, sin datos personales reales. |
| 2:30–3:30 | Mostrar arquitectura: un agente, modelo, skill, herramientas, API y validación Python; explicar ciclo de acciones y resultados. |
| 3:30–7:30 | Ejecutar el objetivo preparado. Mientras espera, explicar recuperación, matriz P×I, control consultado y manejo de pausas por cuota. |
| 7:30–10:00 | Revisar un escenario: activo, amenaza, vulnerabilidad, consecuencia, justificación P/I, control y tratamiento. Abrir una referencia real. |
| 10:00–11:00 | Registrar una revisión con el nombre real del expositor y observación. Aclarar que no acepta riesgo residual ni publica en GESTITEL. |
| 11:00–12:00 | Exportar JSON y PDF; abrir Historial. Mostrar hoja de una página y alcance normativo. |
| 12:00–15:00 | Preguntas. Explicar limitaciones y diferenciar el contenido documentado, lo observado y lo propuesto. |

## Preparación

1. `./iniciar.sh` (o `PORT=5051 ./iniciar.sh`). Abrir la URL del puerto elegido.
2. Comprobar `GET /api/status`: IA y credenciales GESTITEL configuradas.
3. Abrir GESTITEL con la cuenta autorizada. No mostrar `.env`, contraseñas ni tokens en pantalla.
4. Abrir `docs/entrega_ec2/main.pdf` y el informe de la ejecución real disponible en Historial.
5. Ensayar en el equipo de exposición. El agente usa servicios externos: disponer de una ejecución anterior
   permite explicar el resultado si hay una interrupción; identificarla como ejecución guardada, nunca como nueva.

## Objetivo acotado

```text
Evalúa solo ACT-HW-001, caso ficticio EC2-DEMO registrado en GESTITEL.
Prepara el contexto y consulta annex-a-controls con registro_id 72 (A.8.13, ID verificado para esta cuenta).
Propón un único riesgo de indisponibilidad por falla de almacenamiento sin prueba de restauración.
Justifica P e I como estimaciones del ejercicio, calcula el nivel y propone tratamiento y evidencia.
Cita activo y control recuperados. No certifiques cumplimiento ni inventes evidencia.
```

El ID 72 fue observado en esta instalación; comprobarlo si cambia la cuenta o se migra la plataforma.
La búsqueda del catálogo no filtra por código en la versión comprobada: usar detalle por ID.
No es contexto manual: la instrucción identifica el alcance; los hechos se recuperan de la API.

## Respuestas que todos deben conocer

- **¿Es un chatbot?** El modelo elige herramientas, observa respuestas y entrega mediante una función validada.
- **¿Qué es la skill?** Un procedimiento reutilizable del agente; no es otro agente ni texto ISO.
- **¿Dónde obtiene los datos?** Solo de GESTITEL; los documentos locales sirven como respaldo técnico/normativo.
- **¿Por qué P×I?** Está documentada en Anexo 04, páginas PDF 6 y 10; las escalas y rangos se recuperan en vivo.
- **¿El control está implementado?** Un catálogo define el control; la implementación exige evidencia adicional.
- **¿Acepta riesgos?** No. La revisión local es una observación del revisor; la aceptación corporativa queda fuera del alcance.
- **¿Se integra con otros agentes?** No se presupone su existencia. Consume módulos y documenta contratos de intercambio.
- **¿Qué normativa cubre?** Apoya evaluación y propuestas de tratamiento; la tabla distingue apoyo de implementación y marca el contraste ISO pendiente.
- **¿Qué sale del equipo?** Objetivo y fragmentos seleccionados llegan a Groq o Gemini. Credenciales de GESTITEL permanecen en el servidor.
