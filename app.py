"""Console companion for PrivAudit. The graphical interface is web_app.py."""
import json
from pathlib import Path


def main():
    print('\nPrivAudit · Auditoría de privacidad\n')
    print('1. Auditar un esquema SQL\n2. Chat documental con IA\n3. Abrir interfaz web')
    choice = input('Opción: ').strip()
    if choice == '3':
        from web_app import app
        print('Abre http://127.0.0.1:5000')
        app.run(host='127.0.0.1', port=5000, debug=False)
    elif choice == '2':
        from src.priv_audit.rag_chat import ChatRAG
        agent = ChatRAG()
        while True:
            question = input('\nConsulta (salir para terminar): ').strip()
            if question.lower() in ('salir', 'exit', 'quit'):
                break
            if question:
                print(agent.preguntar(question))
    elif choice == '1':
        from dotenv import load_dotenv
        from src.priv_audit.service import audit, ROOT
        from src.priv_audit.pdf_report import generar_pdf
        load_dotenv(ROOT / '.env')
        path = input('Ruta del archivo SQL (Enter para el ejemplo): ').strip()
        sql = Path(path).read_text(encoding='utf-8-sig') if path else (ROOT / 'web/demo.sql').read_text()
        mode = 'ai' if input('¿Usar IA remota? (s/N): ').strip().lower() == 's' else 'local'
        report = audit(sql, mode)
        print('\n' + report['resumen_ejecutivo'])
        print(json.dumps(report['conteo'], ensure_ascii=False))
        (ROOT / 'informe_auditoria_pims.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
        generar_pdf(report['hallazgos'], report['resumen_ejecutivo'], str(ROOT / 'informe_auditoria_pims.pdf'), False)
    else:
        print('Opción no válida.')

if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as exc:
        print(f'No se pudo completar la operación: {exc}')
    except KeyboardInterrupt:
        print('\nSesión terminada.')
