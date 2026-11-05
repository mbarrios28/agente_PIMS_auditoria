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
  $('#risk-result').hidden = false;
  $('#risk-export').onclick = () => download(new Blob([JSON.stringify(riskReport,null,2)],{type:'application/json'}),'GESTITEL-propuesta-riesgos.json');
}
