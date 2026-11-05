"""Local web interface. Run: python web_app.py"""
import io
import logging
import os
from pathlib import Path
from flask import Flask, jsonify, render_template, request, send_file
from threading import Lock
from dotenv import load_dotenv
from src.priv_audit.service import audit, ROOT

load_dotenv(ROOT / '.env')
app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
app.config['MAX_CONTENT_LENGTH'] = 1_000_000
index_lock = Lock()

@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
    return response

@app.before_request
def same_origin():
    if request.method == 'POST' and request.headers.get('Origin') not in (None, request.host_url.rstrip('/')):
        return jsonify(error='Origen de la solicitud no permitido.'), 403

@app.errorhandler(413)
def too_large(error):
    return jsonify(error='El archivo o solicitud supera el tamaño permitido.'), 413

@app.get('/')
def index():
    return render_template('index.html')

@app.get('/api/status')
def status():
    from src.priv_audit.rag_loader import diagnostico_documentos
    from src.priv_audit.agent import MODEL, MAX_TURNS
    return jsonify(ai_ready=bool(os.getenv('GROQ_API_KEY')), documentos=diagnostico_documentos(),
                   modelo=MODEL, gemini_fallback=bool(os.getenv('GEMINI_API_KEY')), agente=True, max_turnos=MAX_TURNS,
                   demo=(ROOT / 'web/demo.sql').read_text())

@app.post('/api/agent/runs')
def start_agent_run():
    from src.priv_audit.jobs import runs
    from src.priv_audit.service import parse_schema
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Se esperaba un objeto JSON.'), 400
    if not os.getenv('GROQ_API_KEY'):
        return jsonify(error='Configura GROQ_API_KEY para ejecutar el agente.'), 400
    task = data.get('tarea', 'auditoria')
    objective = data.get('objetivo', '')
    if task not in ('auditoria', 'consulta', 'gestitel', 'riesgos') or not isinstance(objective, str) or len(objective) > 4000:
        return jsonify(error='Indica una tarea válida y un objetivo de hasta 4 000 caracteres.'), 400
    if task in ('consulta', 'gestitel', 'riesgos') and not objective.strip():
        return jsonify(error='Escribe el objetivo de la consulta.'), 400
    risk_input = None
    if task == 'riesgos':
        from src.priv_audit.risk import RiskInput
        try:
            risk_input = RiskInput.model_validate(data.get('riesgos', {})).model_dump()
        except ValueError:
            return jsonify(error='Contexto o metodología de riesgos inválidos. Revisa fuente, escalas y rangos.'), 400
    if task == 'gestitel' or (risk_input and risk_input['fuente'] == 'gestitel'):
        from src.priv_audit.gestitel import configured
        if not configured():
            return jsonify(error='Configura las credenciales de GESTITEL en .env.'), 400
    try:
        if task == 'auditoria':
            parse_schema(data.get('sql'), data.get('dialect', 'mysql'))
        key = runs.start(dict(tarea=task, objetivo=objective, sql=data.get('sql', ''), dialect=data.get('dialect', 'mysql'), risk_input=risk_input))
        return jsonify(id=key, estado='pendiente'), 202
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

@app.get('/api/risks/contract')
def risk_contract():
    from src.priv_audit.risk import RiskInput, FinishRisk, demo_methodology
    return jsonify(version='1.0', entrada=RiskInput.model_json_schema(),
                   propuesta=FinishRisk.model_json_schema(), metodologia_ejemplo=demo_methodology().model_dump(),
                   escritura_gestitel=False, autenticacion='Solo servidor local; requiere gateway autenticado para producción.')

@app.get('/api/agent/runs/<run_id>')
def agent_run_status(run_id):
    from src.priv_audit.jobs import runs
    result = runs.get(run_id)
    return (jsonify(result), 200) if result else (jsonify(error='Ejecución no encontrada o caducada.'), 404)

@app.get('/api/history')
def history_list():
    from src.priv_audit.history import list_entries
    try:
        limit, offset = int(request.args.get('limit', 50)), int(request.args.get('offset', 0))
        if not 1 <= limit <= 100 or offset < 0:
            raise ValueError()
    except ValueError:
        return jsonify(error='Paginación inválida.'), 400
    return jsonify(list_entries(limit, offset))

@app.get('/api/history/<entry_id>')
def history_detail(entry_id):
    from src.priv_audit.history import get
    entry = get(entry_id)
    return (jsonify(entry), 200) if entry else (jsonify(error='Registro no encontrado.'), 404)

@app.post('/api/audit')
def run_audit():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Se esperaba un objeto JSON.'), 400
    try:
        result = audit(data.get('sql'), data.get('mode', 'local'), data.get('dialect', 'mysql'), data.get('objetivo', ''))
        from src.priv_audit.history import save
        save('auditoria', data.get('objetivo') or 'Auditoría SQL', result)
        return jsonify(result)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except Exception:
        logging.exception('Audit failed')
        return jsonify(error='No se pudo completar el análisis. Comprueba la conexión y la configuración de Groq.'), 502

@app.post('/api/chat')
def chat():
    data = request.get_json(silent=True) or {}
    question = data.get('question', '') if isinstance(data, dict) else ''
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 4000:
        return jsonify(error='Escribe una pregunta de hasta 4 000 caracteres.'), 400
    def reply(**result):
        from src.priv_audit.history import save
        save('chat', question, result)
        return jsonify(result)
    try:
        from src.priv_audit.rag_chat import construir_mensajes, respuesta_basica, respuesta_local
        basica = respuesta_basica(question)
        if basica and not os.getenv("GROQ_API_KEY"):
            return reply(answer=basica, sources=[], mode="local")
        # Index is reused; conversation belongs to the browser, never shared globally.
        from src.priv_audit.rag_loader import obtener_retriever
        from src.priv_audit.rag_retriever import Retriever
        with index_lock:
            if not hasattr(app, 'retriever'):
                app.retriever = obtener_retriever()
        contexts = [] if basica else app.retriever.recuperar(question, top_k=5)
        if not os.getenv('GROQ_API_KEY'):
            return reply(answer=respuesta_local(question, contexts), sources=contexts, mode='local')
        from src.priv_audit.llm import llm_chat
        messages = construir_mensajes(question, contexts, data.get('history', []))
        response = llm_chat.invoke(messages)
        return reply(answer=response.content, sources=contexts, mode='ai',
                       provider=getattr(response, 'provider', 'groq'), model=getattr(response, 'model', None))
    except Exception:
        logging.exception('Chat failed')
        return jsonify(error='No se pudo completar la consulta. Revisa los documentos y la conexión con Groq.'), 502

@app.post('/api/report')
def report():
    from src.priv_audit.schemas import InformeAuditoria
    from src.priv_audit.pdf_report import generar_pdf
    from tempfile import TemporaryDirectory
    try:
        data = request.get_json(silent=True)
        validated = InformeAuditoria.model_validate(data)
        with TemporaryDirectory() as temp:
            path = Path(temp) / 'informe.pdf'
            generar_pdf([h.model_dump() for h in validated.hallazgos], validated.resumen_ejecutivo, str(path), False)
            content = path.read_bytes()
        return send_file(io.BytesIO(content), mimetype='application/pdf', as_attachment=True, download_name='PrivAudit-informe.pdf')
    except (ValueError, TypeError):
        return jsonify(error='El informe no tiene una estructura válida.'), 400
    except Exception:
        logging.exception('PDF failed')
        return jsonify(error='No se pudo generar el PDF. Descarga el informe JSON.'), 500

if __name__ == '__main__':
    print('PrivAudit · Abre http://127.0.0.1:5000 en tu navegador')
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)
