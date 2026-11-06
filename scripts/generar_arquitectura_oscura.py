"""Diagrama vectorial de arquitectura con el estilo de la ficha de referencia.

python scripts/generar_arquitectura_oscura.py
Dependencias de exportación: reportlab, svglib y pymupdf.
Iconos de trazo construidos en SVG; sin imágenes externas ni llamadas de red.
"""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/entrega_ec2/assets'
WHITE = '#E7E9EC'
MUTED = '#AEB4BF'

ICONS = {
    'person': '<circle cx="24" cy="9" r="7"/><path d="M10 44V35a14 14 0 0 1 28 0v9"/>',
    'monitor': '<rect x="3" y="5" width="42" height="29" rx="3"/><path d="M24 34v9M14 44h20"/>',
    'file': '<path d="M12 3h18l10 10v32H12zM30 3v11h10M19 23h14M19 30h14M19 37h10"/>',
    'layers': '<path d="m3 13 21-10 21 10-21 10zM3 24l21 10 21-10M3 35l21 10 21-10"/>',
    'brain': '<path d="M24 7c-4-8-15-4-14 3-8-1-11 10-5 14-7 6-3 15 4 15 0 9 12 10 15 3zM24 7c4-8 15-4 14 3 8-1 11 10 5 14 7 6 3 15-4 15 0 9-12 10-15 3zM12 14c5-2 8 3 7 7M9 29c5-3 10 1 9 7M36 14c-5-2-8 3-7 7M39 29c-5-3-10 1-9 7"/>',
    'shield': '<path d="m24 3 18 7v14c0 12-10 19-18 23C16 43 6 36 6 24V10zM15 25l6 6 13-14"/>',
    'list': '<circle cx="5" cy="9" r="2"/><circle cx="5" cy="24" r="2"/><circle cx="5" cy="39" r="2"/><path d="M15 9h30M15 24h30M15 39h30"/>',
    'search': '<circle cx="21" cy="20" r="16"/><path d="m33 33 13 13"/>',
    'database': '<ellipse cx="24" cy="8" rx="20" ry="6"/><path d="M4 8v31c0 9 40 9 40 0V8M4 23c0 9 40 9 40 0"/>',
    'bolt': '<path d="M28 2 6 28h16l-2 18 22-27H26z"/>',
    'refresh': '<path d="M41 17A18 18 0 0 0 9 11L4 18M4 6v12h12M7 31a18 18 0 0 0 32 6l5-7M44 42V30H32"/>',
    'plug': '<path d="M14 2v14M34 2v14M9 16h30v8a15 15 0 0 1-30 0zM24 39v8"/>',
    'wrench': '<path d="M30 5a13 13 0 0 0-15 17L3 35a7 7 0 0 0 10 10l13-13A13 13 0 0 0 43 17l-9 9-12-12z"/>',
    'calc': '<rect x="8" y="2" width="32" height="44" rx="4"/><path d="M14 9h20v9H14zM15 26h4M29 26h4M15 35h4M29 35h4"/>',
    'book': '<path d="M24 9C15 3 7 3 2 6v34c7-3 15-2 22 3 7-5 15-6 22-3V6c-5-3-13-3-22 3zM24 9v34"/>',
}


def build_svg():
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1080" viewBox="0 0 1400 1080" role="img" aria-labelledby="title desc">',
             '<title id="title">RIESGO-GESTITEL · Arquitectura del agente</title>',
             '<desc id="desc">Un revisor usa una interfaz Flask. RiskAgent carga gestion_riesgos, selecciona seis herramientas y consulta ISO 27701:2025 y GESTITEL. SQLite conserva el resultado. Groq es el proveedor principal y Gemini el respaldo.</desc>',
             '<rect width="1400" height="1080" fill="#171717"/>']

    def text(x, y, lines, size=19, color=WHITE, anchor='middle', weight='normal', leading=26):
        if isinstance(lines, str):
            lines = [lines]
        for i, line in enumerate(lines):
            parts.append(f'<text x="{x}" y="{y+i*leading}" fill="{color}" font-family="Helvetica" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{escape(line)}</text>')

    def icon(name, x, y, size=44, color=WHITE):
        parts.append(f'<g transform="translate({x},{y}) scale({size/48})" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>')

    def block(x, y, w, h, color, label, symbol, tab_width):
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#252A2E" stroke="{color}" stroke-width="1.4"/>')
        parts.append(f'<rect x="{x+10}" y="{y+10}" width="{tab_width}" height="31" rx="2" fill="#202325" stroke="{color}" stroke-width="0.8"/>')
        icon(symbol, x+18, y+16, 18)
        text(x+45, y+33, label, 16, anchor='start')

    def path(d, color='#BEC3C8', dashed=False):
        parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"{(" stroke-dasharray="+chr(34)+"6 6"+chr(34)) if dashed else ""}/>')
        # Arrowheads are drawn separately so SVG and PDF retain identical geometry.

    def arrow(x, y, direction='right', color='#BEC3C8'):
        points = {'right': f'{x-9},{y-5} {x},{y} {x-9},{y+5}',
                  'left': f'{x+9},{y-5} {x},{y} {x+9},{y+5}',
                  'down': f'{x-5},{y-9} {x},{y} {x+5},{y-9}',
                  'up': f'{x-5},{y+9} {x},{y} {x+5},{y+9}'}
        parts.append(f'<polyline points="{points[direction]}" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')

    text(48, 52, 'RIESGO-GESTITEL', 27, anchor='start', weight='bold')
    text(48, 81, 'Arquitectura del agente de riesgos de privacidad', 19, MUTED, anchor='start')
    text(1350, 51, 'ISO/IEC 27701:2025', 18, '#B2C69B', anchor='end')
    text(1350, 78, 'Base normativa exclusiva', 15, MUTED, anchor='end')
    parts.append('<path d="M48 105H1352" stroke="#383C40"/>')

    # Contenedores: mismos grupos, pestañas e iconos de la referencia.
    block(390, 315, 360, 420, '#69AD6C', 'AGENT RUNTIME', 'layers', 178)
    block(835, 145, 470, 300, '#5D89C3', 'TOOLS + RAG', 'wrench', 170)
    block(835, 480, 470, 172, '#BC6464', 'MEMORY', 'database', 127)
    block(835, 690, 470, 285, '#A9AF4C', 'SERVICIOS EXTERNOS', 'plug', 255)

    # Usuario y objetivo, equivalentes a las dos entradas del documento original.
    icon('person', 85, 390, 47)
    text(109, 461, ['Revisor humano', 'Revisión y aprobación'], 16)
    icon('file', 85, 620, 47)
    text(109, 694, ['Objetivo de evaluación', 'Delimita la tarea'], 16)
    icon('monitor', 249, 512, 48, '#DE9550')
    text(274, 584, ['Interfaz web local', 'Flask + JavaScript'], 18)

    # Entradas y respuestas, trazadas por canales libres.
    path('M140 415H181Q191 415 191 425V530Q191 539 201 539H246')
    arrow(246, 539)
    path('M140 644H181Q191 644 191 634V555Q191 548 201 548H246')
    arrow(246, 548)
    path('M248 524H213Q206 524 206 517V390Q206 381 197 381H141')
    arrow(141, 381, 'left')
    path('M302 538H390')
    arrow(390, 538)
    arrow(302, 538, 'left')

    # Runtime: orquestación, ciclo, skill y validación, con iconos propios.
    icon('layers', 454, 386, 44)
    text(476, 452, ['Orquestación', 'RunStore', 'ThreadPool'], 16, leading=23)
    icon('brain', 637, 386, 44)
    text(659, 452, ['RiskAgent', 'Ciclo de', 'herramientas'], 16, leading=23)
    icon('book', 454, 527, 44)
    text(476, 593, ['Skill activa', 'gestion_riesgos'], 16)
    icon('shield', 637, 527, 44)
    text(659, 593, ['Validaciones', 'Pydantic · referencias'], 16)
    parts.append('<path d="M416 645H724" stroke="#455A49"/>')
    text(570, 681, '16 decisiones · 300 s', 17, MUTED)
    text(570, 709, 'tool_calls → Python → resultado', 17, MUTED)

    # Herramientas y recuperación normativa.
    icon('list', 910, 213, 43)
    text(932, 278, ['6 herramientas', 'Registro acotado'], 18)
    icon('search', 1162, 213, 43)
    text(1184, 278, ['RAG local', 'TF-IDF o BM25'], 18)
    icon('calc', 914, 321, 37)
    text(968, 340, ['Cálculo P × I en Python', 'Matriz activa de GESTITEL'], 17, anchor='start', leading=24)
    parts.append('<path d="M862 382H1278" stroke="#425364"/>')
    text(1070, 414, 'PDF OCR ISO 27701:2025 · ID + página', 17, '#C2D0E3')

    # Persistencia.
    icon('database', 879, 548, 42)
    text(948, 570, ['Persistencia local · SQLite', 'Resultado · fuentes · traza · revisión'], 18, anchor='start', leading=29)

    # Servicios externos: el modelo y el servidor de evidencia.
    icon('bolt', 939, 756, 40)
    text(959, 817, ['Groq · principal', 'openai/gpt-oss-120b'], 17)
    icon('refresh', 1170, 756, 40)
    text(1190, 817, ['Gemini', 'Respaldo configurable'], 17)
    icon('plug', 1048, 876, 40)
    text(1070, 941, ['API GESTITEL · HTTPS', 'Contexto y matriz · lectura acotada'], 17, leading=23)

    # Conexiones ortogonales, en el mismo sentido que la referencia.
    path('M750 398H785Q795 398 795 388V295Q795 285 805 285H835')
    arrow(835, 285)
    arrow(750, 398, 'left')
    text(779, 255, 'tools', 13, MUTED)
    path('M750 563H835')
    arrow(835, 563)
    arrow(750, 563, 'left')
    path('M750 683H785Q795 683 795 693V839Q795 849 805 849H835')
    arrow(835, 849)
    arrow(750, 683, 'left')
    text(783, 812, 'LLM', 13, MUTED)
    path('M1305 292H1333Q1343 292 1343 302V908Q1343 918 1333 918H1305')
    arrow(1305, 918, 'left')
    text(1359, 605, 'API', 13, MUTED)

    parts.append('<path d="M48 1008H1352" stroke="#383C40"/>')
    text(48, 1041, 'Un agente · una skill activa · seis herramientas', 17, MUTED, anchor='start')
    text(1352, 1041, 'Publicación separada: vista previa + confirmación humana', 16, MUTED, anchor='end')
    parts.append('</svg>')
    return '\n'.join(parts)


def main():
    from reportlab.graphics import renderPDF
    from svglib.svglib import svg2rlg
    import pymupdf
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / 'arquitectura_oscura'
    target.with_suffix('.svg').write_text(build_svg(), encoding='utf-8')
    drawing = svg2rlg(str(target.with_suffix('.svg')))
    renderPDF.drawToFile(drawing, str(target.with_suffix('.pdf')))
    with pymupdf.open(target.with_suffix('.pdf')) as doc:
        doc[0].get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False).save(target.with_suffix('.png'))
    print('Diagrama exportado a SVG, PDF y PNG: ' + str(target))


if __name__ == '__main__':
    main()
