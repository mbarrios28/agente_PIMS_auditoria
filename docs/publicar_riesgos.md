# Registro aprobado de propuestas en GESTITEL

La aplicación puede crear riesgos y actualizar sus campos de evaluación en la API de GESTITEL.
El modelo sigue sin disponer de herramientas de escritura: el envío se realiza fuera del ciclo LLM,
con datos persistidos y aprobación explícita del usuario desde la interfaz local.

## Uso

1. Ejecuta una evaluación o abre su resultado desde Historial.
2. En **Registrar en GESTITEL**, selecciona el escenario y crear o actualizar.
3. Para actualizar, indica el ID numérico del riesgo existente. Debe corresponder al mismo activo,
   al período activo y no tener evaluación residual ni estar cerrado o bloqueado.
4. Pulsa **Preparar vista previa**. Este paso solo consulta; no crea ni modifica registros remotos.
5. Revisa campos, planes y datos exactos. En actualización se muestran los valores actuales.
6. Escribe quién autoriza, marca la aprobación y pulsa **Confirmar envío a GESTITEL**.
7. La aplicación confirma por GET el registro devuelto y muestra su código y acceso al panel.

Crear registra un riesgo abierto vinculado al activo. Los controles recuperados y aplicables permiten
crear tratamientos con las acciones propuestas. Acciones, hipótesis, datos faltantes y evidencia a
solicitar se conservan en observaciones. No se afirma que un control esté implementado.
Actualizar cambia únicamente propietario propuesto, amenaza, vulnerabilidad, consecuencia, P/I,
estrategia y observaciones. Conserva activos, planes, estado y período del riesgo existente.
No se permite aceptar riesgo residual, cerrar riesgos o asignarles eficacia mediante este flujo.

## Validaciones y recuperación

- La propuesta y el cálculo provienen del historial; el cliente no envía un payload arbitrario.
- Se comprueban activo, matriz, período, aplicabilidad de controles y, al actualizar, estado del destino.
- La aprobación incluye la huella del payload exacto y una vista previa de hasta diez minutos.
- Antes del envío se vuelven a comprobar las versiones de los datos remotos.
- Se reserva la operación en SQLite antes de escribir; peticiones concurrentes o repetidas no repiten
  la creación del mismo escenario desde esta instancia.
- El marcador `PIMS-RISK:...` permite recuperar una creación si se perdió la confirmación.
- No hay reintentos automáticos de POST/PATCH. Si el resultado es incierto, la interfaz ofrece
  **Comprobar resultado en GESTITEL**, que solo consulta. No se habilita otro envío hasta resolverlo.
- Si aparecen varios registros con el marcador o no se confirma uno, se requiere revisión del
  administrador de GESTITEL. No se borra ningún registro para resolverlo automáticamente.

La comprobación de cambios es previa al PATCH; la API no ha confirmado soporte de ETag o bloqueo
remoto. No garantiza exclusión frente a otros clientes que escriban entre comprobación y actualización.
La idempotencia local no es una garantía global entre varias instalaciones con bases locales distintas.
El nombre de quien autoriza es trazabilidad de una aplicación individual; no autentica identidad ni
sustituye una autorización corporativa. Una instalación compartida requiere autenticación y permisos.

## API local

- `POST /api/history/<id>/gestitel/preview`: `{ "indice": 0 }`, o añade `"riesgo_remoto": 10` para actualizar.
- `POST /api/gestitel/previews/<id>/confirm`: `{ "revisor": "Nombre", "huella": "...", "confirmar": true }`.
- `POST /api/gestitel/previews/<id>/reconcile`: `{}`. Nunca acepta campos para modificar el registro.
- `GET /api/history/<id>` incluye el registro de publicaciones; el PDF también refleja su estado.
- `GET /api/risks/contract`: versión 1.2, publicación limitada a vista previa y confirmación.

Las rutas remotas de escritura están limitadas a `/api/risk-evaluations/` y su detalle por ID.
No se pueden enviar URLs, tokens, SQL ni métodos arbitrarios desde el navegador o desde el modelo.

## Verificación

Se comprobaron permisos declarados y campos con OPTIONS de la API real, el formato usado por su
frontend y una vista previa real del escenario ACT-HW-001. No se ha realizado un POST/PATCH de
riesgos en producción durante esta implementación: el usuario confirma el registro desde la interfaz.
Las pruebas simuladas cubren creación, planes, actualización, aprobación, cambios de versión,
concurrencia, reintentos, confirmaciones perdidas, conciliación y rechazo de payloads arbitrarios.

Verificación de cierre: 58 pruebas correctas, JavaScript válido y checks de UNSAReport sin hallazgos.
También se ejercitó la ruta HTTP de vista previa contra la cuenta real y se rechazó una confirmación
falsa con HTTP 409, sin realizar escritura remota. La hoja EC2 mantiene una página.
