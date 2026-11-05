'use strict';
const $ = selector => document.querySelector(selector);
const state = { report: null, messages: [], filter: 'ALL', status: null, busy: false };
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let toastTimer;
function toast(message) { $('#toast').textContent = message; $('#toast').hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => $('#toast').hidden = true, 6000); }
async function api(path, data) { const response = await fetch(path, data === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}); const type = response.headers.get('content-type') || ''; const result = type.includes('json') ? await response.json() : await response.blob(); if (!response.ok) throw new Error(result.error || 'No se pudo completar la solicitud.'); return result; }
function navigate(page) { document.querySelectorAll('.page').forEach(el => el.hidden = el.id !== `page-${page}`); document.querySelectorAll('.nav-item').forEach(el => el.classList.toggle('active',el.dataset.page === page)); const item = $(`[data-page="${page}"]`); $('#breadcrumb').textContent = item.textContent.trim().slice(2).trim(); if (page === 'history') renderHistory(); }
document.querySelectorAll('.nav-item').forEach(button => button.addEventListener('click', () => navigate(button.dataset.page)));
function count() { $('#char-count').textContent = `${$('#sql-input').value.length.toLocaleString('es-PE')} caracteres`; }
$('#sql-input').addEventListener('input', count);
$('#load-demo').addEventListener('click', () => { if (!state.status) return; $('#sql-input').value = state.status.demo; $('#filename').textContent = 'ejemplo-privacidad.sql'; count(); toast('Esquema de demostración cargado. Puedes editarlo antes de analizar.'); });
$('#sql-file').addEventListener('change', async event => { const file = event.target.files[0]; if (!file) return; try { $('#sql-input').value = await file.text(); $('#filename').textContent = file.name; count(); } catch { toast('No se pudo leer el archivo.'); } event.target.value = ''; });
$('#mode').addEventListener('change', () => { $('#mode-notice').textContent = $('#mode').value === 'ai' ? '◈ El agente elegirá herramientas y enviará esquema y contexto a Groq, o a Gemini si se activa el respaldo. Usa estructura sin registros personales ni secretos reales.' : '◈ El análisis local funciona sin conexión y no envía tu esquema a servicios externos.'; });
$('#run-audit').addEventListener('click', async () => { if (state.busy) return; const button = $('#run-audit'); $('#audit-error').hidden = true; state.busy = true; button.disabled = true; button.innerHTML = '<span>Interpretando esquema y preparando hallazgos…</span><span>◌</span>'; try { const payload = {sql:$('#sql-input').value,mode:$('#mode').value,dialect:$('#dialect').value,objetivo:$('#audit-objective').value}; let report; if(payload.mode === 'ai') { $('#audit-trace-panel').hidden = false; report = await executeAgent({...payload,tarea:'auditoria'}, $('#audit-trace')); } else { $('#audit-trace-panel').hidden = true; report = await api('/api/audit',payload); } showReport(report); toast('Análisis completado. Revisa las evidencias y las recomendaciones.'); } catch (error) { $('#audit-error').textContent = error.message; $('#audit-error').hidden = false; } finally { state.busy = false; button.disabled = false; button.innerHTML = '<span>Analizar privacidad</span><span>↗</span>'; } });
function showReport(report) { state.report = report; state.filter = 'ALL'; $('#finding-search').value = ''; document.querySelectorAll('.filter').forEach(el => el.classList.toggle('active',el.dataset.risk === 'ALL')); $('#metric-tables').textContent = report.tablas.length; $('#metric-high').textContent = report.conteo.ALTO; $('#metric-medium').textContent = report.conteo.MEDIO; $('#metric-total').textContent = report.hallazgos.length; $('#result-summary').textContent = report.resumen_ejecutivo; $('#run-steps').innerHTML = report.pasos.map(step => `<span>✓ ${esc(step)}</span>`).join(''); $('#results').hidden = false; $('#pending-questions').innerHTML = report.preguntas_pendientes?.length ? '<h3>Información pendiente de verificar</h3><ul>' + report.preguntas_pendientes.map(q => `<li>${esc(q)}</li>`).join('') + '</ul>' : ''; if(report.traza) { $('#audit-trace-panel').hidden = false; renderTrace($('#audit-trace'), report.traza); } renderFindings(); $('#results').scrollIntoView({behavior:'smooth',block:'start'}); }
function renderFindings() { if (!state.report) return; const query = $('#finding-search').value.toLowerCase(); const findings = state.report.hallazgos.filter(h => (state.filter === 'ALL' || h.nivel_riesgo === state.filter) && `${h.tabla} ${h.campos_afectados.join(' ')} ${h.descripcion_hallazgo}`.toLowerCase().includes(query)); findings.sort((a,b) => ({ALTO:0,MEDIO:1,BAJO:2}[a.nivel_riesgo] - {ALTO:0,MEDIO:1,BAJO:2}[b.nivel_riesgo])); $('#findings').innerHTML = findings.length ? findings.map(h => `<details class="finding"><summary><span class="risk-badge risk-${esc(h.nivel_riesgo)}">${esc(h.nivel_riesgo)}</span><div class="finding-title"><strong>${esc(h.tabla)}</strong><small>${esc(h.campos_afectados.join(' · '))}</small></div><span>＋</span></summary><div class="finding-body"><p>${esc(h.descripcion_hallazgo)}</p><h4>Evidencia en el esquema</h4><pre>${esc(h.evidencia)}</pre>${(h.referencias || []).map(renderReference).join('')}${[['Riesgo potencial',h.riesgo_potencial],['Información que falta verificar',h.informacion_faltante],['Recomendación',h.recomendacion_mitigacion],['Referencia y alcance',h.criterio_normativo]].map(([label,value]) => `<h4>${label}</h4><p>${esc(value)}</p>`).join('')}</div></details>`).join('') : '<div class="empty-state">No hay observaciones para esta selección.<br>La ausencia de hallazgos no acredita el cumplimiento normativo.</div>'; }
document.querySelectorAll('.filter').forEach(button => button.addEventListener('click',() => { state.filter = button.dataset.risk; document.querySelectorAll('.filter').forEach(el => el.classList.toggle('active',el === button)); renderFindings(); }));
$('#finding-search').addEventListener('input',renderFindings);
function download(blob, name) { const url = URL.createObjectURL(blob); const anchor = document.createElement('a'); anchor.href = url; anchor.download = name; anchor.click(); setTimeout(() => URL.revokeObjectURL(url),1000); }
$('#export-json').addEventListener('click',() => { if (state.report) download(new Blob([JSON.stringify(state.report,null,2)],{type:'application/json'}),'PrivAudit-informe.json'); });
$('#export-pdf').addEventListener('click', async () => { if (!state.report) return; const button = $('#export-pdf'); button.disabled = true; try { download(await api('/api/report',state.report),'PrivAudit-informe.pdf'); } catch (error) { toast(error.message); } finally { button.disabled = false; } });
async function renderHistory(offset = 0) {
  const target = $('#history-list');
  target.textContent = 'Cargando historial…';
  const labels = {auditoria:'Auditoría SQL', consulta:'Consulta EC1', gestitel:'GESTITEL', riesgos:'Agente de riesgos', chat:'Chat de privacidad'};
  try {
    const page = await api(`/api/history?limit=50&offset=${offset}`);
    target.innerHTML = page.items.length ? page.items.map(item => `<article class="panel history-entry"><div><h3>${esc(labels[item.tipo] || item.tipo)} · ${esc(item.estado)}</h3><p>${esc(item.objetivo)}</p><small>${esc(new Date(item.fecha).toLocaleString('es-PE'))}</small></div><button class="secondary-button" data-history-id="${esc(item.id)}">Ver resultado ↗</button></article>`).join('') : '<div class="panel empty-state">Aún no hay consultas guardadas. Las nuevas auditorías y consultas aparecerán aquí.</div>';
    target.insertAdjacentHTML('beforeend', `<p>${page.total} registros guardados</p><button id="history-prev" class="secondary-button" ${offset === 0 ? 'disabled' : ''}>Anterior</button> <button id="history-next" class="secondary-button" ${offset + 50 >= page.total ? 'disabled' : ''}>Siguiente</button><div id="history-detail" class="panel" hidden></div>`);
    $('#history-prev').onclick = () => renderHistory(Math.max(0, offset - 50));
    $('#history-next').onclick = () => renderHistory(offset + 50);
    target.querySelectorAll('[data-history-id]').forEach(button => button.addEventListener('click', async () => {
      try {
        const entry = await api(`/api/history/${encodeURIComponent(button.dataset.historyId)}`);
        const result = entry.resultado;
        if (entry.tipo === 'auditoria' && entry.estado === 'completado') {
          navigate('audit');
          $('#audit-trace-panel').hidden = !result.traza;
          showReport(result);
        } else if (entry.tipo === 'riesgos' && entry.estado === 'completado') {
          navigate('risk');
          $('#risk-trace-panel').hidden = false;
          renderTrace($('#risk-trace'), result.traza || []);
          renderRiskResult(result);
        } else if (entry.tipo === 'chat') {
          navigate('chat');
          $('#messages').innerHTML = '';
          state.messages = [{role:'user',content:entry.objetivo},{role:'assistant',content:result.answer}];
          appendMessage('user',entry.objetivo);
          appendMessage('assistant',result.answer,result.sources || [],result.provider);
        } else if (entry.estado === 'completado') {
          navigate('agent');
          $('#agent-task').value = entry.tipo;
          $('#agent-objective').value = entry.objetivo;
          $('#agent-error').hidden = true;
          $('#consult-trace-panel').hidden = false;
          renderTrace($('#consult-trace'), result.traza || []);
          showAgentResult(result);
        } else {
          const detail = $('#history-detail');
          detail.hidden = false;
          detail.innerHTML = `<h3>${esc(entry.objetivo)}</h3><p>${esc(result.error)}</p><div id="history-error-trace"></div>`;
          renderTrace($('#history-error-trace'), result.traza || []);
          detail.scrollIntoView({behavior:'smooth'});
        }
      } catch (error) { toast(error.message); }
    }));
  } catch (error) { target.textContent = error.message; }
}
function appendMessage(role, text, sources = [], provider = null) { const message = document.createElement('article'); message.className = `message ${role}`; message.innerHTML = `<span class="message-label">${role === 'user' ? 'Tu consulta' : (provider === 'gemini' ? 'PrivAudit · Gemini (respaldo)' : 'PrivAudit · Asistente de privacidad')}</span><p>${esc(text)}</p>`; if (sources.length) { const block = document.createElement('div'); block.className = 'sources'; block.innerHTML = sources.map(source => `<details><summary>▤ ${esc(source.fuente)}${source.pagina ? ` · Página ${esc(source.pagina)}` : ''} · Relevancia ${Number(source.score).toFixed(2)}</summary><p>${esc(source.texto)}</p></details>`).join(''); message.append(block); } $('#messages').append(message); message.scrollIntoView({behavior:'smooth',block:'nearest'}); }
$('#chat-form').addEventListener('submit', async event => { event.preventDefault(); const question = $('#question').value.trim(); if (!question || $('#send-chat').disabled) return; appendMessage('user',question); $('#question').value = ''; $('#send-chat').disabled = true; $('#send-chat').textContent = 'Consultando…'; try { const result = await api('/api/chat',{question,history:state.messages}); appendMessage('assistant',result.answer,result.sources,result.provider); state.messages.push({role:'user',content:question},{role:'assistant',content:result.answer}); } catch(error) { appendMessage('assistant',error.message); } finally { $('#send-chat').disabled = false; $('#send-chat').textContent = 'Enviar ↗'; } });
document.querySelectorAll('[data-question]').forEach(button => button.addEventListener('click',() => { $('#question').value = button.dataset.question; $('#chat-form').requestSubmit(); }));
async function init() { try { state.status = await api('/api/status'); $('#run-agent').disabled = !state.status.ai_ready; $('#run-risk').disabled = !state.status.ai_ready; if(state.status.ai_ready) { $('#mode').value = 'ai'; $('#mode').dispatchEvent(new Event('change')); } $('#connection').textContent = state.status.ai_ready ? (state.status.gemini_fallback ? 'Groq · Respaldo Gemini configurado' : 'Groq configurado · Agente disponible') : 'Análisis local disponible'; if (!state.status.ai_ready) { $('#mode option[value="ai"]').disabled = true; $('#mode option[value="ai"]').textContent = 'IA · Requiere GROQ_API_KEY'; } $('#document-list').innerHTML = state.status.documentos.map(doc => `<article class="panel document-card"><span class="doc-icon">${esc(doc.tipo)}</span><h3>${esc(doc.nombre)}</h3><p>${(doc.bytes/1024).toFixed(1)} KB · ${esc(doc.tipo_fuente || 'Fuente local')}</p><span class="document-state ${doc.indexado ? '' : 'warning'}">${doc.indexado ? `${doc.fragmentos} fragmentos consultables` : esc(doc.aviso || 'Sin texto recuperable')}</span>${sourceLink(doc.url)}</article>`).join(''); } catch(error) { $('#connection').textContent = 'Servidor no disponible'; toast(error.message); } }


function sourceLink(url) {
  if (!url) return '';
  try { const parsed = new URL(url); return parsed.protocol === 'https:' ? `<a href="${esc(parsed.href)}" target="_blank" rel="noopener noreferrer">Abrir fuente original ↗</a>` : ''; } catch { return ''; }
}
function renderReference(ref) { return `<div class="agent-reference"><strong>${esc(ref.fuente)}${ref.pagina ? ` · Página ${esc(ref.pagina)}` : ''}</strong><blockquote>${esc(ref.cita)}</blockquote>${sourceLink(ref.url)}</div>`; }
function renderTrace(target, events) {
  target.innerHTML = events.map(event => `<article class="agent-event ${esc(event.estado)}"><strong>${esc(event.herramienta)} · ${esc(event.estado)}</strong><p>${esc(event.motivo)}</p><p>${esc(event.resultado)}</p><small>${Number(event.segundos).toFixed(1)} s</small></article>`).join('');
}
async function executeAgent(payload, target) {
  target.textContent = 'Iniciando tarea…';
  const run = await api('/api/agent/runs', payload);
  const deadline = Date.now() + 420000;
  while (Date.now() < deadline) {
    const result = await api(`/api/agent/runs/${encodeURIComponent(run.id)}`);
    renderTrace(target, result.traza || []);
    if (result.estado === 'completado') return result.resultado;
    if (result.estado === 'error') throw new Error(result.error);
    await new Promise(resolve => setTimeout(resolve, 1200));
  }
  throw new Error('La espera superó el límite. La tarea conserva su límite de ejecución en el servidor.');
}
$('#agent-example').addEventListener('click', () => { $('#agent-objective').value = 'Según el survey de Xi et al. de EC1, explica los componentes de un agente basado en LLM y propone cómo aplicarlos a una revisión de privacidad con acceso limitado a datos. Distingue la evidencia de tu propuesta.'; });
$('#agent-form').addEventListener('submit', async event => {
  event.preventDefault();
  const button = $('#run-agent');
  if (button.disabled) return;
  button.disabled = true; button.textContent = 'Agente trabajando…';
  $('#agent-error').hidden = true; $('#agent-result').hidden = true; $('#consult-trace-panel').hidden = false;
  try {
    const result = await executeAgent({tarea:$('#agent-task').value, objetivo:$('#agent-objective').value}, $('#consult-trace'));
    showAgentResult(result);
  } catch (error) { $('#agent-error').textContent = error.message; $('#agent-error').hidden = false; }
  finally { button.disabled = false; button.textContent = 'Ejecutar agente ↗'; }
});
function showAgentResult(result) {
    const labels = {respondida:'Consulta documentada',evidencia_insuficiente:'Evidencia insuficiente',fuera_de_alcance:'Consulta fuera del alcance'};
    $('#agent-result').innerHTML = `<h2>${labels[result.estado_respuesta] || 'Resultado'}</h2>` +
      result.conclusiones.map(c => `<article class="agent-conclusion"><strong>${c.tipo === 'propuesta' ? 'Propuesta de diseño' : 'Conclusión con apoyo documental'}</strong><p>${esc(c.afirmacion)}</p>${c.referencias.map(renderReference).join('')}</article>`).join('') +
      (result.limitaciones.length ? '<h3>Alcance y limitaciones</h3><ul>' + result.limitaciones.map(l => `<li>${esc(l)}</li>`).join('') + '</ul>' : '') +
      `<p>${result.turnos} pasos de ejecución · Skills: ${esc(result.skills.join(', '))} · ${esc(result.modelo)}</p><p>Las citas se comprobaron literalmente. Su pertinencia y la interpretación requieren revisión humana.</p>`;
    $('#agent-result').hidden = false;
}
init();

$('#agent-task').addEventListener('change', () => { if ($('#agent-task').value === 'gestitel') $('#agent-objective').value = 'Revisa la primera página de la matriz de brecha de GESTITEL. Identifica evidencia pendiente y propone qué documentos solicitar y qué acciones evaluar. Busca respaldo documental, cita los registros consultados y declara el alcance parcial. No asignes niveles ni confirmes incumplimientos.'; });
