"""PDF de una evaluación persistida, con referencias y revisiones locales."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def build_pdf(entry, reviews):
    output = BytesIO()
    styles = getSampleStyleSheet()
    styles['BodyText'].fontSize = 9
    styles['BodyText'].leading = 13
    styles['BodyText'].alignment = TA_LEFT
    story = []
    def paragraph(value, style='BodyText'):
        story.append(Paragraph(escape(str(value)).replace('\n', '<br/>'), styles[style]))
        story.append(Spacer(1, 5))
    paragraph('GESTITEL · Evaluación de riesgos', 'Title')
    paragraph(f"Ejecución: {entry['id']} · {entry['fecha']}")
    paragraph(entry['objetivo'])
    result = entry['resultado']
    paragraph(f"Resultado: {result['estado_respuesta']} · Contexto: GESTITEL")
    method = result.get('metodologia')
    if method:
        paragraph(f"Matriz: {method['nombre']} · Versión {method['version']} · Fórmula {method['formula']}")
    for risk in result['riesgos']:
        paragraph(f"{risk['activo']} — {risk['amenaza']}", 'Heading2')
        for field in ('vulnerabilidad', 'consecuencia', 'estrategia', 'responsable_propuesto', 'plazo_propuesto'):
            paragraph(f"{field.replace('_', ' ').capitalize()}: {risk[field]}")
        evaluation = risk.get('evaluacion')
        if evaluation:
            paragraph(f"Estimación propuesta: P={evaluation['probabilidad']} × I={evaluation['impacto']} = {evaluation['puntaje']} ({evaluation['nivel']})")
            paragraph(evaluation['justificacion_probabilidad'])
            paragraph(evaluation['justificacion_impacto'])
        for field in ('supuestos', 'informacion_faltante', 'acciones', 'evidencia_a_solicitar'):
            paragraph(field.replace('_', ' ').capitalize(), 'Heading3')
            for value in risk[field]:
                paragraph('• ' + value)
        paragraph('Referencias recuperadas', 'Heading3')
        for ref in risk['referencias'] + risk.get('controles', []):
            paragraph(ref['fuente'])
            paragraph(ref['cita'])
    paragraph('Alcance y limitaciones', 'Heading2')
    for item in result.get('alcance', []):
        paragraph(f"{item['modulo']} · página {item['pagina']} · búsqueda {item.get('busqueda') or 'sin filtro'} · {item['consultado_en']}")
    for value in result['limitaciones']:
        paragraph('• ' + value)
    paragraph('Revisión humana local', 'Heading2')
    if not reviews:
        paragraph('Pendiente de revisión.')
    for event in reviews:
        paragraph(f"{event['fecha']} · {event['reviewer']} · {event['decision']}")
        paragraph(event['comment'])
        paragraph('Huella de la evaluación: ' + event['result_hash'])
    paragraph('La revisión local no acepta riesgo residual ni guarda cambios en GESTITEL.')
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    def footer(canvas, document):
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#50606c'))
        canvas.drawString(42, 24, 'Grupo 1 · Agente de riesgos · Propuesta para revisión humana')
        canvas.drawRightString(A4[0]-42, 24, str(document.page))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
