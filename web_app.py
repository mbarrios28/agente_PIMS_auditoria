"""Local web interface. Run: python web_app.py"""
import os
import io
from flask import Flask, jsonify, render_template, request, send_file
from dotenv import load_dotenv
from pathlib import Path
ROOT = Path(__file__).resolve().parent

load_dotenv(ROOT / '.env')
app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
app.config['MAX_CONTENT_LENGTH'] = 1_000_000

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
    from src.priv_audit.gestitel import configured
    return jsonify(ai_ready=bool(os.getenv('GROQ_API_KEY')), gestitel_ready=configured(),
                   documentos=diagnostico_documentos(), modelo=MODEL,
                   gemini_fallback=bool(os.getenv('GEMINI_API_KEY')), agente='riesgos', max_turnos=MAX_TURNS)

@app.post('/api/agent/runs')
def start_agent_run():
    from src.priv_audit.jobs import runs
    from src.priv_audit.risk import RiskInput
    from src.priv_audit.gestitel import configured
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Se esperaba un objeto JSON.'), 400
    if set(data) - {'tarea', 'objetivo', 'riesgos'} or data.get('tarea', 'riesgos') != 'riesgos':
        return jsonify(error='Solo se admite el agente de riesgos con contexto de GESTITEL.'), 400
    objective = data.get('objetivo', '')
    if not isinstance(objective, str) or not 1 <= len(objective.strip()) <= 4000:
        return jsonify(error='Escribe un objetivo de hasta 4 000 caracteres.'), 400
    try:
        risk_input = RiskInput.model_validate(data.get('riesgos', {})).model_dump()
    except ValueError:
        return jsonify(error='El contexto y la metodología se obtienen exclusivamente de GESTITEL.'), 400
    if not os.getenv('GROQ_API_KEY') or not configured():
        return jsonify(error='Configura GROQ_API_KEY y las credenciales de GESTITEL en .env.'), 400
    try:
        key = runs.start(dict(tarea='riesgos', objetivo=objective, risk_input=risk_input))
        return jsonify(id=key, estado='pendiente'), 202
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

@app.get('/api/risks/contract')
def risk_contract():
    from src.priv_audit.risk import RiskInput, FinishRisk
    return jsonify(version='1.1', entrada=RiskInput.model_json_schema(),
                   propuesta=FinishRisk.model_json_schema(), fuente='gestitel',
                   escritura_gestitel=False, autenticacion='Servidor local; requiere gateway autenticado para producción.')

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
    return jsonify(list_entries(limit, offset, kind='riesgos'))

@app.get('/api/history/<entry_id>')
def history_detail(entry_id):
    from src.priv_audit.history import get
    entry = get(entry_id)
    if not entry or entry['tipo'] != 'riesgos':
        return jsonify(error='Registro no encontrado.'), 404
    from src.priv_audit.history import reviews
    return jsonify(dict(entry, revisiones=reviews(entry_id)))

@app.post('/api/history/<entry_id>/review')
def review_risk(entry_id):
    from src.priv_audit.history import review
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) != {'revisor', 'decision', 'comentario'}:
        return jsonify(error='Indica revisor, decisión y comentario.'), 400
    try:
        return jsonify(review(entry_id, data['revisor'], data['decision'], data['comentario'])), 201
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

@app.get('/api/risks/report/<entry_id>')
def risk_pdf(entry_id):
    from src.priv_audit.history import get, reviews
    from src.priv_audit.risk_report import build_pdf
    entry = get(entry_id)
    if not entry or entry['tipo'] != 'riesgos' or entry['estado'] != 'completado':
        return jsonify(error='Evaluación no encontrada.'), 404
    content = build_pdf(entry, reviews(entry_id))
    return send_file(io.BytesIO(content), mimetype='application/pdf', as_attachment=True,
                     download_name='GESTITEL-evaluacion-riesgos.pdf')

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    print(f'Agente de riesgos · Abre http://127.0.0.1:{port}')
    app.run(host='127.0.0.1', port=port, debug=False)
