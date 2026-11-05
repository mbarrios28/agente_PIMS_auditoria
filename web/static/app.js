'use strict';
const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let toastTimer;
function toast(message) { $('#toast').textContent=message; $('#toast').hidden=false; clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('#toast').hidden=true,6000); }
async function api(path,data) {
  const response=await fetch(path,data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  const result=await response.json();
  if(!response.ok) throw new Error(result.error || 'No se pudo completar la solicitud.');
  return result;
}
function navigate(page) {
  document.querySelectorAll('.page').forEach(el=>el.hidden=el.id!==`page-${page}`);
  document.querySelectorAll('.nav-item').forEach(el=>el.classList.toggle('active',el.dataset.page===page));
  $('#breadcrumb').textContent=page==='risk'?'Agente de riesgos':'Historial de riesgos';
  if(page==='history') renderHistory();
}
document.querySelectorAll('.nav-item').forEach(button=>button.addEventListener('click',()=>navigate(button.dataset.page)));
function download(blob,name) { const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download=name; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000); }
function sourceLink(url) {
  if(!url) return '';
  try { const parsed=new URL(url); return parsed.protocol==='https:'?`<a href="${esc(parsed.href)}" target="_blank" rel="noopener noreferrer">Abrir fuente ↗</a>`:''; } catch { return ''; }
}
function renderReference(ref) { return `<div class="agent-reference"><strong>${esc(ref.fuente)}</strong><blockquote>${esc(ref.cita)}</blockquote>${sourceLink(ref.url)}</div>`; }
function renderTrace(target,events) {
  target.innerHTML=events.map(e=>`<article class="agent-event ${esc(e.estado)}"><strong>${esc(e.herramienta)} · ${esc(e.estado)}</strong><p>${esc(e.motivo)}</p><p>${esc(e.resultado)}</p><small>${Number(e.segundos).toFixed(1)} s</small></article>`).join('');
}
async function executeAgent(payload,target) {
  target.textContent='Iniciando consulta a GESTITEL…';
  const run=await api('/api/agent/runs',payload);
  const deadline=Date.now()+420000;
  while(Date.now()<deadline) {
    const result=await api(`/api/agent/runs/${encodeURIComponent(run.id)}`);
    renderTrace(target,result.traza || []);
    if(result.estado==='completado') return result.resultado;
    if(result.estado==='error') throw new Error(result.error);
    await new Promise(resolve=>setTimeout(resolve,1200));
  }
  throw new Error('Se superó la espera. Consulta el historial para recuperar el resultado.');
}
async function renderHistory(offset=0) {
  const target=$('#history-list'); target.textContent='Cargando historial…';
  try {
    const page=await api(`/api/history?limit=50&offset=${offset}`);
    target.innerHTML=page.items.map(item=>`<article class="panel history-entry"><div><h3>Riesgos · ${esc(item.estado)}</h3><p>${esc(item.objetivo)}</p><small>${esc(new Date(item.fecha).toLocaleString('es-PE'))}</small></div><button class="secondary-button" data-history-id="${esc(item.id)}">Ver resultado ↗</button></article>`).join('') || '<p>Aún no hay evaluaciones guardadas.</p>';
    target.insertAdjacentHTML('beforeend',`<p>${page.total} evaluaciones</p><button id="history-prev" class="secondary-button" ${offset===0?'disabled':''}>Anterior</button> <button id="history-next" class="secondary-button" ${offset+50>=page.total?'disabled':''}>Siguiente</button><div id="history-detail" class="panel" hidden></div>`);
    $('#history-prev').onclick=()=>renderHistory(Math.max(0,offset-50));
    $('#history-next').onclick=()=>renderHistory(offset+50);
    target.querySelectorAll('[data-history-id]').forEach(button=>button.addEventListener('click',async()=>{
      try {
        const entry=await api(`/api/history/${encodeURIComponent(button.dataset.historyId)}`);
        if(entry.estado==='completado') {
          navigate('risk'); $('#risk-objective').value=entry.objetivo;
          $('#risk-error').hidden=true; $('#risk-trace-panel').hidden=false;
          renderTrace($('#risk-trace'),entry.resultado.traza || []); renderRiskResult(entry.resultado);
        } else {
          $('#history-detail').hidden=false;
          $('#history-detail').innerHTML=`<h3>${esc(entry.objetivo)}</h3><p>${esc(entry.resultado.error)}</p><div id="history-error-trace"></div>`;
          renderTrace($('#history-error-trace'),entry.resultado.traza || []);
        }
      } catch(error) { toast(error.message); }
    }));
  } catch(error) { target.textContent=error.message; }
}
async function init() {
  try {
    const status=await api('/api/status');
    $('#run-risk').disabled=!(status.ai_ready && status.gestitel_ready);
    $('#connection').textContent=status.ai_ready && status.gestitel_ready ? 'GESTITEL · Agente configurado' : 'Configura IA y conexión a GESTITEL';
  } catch(error) { $('#connection').textContent='Servidor no disponible'; toast(error.message); }
}
init();
