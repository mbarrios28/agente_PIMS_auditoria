# Verificación del agente de riesgos

## Ajuste de alcance: fuente exclusiva GESTITEL

La versión actual elimina el contexto manual y las tareas de SQL, chat y EC1 de los puntos de entrada.
Se actualizó la suite para probar rechazos por API y agente, contexto remoto simulado, cálculo con
matriz recuperada, historial filtrado y respaldo del proveedor. Los casos ficticios son fixtures de
pruebas del conector, nunca opciones de la aplicación. La interfaz abre directamente el agente de riesgos.

Suite actual: 39 pruebas correctas, adaptadas al único agente disponible. Sintaxis JavaScript
correcta y comprobación HTTP real de que la aplicación no muestra campos manuales y rechaza
una solicitud de contexto manual con HTTP 400. Los recuentos siguientes son históricos.

Lo siguiente documenta los ensayos de la primera versión; los intentos manuales son antecedentes
anteriores a la eliminación de esa función y no son instrucciones de uso actuales.


Comprobaciones realizadas el 5 de noviembre de 2026.

## Automatizadas

68 pruebas del proyecto pasan, incluidas pruebas de riesgos sobre cálculo y rangos, referencias,
controles recuperados, matriz remota, correspondencia entre activo y referencia, aislamiento de
herramientas, contratos HTTP y ciclo con cliente simulado que corrige una acción inválida.
Se comprobaron también sintaxis JavaScript con `node --check`, respuesta HTTP de la página,
script de la interfaz y contrato JSON. No se hizo una prueba visual completa en navegador.

## GESTITEL real

Se autenticó con las credenciales del entorno, sin mostrarlas ni incorporarlas al repositorio.
Se verificaron los endpoints `/api/evaluation-matrices/` y `/api/risk-evaluations/`.
Había tres matrices, una activa 4×4 con rangos 1–3, 4–7, 8–11 y 12–16; cero evaluaciones de riesgo.

Una ejecución real del nuevo agente con Groq terminó en cuatro decisiones: cargó la skill,
consultó activos y matrices y finalizó con `evidencia_insuficiente`, cero riesgos y la metodología
recuperada. No inventó activos ni guardó cambios remotos. Es una prueba del camino de falta de
contexto, no de la calidad de una evaluación completa sobre activos reales.

## Caso ficticio con proveedor real

Se ensayó el caso manual dos veces. El primer intento alcanzó búsqueda documental y falló en el
proveedor de respaldo con HTTP 503. El segundo incluyó acciones rechazadas por validación y terminó
con fallo de conexión/disponibilidad del respaldo. Ninguno entregó una propuesta completa.
Se restringió después la oferta de herramientas: el contexto manual no ofrece la consulta remota,
y la ejecución remota no ofrece cálculo hasta disponer de matriz. Estos filtros están probados localmente;
no se atribuye a esta mejora una ejecución real manual exitosa.

El flujo de propuestas y cálculos está probado con clientes simulados. Sigue pendiente completar un
ensayo manual con proveedor disponible y revisar la pertinencia de sus resultados con el profesor.
No se incluyen registros personales de producción ni claves en esta documentación.

## Integración pendiente

No se dispone del código fuente de GESTITEL. Esta entrega no está instalada en su página,
no escribe propuestas en su base de datos ni se comunica con agentes de otros equipos.
El contrato, las dependencias y los requisitos para el adaptador están en `agente_riesgos.md`.
