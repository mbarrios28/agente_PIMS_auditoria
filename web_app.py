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
    files = []
    for folder in (ROOT / 'ISOS', ROOT / 'src/priv_audit/knowledge'):
        for path in sorted(folder.glob('*')):
            if path.suffix.lower() in ('.md', '.pdf'):
                files.append(dict(nombre=path.name, tipo=path.suffix[1:].upper(), bytes=path.stat().st_size))
    return jsonify(ai_ready=bool(os.getenv('GROQ_API_KEY')), documentos=files,
                   demo=(ROOT / 'web/demo.sql').read_text())

@app.post('/api/audit')
def run_audit():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Se esperaba un objeto JSON.'), 400
    try:
        return jsonify(audit(data.get('sql'), data.get('mode', 'local'), data.get('dialect', 'mysql')))
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
    try:
        from src.priv_audit.rag_chat import construir_mensajes, respuesta_basica, respuesta_local
        basica = respuesta_basica(question)
        if basica and not os.getenv("GROQ_API_KEY"):
            return jsonify(answer=basica, sources=[], mode="local")
        # Index is reused; conversation belongs to the browser, never shared globally.
        from src.priv_audit.rag_loader import cargar_base_conocimiento
        from src.priv_audit.rag_retriever import Retriever
        with index_lock:
            if not hasattr(app, 'retriever'):
                app.retriever = Retriever(cargar_base_conocimiento())
        contexts = [] if basica else app.retriever.recuperar(question, top_k=5)
        if not os.getenv('GROQ_API_KEY'):
            return jsonify(answer=respuesta_local(question, contexts), sources=contexts, mode='local')
        from src.priv_audit.llm import llm_chat
        messages = construir_mensajes(question, contexts, data.get('history', []))
        return jsonify(answer=llm_chat.invoke(messages).content, sources=contexts, mode='ai')
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
