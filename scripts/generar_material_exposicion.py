"""Exporta arquitectura Graphviz a PDF/PNG y guion a PDF para ensayo.

Dependencias: reportlab, svglib, pymupdf. No consulta GESTITEL ni consume IA.
"""
from html import escape
from pathlib import Path
import re

import pymupdf
from reportlab.graphics import renderPDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from svglib.svglib import svg2rlg

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT / 'docs/entrega_ec2'
ASSETS = DELIVERY / 'assets'
NAVY = colors.HexColor('#163B52')
TEAL = colors.HexColor('#24846B')


def register_fonts():
    fonts = Path('C:/Windows/Fonts')
    if (fonts / 'arial.ttf').is_file():
        pdfmetrics.registerFont(TTFont('Body', str(fonts / 'arial.ttf')))
        pdfmetrics.registerFont(TTFont('BodyBold', str(fonts / 'arialbd.ttf')))
        pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold', italic='Body', boldItalic='BodyBold')
        return 'Body', 'BodyBold'
    return 'Helvetica', 'Helvetica-Bold'


def markup(text):
    text = escape(text)
    text = re.sub(r'`([^`]+)`', r'<font color="#24846B">\1</font>', text)
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)


def diagram():
    drawing = svg2rlg(str(ASSETS / 'arquitectura.svg'))
    renderPDF.drawToFile(drawing, str(ASSETS / 'arquitectura.pdf'))
    doc = pymupdf.open(ASSETS / 'arquitectura.pdf')
    page = doc[0]
    page.get_pixmap(matrix=pymupdf.Matrix(2400 / page.rect.width, 2400 / page.rect.width), alpha=False).save(ASSETS / 'arquitectura.png')
    doc.close()


def guide():
    regular, bold = register_fonts()
    body = ParagraphStyle('body', fontName=regular, fontSize=9.5, leading=14,
                          textColor=NAVY, spaceAfter=7, splitLongWords=False)
    title = ParagraphStyle('title', parent=body, fontName=bold, fontSize=23, leading=28, spaceAfter=12)
    heading = ParagraphStyle('heading', parent=body, fontName=bold, fontSize=13, leading=17,
                             textColor=TEAL, spaceBefore=15, spaceAfter=8, keepWithNext=True)
    cell = ParagraphStyle('cell', parent=body, fontSize=8.2, leading=11, spaceAfter=0)
    flow = []
    lines = (DELIVERY / 'guion_exposicion.md').read_text(encoding='utf-8-sig').splitlines()
    buffer = []

    def flush():
        if buffer:
            flow.append(Paragraph(markup(' '.join(buffer)), body))
            buffer.clear()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('|'):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                values = [v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[:\- ]+', v) for v in values):
                    rows.append([Paragraph(markup(v), cell) for v in values])
                i += 1
            widths = [125, 165, 205] if len(rows[0]) == 3 else [160, 335]
            table = Table(rows, colWidths=widths, repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E7F5F1')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F4F7FA')]),
                ('LINEBELOW', (0, 0), (-1, 0), 0.8, TEAL),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ]))
            flow.extend([table, Spacer(1, 10)])
            continue
        if line.startswith('# '):
            flush()
            flow.extend([Paragraph('GUÍA DE ENSAYO · GRUPO 1', heading), Paragraph(markup(line[2:]), title),
                         Paragraph('Cómo funciona · Con qué funciona · Qué mostrar', body)])
        elif line.startswith('## '):
            flush()
            if any(line.startswith('## ' + start) for start in ('2:15', '5:00', '8:15', '12:00')):
                flow.append(PageBreak())
            flow.append(Paragraph(markup(line[3:]), heading))
        elif line.startswith('- '):
            flush()
            flow.append(Paragraph('• ' + markup(line[2:]), body))
        elif not line:
            flush()
        else:
            buffer.append(line)
        i += 1
    flush()

    def furniture(canvas, doc):
        w, h = A4
        canvas.setStrokeColor(TEAL)
        canvas.setLineWidth(1)
        canvas.line(50, h - 35, w - 50, h - 35)
        canvas.setFont(regular, 8)
        canvas.setFillColor(NAVY)
        canvas.drawString(50, h - 27, 'RIESGO-GESTITEL / ISO/IEC 27701:2025')
        canvas.drawString(50, 28, 'Exposición técnica · 12 min de recorrido + 3 min de preguntas')
        canvas.drawRightString(w - 50, 28, str(doc.page))

    SimpleDocTemplate(str(DELIVERY / 'guia_exposicion.pdf'), pagesize=A4, rightMargin=50,
                      leftMargin=50, topMargin=54, bottomMargin=48,
                      title='Guía de exposición técnica - RIESGO-GESTITEL', author='Grupo 1').build(
                          flow, onFirstPage=furniture, onLaterPages=furniture)


if __name__ == '__main__':
    diagram()
    guide()
    print('Generados: arquitectura.svg/pdf/png y guia_exposicion.pdf')
