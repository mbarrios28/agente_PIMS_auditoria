# src/priv_audit/pdf_report.py
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from datetime import datetime
import os


COLORES = {
    "ALTO":  colors.HexColor("#C0392B"),
    "MEDIO": colors.HexColor("#D4A017"),
    "BAJO":  colors.HexColor("#1A7A4A"),
    "encabezado": colors.HexColor("#1B2A4A"),
    "subencabezado": colors.HexColor("#2C3E6B"),
    "fila_par": colors.HexColor("#F2F4F8"),
    "borde": colors.HexColor("#CCCCCC"),
}


def construir_estilos():
    base = getSampleStyleSheet()

    estilos = {
        "titulo": ParagraphStyle(
            "titulo",
            parent=base["Title"],
            fontSize=18,
            textColor=COLORES["encabezado"],
            spaceAfter=4,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
        ),
        "subtitulo": ParagraphStyle(
            "subtitulo",
            parent=base["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#555555"),
            spaceAfter=2,
            alignment=TA_CENTER,
        ),
        "seccion": ParagraphStyle(
            "seccion",
            parent=base["Heading2"],
            fontSize=12,
            textColor=COLORES["subencabezado"],
            spaceBefore=14,
            spaceAfter=6,
            fontName="Helvetica-Bold",
            borderPad=2,
        ),
        "campo_label": ParagraphStyle(
            "campo_label",
            parent=base["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#444444"),
            fontName="Helvetica-Bold",
            spaceAfter=1,
        ),
        "campo_valor": ParagraphStyle(
            "campo_valor",
            parent=base["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#222222"),
            fontName="Helvetica",
            spaceAfter=5,
            alignment=TA_JUSTIFY,
        ),
        "normal": ParagraphStyle(
            "normal",
            parent=base["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#222222"),
            fontName="Helvetica",
            spaceAfter=4,
            alignment=TA_JUSTIFY,
        ),
        "resumen": ParagraphStyle(
            "resumen",
            parent=base["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#111111"),
            fontName="Helvetica",
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            leftIndent=10,
        ),
        "pie": ParagraphStyle(
            "pie",
            parent=base["Normal"],
            fontSize=7,
            textColor=colors.HexColor("#888888"),
            alignment=TA_CENTER,
        ),
    }
    return estilos


def badge_riesgo(nivel: str, estilos: dict):
    color = COLORES.get(nivel, colors.grey)
    data = [[Paragraph(f"<font color='white'><b>  {nivel}  </b></font>", estilos["campo_valor"])]]
    tabla = Table(data, colWidths=[2.2 * cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROUNDEDCORNERS", [3, 3, 3, 3]),
    ]))
    return tabla


def tabla_resumen_riesgos(hallazgos: list, estilos: dict):
    alto = sum(1 for h in hallazgos if h.get("nivel_riesgo") == "ALTO")
    medio = sum(1 for h in hallazgos if h.get("nivel_riesgo") == "MEDIO")
    bajo = sum(1 for h in hallazgos if h.get("nivel_riesgo") == "BAJO")

    encabezados = [
        Paragraph("<b>Nivel</b>", estilos["campo_label"]),
        Paragraph("<b>Cantidad</b>", estilos["campo_label"]),
        Paragraph("<b>Descripcion</b>", estilos["campo_label"]),
    ]
    filas = [
        encabezados,
        [
            Paragraph("ALTO", estilos["campo_valor"]),
            Paragraph(str(alto), estilos["campo_valor"]),
            Paragraph("Requiere accion inmediata. Incumplimiento normativo directo.", estilos["campo_valor"]),
        ],
        [
            Paragraph("MEDIO", estilos["campo_valor"]),
            Paragraph(str(medio), estilos["campo_valor"]),
            Paragraph("Controles parciales. Debe subsanarse antes de la siguiente auditoria.", estilos["campo_valor"]),
        ],
        [
            Paragraph("BAJO", estilos["campo_valor"]),
            Paragraph(str(bajo), estilos["campo_valor"]),
            Paragraph("Oportunidades de mejora identificadas.", estilos["campo_valor"]),
        ],
    ]

    t = Table(filas, colWidths=[3 * cm, 2.5 * cm, 10 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLORES["encabezado"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLORES["fila_par"]]),
        ("GRID", (0, 0), (-1, -1), 0.4, COLORES["borde"]),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def bloque_hallazgo(hallazgo: dict, numero: int, estilos: dict, ancho: float):
    nivel = hallazgo.get("nivel_riesgo", "BAJO")
    color_borde = COLORES.get(nivel, colors.grey)
    campos = ", ".join(hallazgo.get("campos_afectados", []))

    def fila(label, valor):
        return [
            Paragraph(label, estilos["campo_label"]),
            Paragraph(str(valor) if valor else "No especificado.", estilos["campo_valor"]),
        ]

    datos = [
        [
            Paragraph(f"Hallazgo {numero} — Tabla: {hallazgo.get('tabla', 'N/A')}", estilos["campo_label"]),
            badge_riesgo(nivel, estilos),
        ],
        fila("Campos afectados:", campos),
        fila("Descripcion:", hallazgo.get("descripcion_hallazgo", "")),
        fila("Evidencia en el esquema:", hallazgo.get("evidencia", "")),
        fila("Riesgo potencial:", hallazgo.get("riesgo_potencial", "")),
        fila("Informacion adicional requerida:", hallazgo.get("informacion_faltante", "")),
        fila("Recomendacion:", hallazgo.get("recomendacion_mitigacion", "")),
        fila("Criterio normativo:", hallazgo.get("criterio_normativo", "")),
    ]

    col_a = 3.8 * cm
    col_b = ancho - col_a

    t = Table(datos, colWidths=[col_a, col_b])
    t.setStyle(TableStyle([
        # Fila de titulo
        ("BACKGROUND", (0, 0), (-1, 0), COLORES["encabezado"]),
        ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
        ("SPAN", (0, 0), (0, 0)),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        # Cuerpo
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLORES["fila_par"]]),
        ("VALIGN", (0, 1), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        # Borde izquierdo de color segun riesgo
        ("LINEAFTER", (0, 0), (0, -1), 3, color_borde),
        ("BOX", (0, 0), (-1, -1), 0.5, COLORES["borde"]),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, COLORES["borde"]),
    ]))
    return t


def generar_pdf(hallazgos: list, resumen_ejecutivo: str, ruta_salida: str, aprobado: bool):
    doc = SimpleDocTemplate(
        ruta_salida,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    ancho_util = A4[0] - 4 * cm
    estilos = construir_estilos()
    elementos = []

    # --- Encabezado ---
    elementos.append(Paragraph("INFORME DE AUDITORIA DE PRIVACIDAD", estilos["titulo"]))
    elementos.append(Paragraph("Sistema de Gestion de Privacidad de la Informacion (PIMS)", estilos["subtitulo"]))
    elementos.append(Paragraph("Universidad Nacional de San Agustin de Arequipa", estilos["subtitulo"]))
    elementos.append(Spacer(1, 0.3 * cm))

    # Metadatos
    fecha = datetime.now().strftime("%d de %B de %Y, %H:%M hrs")
    estado_txt = "APROBADO - El agente valido todos los hallazgos correctamente." if aprobado else "EMITIDO CON ADVERTENCIAS - Se alcanzo el limite de iteraciones."
    meta = [
        [Paragraph("<b>Fecha de emision:</b>", estilos["campo_label"]), Paragraph(fecha, estilos["campo_valor"])],
        [Paragraph("<b>Elaborado por:</b>", estilos["campo_label"]), Paragraph("PrivAudit AI — Agente de Evaluacion de Riesgos de Privacidad", estilos["campo_valor"])],
        [Paragraph("<b>Marco normativo:</b>", estilos["campo_label"]), Paragraph("ISO 27701:2025 | ISO 27001:2022 | ISO 42001:2023 | Ley 29733 (Peru)", estilos["campo_valor"])],
        [Paragraph("<b>Estado del informe:</b>", estilos["campo_label"]), Paragraph(estado_txt, estilos["campo_valor"])],
    ]
    t_meta = Table(meta, colWidths=[4 * cm, ancho_util - 4 * cm])
    t_meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLORES["fila_par"]),
        ("BOX", (0, 0), (-1, -1), 0.5, COLORES["borde"]),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, COLORES["borde"]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elementos.append(t_meta)
    elementos.append(Spacer(1, 0.4 * cm))

    # --- Resumen ejecutivo ---
    elementos.append(HRFlowable(width="100%", thickness=1, color=COLORES["encabezado"]))
    elementos.append(Paragraph("1. Resumen Ejecutivo", estilos["seccion"]))
    elementos.append(Paragraph(resumen_ejecutivo, estilos["resumen"]))
    elementos.append(Spacer(1, 0.3 * cm))

    # --- Tabla de conteo de riesgos ---
    elementos.append(Paragraph("Distribucion de Hallazgos por Nivel de Riesgo", estilos["campo_label"]))
    elementos.append(Spacer(1, 0.2 * cm))
    elementos.append(tabla_resumen_riesgos(hallazgos, estilos))
    elementos.append(Spacer(1, 0.5 * cm))

    # --- Hallazgos detallados ---
    elementos.append(HRFlowable(width="100%", thickness=1, color=COLORES["encabezado"]))
    elementos.append(Paragraph("2. Hallazgos Detallados", estilos["seccion"]))

    # Ordenar: ALTO primero, luego MEDIO, luego BAJO
    orden = {"ALTO": 0, "MEDIO": 1, "BAJO": 2}
    hallazgos_ordenados = sorted(hallazgos, key=lambda h: orden.get(h.get("nivel_riesgo", "BAJO"), 3))

    for i, h in enumerate(hallazgos_ordenados, 1):
        elementos.append(Spacer(1, 0.3 * cm))
        blq = bloque_hallazgo(h, i, estilos, ancho_util)
        elementos.append(KeepTogether([blq]))

    # --- Pie de pagina ---
    elementos.append(Spacer(1, 0.8 * cm))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=COLORES["borde"]))
    elementos.append(Spacer(1, 0.2 * cm))
    elementos.append(Paragraph(
        "Documento generado automaticamente por el Agente PrivAudit AI. "
        "Este informe es de caracter tecnico y debe ser revisado por un auditor certificado antes de su uso oficial. "
        "Confidencial — Uso interno UNSA.",
        estilos["pie"]
    ))

    doc.build(elementos)
    print(f"[PDF] Informe generado en: {ruta_salida}")
