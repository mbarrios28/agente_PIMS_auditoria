'use strict';
let riskReport = null;
$('#risk-form').addEventListener('submit', async event => {
  event.preventDefault();
  const button = $('#run-risk');
  if (button.disabled) return;
  button.disabled = true;
  button.textContent = 'Agente evaluando…';
  $('#risk-error').hidden = true;
  $('#risk-result').hidden = true;
  $('#risk-trace-panel').hidden = false;
  try {
    const result = await executeAgent({tarea:'riesgos', objetivo:$('#risk-objective').value}, $('#risk-trace'));
    renderRiskResult(result);
  } catch (error) {
    $('#risk-error').textContent = error.message;
    $('#risk-error').hidden = false;
  } finally {
    button.disabled = false;
    button.textContent = 'Preparar evaluación de riesgos ↗';
  }
});
function riskList(title, values) {
  return values?.length ? `<h4>${esc(title)}</h4><ul>${values.map(v => `<li>${esc(v)}</li>`).join('')}</ul>` : '';
}
function renderRiskResult(result) {
  riskReport = result;
  const method = result.metodologia;
  $('#risk-result').innerHTML = `<h2>${result.estado_respuesta === 'propuesta' ? 'Propuesta pendiente de revisión' : 'Evidencia insuficiente'}</h2><button class="secondary-button" id="risk-export">↓ Exportar propuesta JSON</button>` +
    (method ? `<p>Metodología: ${esc(method.nombre)} · Versión ${esc(method.version)} · ${esc(method.formula)} · ${esc(method.origen)}</p>` : '<p>Sin metodología recuperada; no se asignaron puntuaciones.</p>') +
    result.riesgos.map(r => `<article class="agent-conclusion"><h3>${esc(r.activo)} · ${esc(r.amenaza)}</h3><p><strong>Vulnerabilidad:</strong> ${esc(r.vulnerabilidad)}</p><p><strong>Consecuencia:</strong> ${esc(r.consecuencia)}</p>` +
      (r.evaluacion ? `<p><strong>Estimación propuesta: ${esc(r.evaluacion.nivel)} (${r.evaluacion.puntaje})</strong> · P=${r.evaluacion.probabilidad} × I=${r.evaluacion.impacto}</p><p>Probabilidad: ${esc(r.evaluacion.justificacion_probabilidad)}</p><p>Impacto: ${esc(r.evaluacion.justificacion_impacto)}</p>` : '<p>Evaluación pendiente de información.</p>') +
      riskList('Supuestos',r.supuestos) + riskList('Información faltante',r.informacion_faltante) +
      `<h4>Tratamiento propuesto · ${esc(r.estrategia)}</h4>` + riskList('Acciones',r.acciones) +
      `<p>Responsable propuesto: ${esc(r.responsable_propuesto)} · Plazo propuesto: ${esc(r.plazo_propuesto)}</p>` +
      riskList('Evidencia a solicitar',r.evidencia_a_solicitar) + `<p>Evaluar EIPD: ${r.requiere_eipd ? 'Sí' : 'No propuesto en esta revisión'} · Riesgo residual pendiente de verificar.</p>` +
      r.referencias.map(renderReference).join('') + (r.controles || []).map(renderReference).join('') + '</article>').join('') +
    riskList('Alcance y limitaciones',result.limitaciones) +
    riskList('Páginas consultadas',result.alcance.map(a => `${a.modulo}, página ${a.pagina}, total ${a.total}, consulta ${a.consultado_en}`)) +
    '<p>El registro en GESTITEL requiere revisar y confirmar una vista previa. No implica aceptación del riesgo residual.</p>';
  if (result.ejecucion_id) $('#risk-result').insertAdjacentHTML('beforeend', renderRiskReview(result) + renderPublicationPanel(result));
  $('#risk-result').hidden = false;
  const reviewForm = $('#risk-review');
  if (reviewForm) reviewForm.onsubmit = submitRiskReview;
  setupPublication();
  $('#risk-export').onclick = () => download(new Blob([JSON.stringify(riskReport,null,2)],{type:'application/json'}),'GESTITEL-propuesta-riesgos.json');
}

function renderRiskReview(result) {
  const events = (result.revisiones || []).map(r => `<p>${esc(r.fecha)} · ${esc(r.reviewer)} · ${esc(r.decision)}<br>${esc(r.comment)}</p>`).join('');
  return `<p><a class="secondary-button" href="/api/risks/report/${encodeURIComponent(result.ejecucion_id)}">↓ Informe PDF</a></p><h3>Revisión humana local</h3>${events}<form id="risk-review"><label for="risk-reviewer">Nombre del revisor</label><input id="risk-reviewer" required minlength="3" maxlength="150"><label for="risk-decision">Resultado de la revisión</label><select id="risk-decision"><option value="revisado">Revisado</option><option value="requiere_cambios">Requiere cambios</option></select><label for="risk-comment">Observaciones</label><textarea id="risk-comment" required minlength="3" maxlength="1500" rows="3"></textarea><p>Este registro local no acepta riesgos ni guarda cambios en GESTITEL.</p><button class="secondary-button" type="submit">Registrar revisión</button></form>`;
}
async function submitRiskReview(event) {
  event.preventDefault();
  const button = event.currentTarget.querySelector('button'); button.disabled = true;
  try {
    await api(`/api/history/${encodeURIComponent(riskReport.ejecucion_id)}/review`, {revisor:$('#risk-reviewer').value,decision:$('#risk-decision').value,comentario:$('#risk-comment').value});
    const entry = await api(`/api/history/${encodeURIComponent(riskReport.ejecucion_id)}`);
    renderRiskResult({...entry.resultado,ejecucion_id:entry.id,revisiones:entry.revisiones,publicaciones:entry.publicaciones}); toast('Revisión registrada.');
  } catch(error) { toast(error.message); button.disabled = false; }
}

let publicationPreview = null;
function renderPublicationPanel(result) {
  if (result.estado_respuesta !== 'propuesta') return '';
  const events = (result.publicaciones || []).map(p => `<article class="agent-reference"><strong>${esc(p.mode)} · ${esc(p.state)}</strong>${p.result ? `<p>Riesgo ${esc(p.result.codigo || p.result.id)} · ${sourceLink(p.result.url)}</p>` : ''}${p.error ? `<p>${esc(p.error)}</p>` : ''}${['sending','uncertain'].includes(p.state) ? `<button class="secondary-button" data-reconcile="${esc(p.id)}">Comprobar resultado en GESTITEL</button>` : ''}</article>`).join('');
  return `<section class="publication"><h3>Registrar en GESTITEL</h3><p>La vista previa consulta el estado actual. El envío requiere tu confirmación y se registra por separado de la evaluación.</p>${events}<form id="publication-form"><label for="publication-risk">Escenario</label><select id="publication-risk">${result.riesgos.map((r,i) => `<option value="${i}">${esc(r.activo)} · ${esc(r.amenaza)}</option>`).join('')}</select><label for="publication-mode">Operación</label><select id="publication-mode"><option value="crear">Crear riesgo</option><option value="actualizar">Actualizar riesgo existente</option></select><label id="publication-target-label" for="publication-target" hidden>ID del riesgo existente en GESTITEL</label><input id="publication-target" type="number" min="1" step="1" hidden><button class="secondary-button" type="submit">Preparar vista previa</button></form><p id="publication-error" class="error" role="alert" hidden></p><div id="publication-preview" hidden></div></section>`;
}
function setupPublication() {
  const form = $('#publication-form'); if (!form) return;
  publicationPreview = null;
  $('#publication-mode').onchange = () => {
    const update = $('#publication-mode').value === 'actualizar';
    $('#publication-target').hidden = !update; $('#publication-target-label').hidden = !update;
    $('#publication-target').required = update;
  };
  form.onsubmit = async event => {
    event.preventDefault(); const button = form.querySelector('button'); button.disabled = true;
    $('#publication-error').hidden = true; $('#publication-preview').hidden = true;
    try {
      const input = {indice:Number($('#publication-risk').value)};
      if ($('#publication-mode').value === 'actualizar') input.riesgo_remoto = Number($('#publication-target').value);
      publicationPreview = await api(`/api/history/${encodeURIComponent(riskReport.ejecucion_id)}/gestitel/preview`, input);
      showPublicationPreview(publicationPreview);
    } catch(error) { $('#publication-error').textContent=error.message; $('#publication-error').hidden=false; }
    finally { button.disabled=false; }
  };
  document.querySelectorAll('[data-reconcile]').forEach(button => button.onclick = async () => {
    button.disabled=true;
    try { await api(`/api/gestitel/previews/${encodeURIComponent(button.dataset.reconcile)}/reconcile`,{}); await reloadRiskPublication(); }
    catch(error) { toast(error.message); button.disabled=false; }
  });
}
function showPublicationPreview(preview) {
  const labels = {risk_owner:'Propietario propuesto',threat:'Amenaza',vulnerability:'Vulnerabilidad',description:'Consecuencia',controlled_probability:'Probabilidad',controlled_impact:'Impacto',response_strategy:'Estrategia'};
  const changes = Object.entries(labels).map(([key,label]) => `<dt>${label}</dt><dd>${preview.actual ? `<span class="previous-value">${esc(preview.actual[key] ?? '—')}</span> → ` : ''}${esc(key === 'response_strategy' ? ({M:'Mitigar',E:'Evitar',T:'Compartir / transferir'}[preview.datos[key]] || preview.datos[key]) : preview.datos[key])}</dd>`).join('');
  $('#publication-preview').innerHTML = `<h4>${preview.accion === 'crear' ? 'Crear un riesgo' : `Actualizar riesgo ${esc(preview.riesgo_remoto)}`}</h4><dl>${changes}</dl><p>${esc(preview.aviso)}</p><details><summary>Ver datos exactos que se enviarán</summary><pre>${esc(JSON.stringify(preview.datos,null,2))}</pre></details><form id="publication-confirm"><label for="publication-reviewer">Nombre de quien autoriza</label><input id="publication-reviewer" minlength="3" maxlength="150" required><label class="confirmation"><input id="publication-approved" type="checkbox" required> Apruebo estos datos y autorizo guardarlos en GESTITEL.</label><button class="primary-button" type="submit">Confirmar envío a GESTITEL</button></form>`;
  $('#publication-preview').hidden = false;
  $('#publication-confirm').onsubmit = async event => {
    event.preventDefault(); const button = event.currentTarget.querySelector('button'); button.disabled = true;
    try {
      const result = await api(`/api/gestitel/previews/${encodeURIComponent(preview.id)}/confirm`, {revisor:$('#publication-reviewer').value,huella:preview.huella,confirmar:$('#publication-approved').checked});
      toast(`Guardado en GESTITEL: ${result.codigo || result.id}`); await reloadRiskPublication();
    } catch(error) { toast(error.message); await reloadRiskPublication(); }
  };
}
async function reloadRiskPublication() {
  const entry = await api(`/api/history/${encodeURIComponent(riskReport.ejecucion_id)}`);
  renderRiskResult({...entry.resultado,ejecucion_id:entry.id,revisiones:entry.revisiones,publicaciones:entry.publicaciones});
}
