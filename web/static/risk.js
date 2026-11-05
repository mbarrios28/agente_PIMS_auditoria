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
    '<p>La aprobación corresponde al responsable autorizado. Esta propuesta no se ha guardado en GESTITEL.</p>';
  if (result.ejecucion_id) $('#risk-result').insertAdjacentHTML('beforeend', renderRiskReview(result));
  $('#risk-result').hidden = false;
  const reviewForm = $('#risk-review');
  if (reviewForm) reviewForm.onsubmit = submitRiskReview;
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
    renderRiskResult({...entry.resultado,ejecucion_id:entry.id,revisiones:entry.revisiones}); toast('Revisión registrada.');
  } catch(error) { toast(error.message); button.disabled = false; }
}
