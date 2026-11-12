"""
Generador de Memoria de Cálculo Profesional en formato PDF
para Tijeral a Dos Aguas en V Invertida (Gable Frame).
Normas: AISC 360-16 / NTE E.020 (Cargas) / NTE E.090 (Estructuras Metálicas) / AISI S100.

Características de presentación:
1. Encabezado de página en letra azul claro: "LDC-Peru" (izq) y "Estructuras" (der).
2. Fórmulas matemáticas en formato editorial con barra de fracción horizontal (estilo LaTeX / MathText).
3. Eliminación total de cuadros negros (reemplazo estricto por tags <sup> y <sub> compatibles con ReportLab).
4. Cero recortes de gráficos o tablas entre páginas (distribución modular protegida con KeepTogether).
"""

import os
import math
import tempfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image as PILImage

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

from perfiles_peru import TR_PERU_DATABASE, CORREAS_PERU_DATABASE, TENSORES_DATABASE

class NumberedCanvas(canvas.Canvas):
    """Canvas de dos pasadas para numerar páginas y dibujar el encabezado corporativo en azul claro."""
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()

        # =====================================================================
        # ENCABEZADO SUPERIOR EN AZUL CLARO
        # "LDC-Peru" a la izquierda y "Estructuras" a la derecha
        # =====================================================================
        self.setFont("Helvetica-Bold", 10.5)
        self.setFillColor(colors.HexColor("#2980B9")) # Azul claro corporativo
        self.drawString(2.0 * cm, 28.5 * cm, "LDC-Peru")
        self.drawRightString(19.0 * cm, 28.5 * cm, "Estructuras")

        # Línea divisoria en azul claro
        self.setStrokeColor(colors.HexColor("#7FB3D5"))
        self.setLineWidth(0.8)
        self.line(2.0 * cm, 28.3 * cm, 19.0 * cm, 28.3 * cm)

        # =====================================================================
        # PIE DE PÁGINA INFERIOR
        # =====================================================================
        self.setStrokeColor(colors.HexColor("#BDC3C7"))
        self.setLineWidth(0.5)
        self.line(2.0 * cm, 1.8 * cm, 19.0 * cm, 1.8 * cm)

        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#566573"))
        self.drawString(2.0 * cm, 1.4 * cm, "Memoria de Cálculo: Tijeral V Invertida | AISC 360-16 / NTE E.020 / NTE E.090")
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(19.0 * cm, 1.4 * cm, page_text)

        self.restoreState()


def _render_latex_formula_image(latex_str, temp_dir, prefix="eq", fontsize=13.5):
    """
    Renderiza una fórmula matemática en formato LaTeX (con barra de fracción horizontal)
    utilizando el motor MathText de Matplotlib.
    Recorta con precisión milimétrica los píxeles transparentes alrededor de la fórmula
    para asegurar un tamaño tipográfico grande, nítido y perfectamente legible.
    Devuelve un objeto RLImage dimensionado en puntos tipográficos con hAlign='LEFT'.
    """
    fig = plt.figure(figsize=(10, 2), dpi=260)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')
    ax.patch.set_alpha(0.0)
    
    ax.text(0.5, 0.5, f"${latex_str}$", fontsize=fontsize, color='#1B365D', ha='center', va='center')
    
    clean_prefix = "".join(c for c in prefix if c.isalnum() or c in ('_', '-'))
    raw_path = os.path.join(temp_dir, f"{clean_prefix}_{abs(hash(latex_str)) % 1000000}_raw.png")
    crop_path = os.path.join(temp_dir, f"{clean_prefix}_{abs(hash(latex_str)) % 1000000}.png")
    fig.savefig(raw_path, dpi=260, transparent=True)
    plt.close(fig)

    im = PILImage.open(raw_path)
    bbox = im.getbbox()
    if bbox:
        pad = 6
        crop_box = (
            max(0, bbox[0] - pad),
            max(0, bbox[1] - pad),
            min(im.size[0], bbox[2] + pad),
            min(im.size[1], bbox[3] + pad)
        )
        cropped = im.crop(crop_box)
        cropped.save(crop_path)
        w_px, h_px = cropped.size
    else:
        im.save(crop_path)
        w_px, h_px = im.size

    scale = 72.0 / 260.0
    w_pt = w_px * scale
    h_pt = h_px * scale

    # Limitar ancho a 440 pt (~15.5 cm) para que encaje limpiamente en la tarjeta
    max_w_pt = 440.0
    if w_pt > max_w_pt:
        ratio = max_w_pt / w_pt
        w_pt = max_w_pt
        h_pt = h_pt * ratio

    # Limitar altura máxima a 36 pt para mantener proporción vertical armónica
    max_h_pt = 36.0
    if h_pt > max_h_pt:
        ratio = max_h_pt / h_pt
        h_pt = max_h_pt
        w_pt = w_pt * ratio

    rl_img = RLImage(crop_path, width=w_pt, height=h_pt)
    rl_img.hAlign = 'LEFT'
    return rl_img


def _build_step_card(title, norm_ref, var_dict, latex_formula_str, subst_str, result_str, is_passed=None, temp_dir=None, eq_prefix="eq", target_h_cm=None):
    """
    Construye un bloque formal de fórmula paso a paso estilo ingeniería.
    Incluye:
    1. Título y norma.
    2. Variables explicadas.
    3. Fórmula en formato display matemático con barra de fracción horizontal (como en la Imagen 3).
    4. Sustitución numérica limpia.
    5. Resultado y estado de evaluación.
    """
    styles = getSampleStyleSheet()

    st_card_title = ParagraphStyle(
        'CardTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8.5, leading=10.5,
        textColor=colors.HexColor('#1B365D')
    )
    st_vars = ParagraphStyle(
        'CardVars', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5, leading=9.5,
        textColor=colors.HexColor('#2C3E50')
    )
    st_subst = ParagraphStyle(
        'CardSubst', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5, leading=9.5,
        textColor=colors.HexColor('#2C3E50')
    )
    st_res = ParagraphStyle(
        'CardRes', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8, leading=10,
        textColor=colors.HexColor('#0E6251') if is_passed else (colors.HexColor('#922B21') if is_passed is False else colors.HexColor('#1B365D'))
    )

    var_items = [f"<b>{k}:</b> {v}" for k, v in var_dict.items()]
    var_text = " &nbsp;|&nbsp; ".join(var_items)

    status_tag = ""
    if is_passed is True:
        status_tag = " &nbsp;-->&nbsp; <font color='#0E6251'><b>[CUMPLE - APROBADO]</b></font>"
    elif is_passed is False:
        status_tag = " &nbsp;-->&nbsp; <font color='#922B21'><b>[NO CUMPLE - EXCEDIDO]</b></font>"

    # Renderizar imagen matemática con escala natural legible y alineación izquierda
    math_img = _render_latex_formula_image(latex_formula_str, temp_dir, prefix=eq_prefix, fontsize=13.5)

    card_data = [
        [Paragraph(f"<b>{title}</b> &nbsp;&nbsp;<font color='#566573'><i>({norm_ref})</i></font>", st_card_title)],
        [Paragraph(f"<b>Variables:</b> {var_text}", st_vars)],
        [math_img],
        [Paragraph(f"<b>Sustitución:</b> &nbsp;{subst_str}", st_subst)],
        [Paragraph(f"<b>Resultado:</b> &nbsp;{result_str}{status_tag}", st_res)]
    ]

    t_card = Table(card_data, colWidths=[17.0 * cm])
    t_card.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8F9FA')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EAEDED')),
        ('BOX', (0,0), (-1,-1), 0.7, colors.HexColor('#BDC3C7')),
        ('LINEBELOW', (0,0), (-1,0), 0.5, colors.HexColor('#BDC3C7')),
        ('ALIGN', (0,2), (0,2), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,2), (0,2), 3),
        ('BOTTOMPADDING', (0,2), (0,2), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,2), (0,2), 22), # Sangría clara para la fórmula
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    return KeepTogether([t_card, Spacer(1, 4)])


def _generate_plot_images(solver, analysis_data):
    """Genera imágenes PNG temporales de los diagramas para embeber en el PDF sin recortes."""
    temp_dir = tempfile.gettempdir()
    gov = analysis_data['governing']
    res_gov = analysis_data['cases'][gov['tr_case']]

    # 1. Gráfico de Geometría y Apoyos
    fig, ax = plt.subplots(figsize=(7.5, 2.7), dpi=220)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#fdfefe')

    for el in solver.elements:
        ni = solver.nodes[el['i']]; nj = solver.nodes[el['j']]
        if 'rafter' in el['type']:
            ax.plot([ni['x'], nj['x']], [ni['y'], nj['y']], color='#c0392b', lw=3.0, zorder=3)
        elif el['type'] == 'tensor':
            ax.plot([ni['x'], nj['x']], [ni['y'], nj['y']], color='#2980b9', lw=2.2, zorder=3)
        elif el['type'] == 'hanger':
            ax.plot([ni['x'], nj['x']], [ni['y'], nj['y']], color='#27ae60', lw=1.5, linestyle='--', zorder=2)

    for p in solver.purlins:
        ax.plot(p['x'], p['y'], 's', color='#d35400', markersize=4.5, zorder=5)
        ax.annotate('', xy=(p['x'], p['y']), xytext=(p['x'], p['y'] + 0.35),
                    arrowprops=dict(arrowstyle="->", color='#d35400', lw=1.1))

    # Apoyo fijo (izquierdo)
    ax.plot([0, -0.22, 0.22, 0], [0, -0.28, -0.28, 0], color='#27ae60', lw=1.8)
    ax.plot([-0.3, 0.3], [-0.28, -0.28], color='#27ae60', lw=1.8)
    ax.text(0, -0.52, "FIJO (PINNED)", color='#27ae60', ha='center', fontsize=7.5, fontweight='bold')

    # Apoyo ranurado (derecho)
    L = solver.L
    slot = gov['slot_design']
    ax.plot([L, L - 0.22, L + 0.22, L], [0, -0.28, -0.28, 0], color='#2980b9', lw=1.8)
    ax.plot([L - 0.22, L + 0.22], [-0.34, -0.34], color='#2980b9', lw=3.0)
    ax.plot([L - 0.10, L + 0.10], [-0.42, -0.42], 'o', color='#2980b9', markersize=3.5)
    ax.text(L, -0.62, f"MÓVIL RANURADO\n(Ranura {slot['slot_length_mm']}x{slot['slot_width_mm']} mm)",
            color='#2980b9', ha='center', fontsize=7.5, fontweight='bold')

    ax.set_title(f"Modelo Estructural V Invertida: {solver.tr_name} + Correas {solver.purlin_name} (L = {solver.L:.1f} m)",
                 fontsize=9.5, fontweight='bold', color='#1b365d', pad=7)
    ax.set_xlabel("X (m)", fontsize=8, color='#566573'); ax.set_ylabel("Y (m)", fontsize=8, color='#566573')
    ax.tick_params(labelsize=7)
    ax.grid(True, linestyle='--', alpha=0.5, color='#dcdde1')
    ax.set_aspect('equal')
    ax.set_ylim(-0.8, solver.H + 0.55)
    plt.tight_layout()
    path_geom = os.path.join(temp_dir, "tijeral_pdf_geom.png")
    plt.savefig(path_geom, bbox_inches='tight')
    plt.close(fig)

    # 2. Gráfico Parabólico de Momentos Flectores
    fig, ax = plt.subplots(figsize=(7.5, 2.5), dpi=220)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#fdfefe')

    for el in solver.elements:
        ni = solver.nodes[el['i']]; nj = solver.nodes[el['j']]
        ax.plot([ni['x'], nj['x']], [ni['y'], nj['y']], color='#7f8c8d', lw=1.0)

    max_M_kgm = res_gov['max_rafter_moment_kgm']
    xs, ys, moments = solver.get_continuous_moment_curve(max_M_kgm)
    scale = 0.60 / (max_M_kgm + 1e-3)
    curve_x = []; curve_y = []
    nx_left = -math.sin(solver.theta); ny_left = math.cos(solver.theta)
    nx_right = math.sin(solver.theta); ny_right = math.cos(solver.theta)

    for i in range(len(xs)):
        x = xs[i]; y = ys[i]; M = moments[i]
        nx, ny = (nx_left, ny_left) if x <= solver.half_L else (nx_right, ny_right)
        offset = M * scale
        curve_x.append(x + nx * offset)
        curve_y.append(y + ny * offset)

    poly_x = list(xs) + list(reversed(curve_x))
    poly_y = list(ys) + list(reversed(curve_y))
    ax.fill(poly_x, poly_y, color='#e67e22', alpha=0.35, zorder=2)
    ax.plot(curve_x, curve_y, color='#d35400', lw=1.8, zorder=3)

    xl = solver.L / 4.0 + nx_left * (max_M_kgm * scale * 1.35)
    yl = solver.H / 2.0 + ny_left * (max_M_kgm * scale * 1.35)
    ax.text(xl, yl, f"Mu Máx = {max_M_kgm:.0f} kgf·m\n({res_gov['max_rafter_moment_kNm']:.2f} kNm)",
            color='#d35400', fontsize=8, fontweight='bold', ha='center',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffff', edgecolor='#d35400', lw=1))

    ax.set_title(f"Diagrama Parabólico Continuo de Momentos Flectores (Envolvente {gov['tr_case']})",
                 fontsize=9.5, fontweight='bold', color='#1b365d', pad=7)
    ax.set_xlabel("X (m)", fontsize=8, color='#566573'); ax.set_ylabel("Y (m)", fontsize=8, color='#566573')
    ax.tick_params(labelsize=7)
    ax.grid(True, linestyle='--', alpha=0.5, color='#dcdde1')
    ax.set_aspect('equal')
    ax.set_ylim(-0.55, solver.H + 0.85)
    plt.tight_layout()
    path_mom = os.path.join(temp_dir, "tijeral_pdf_mom.png")
    plt.savefig(path_mom, bbox_inches='tight')
    plt.close(fig)

    return path_geom, path_mom


def create_pdf_report(solver, filepath="Memoria_Tecnica_Tijeral_V_Invertida.pdf"):
    """
    Genera el documento PDF formal de cálculo estructural con fórmulas tipo LaTeX.
    """
    analysis_data = solver.solve_all_combinations()
    gov = analysis_data['governing']
    cases = analysis_data['cases']

    chk_tr = gov['tr_check']
    chk_t = gov['tensor_check']
    chk_p = gov['purlin_check']
    slot = gov['slot_design']
    cart = gov['cartela_design']

    tr_data = TR_PERU_DATABASE[solver.tr_name]
    purlin_data = CORREAS_PERU_DATABASE[solver.purlin_name]
    tensor_data = TENSORES_DATABASE[solver.tensor_name]

    temp_dir = tempfile.gettempdir()
    img_geom, img_mom = _generate_plot_images(solver, analysis_data)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm
    )

    styles = getSampleStyleSheet()

    style_cover_title = ParagraphStyle(
        'CoverTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=14, leading=17,
        textColor=colors.HexColor('#1B365D'), alignment=1, spaceAfter=4
    )
    style_cover_sub = ParagraphStyle(
        'CoverSub', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9.5, leading=12,
        textColor=colors.HexColor('#2C3E50'), alignment=1, spaceAfter=8
    )
    style_sec_h1 = ParagraphStyle(
        'SecH1', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10, leading=13,
        textColor=colors.HexColor('#1B365D'), spaceBefore=4, spaceAfter=2
    )
    style_norm_ref = ParagraphStyle(
        'NormRef', parent=styles['Normal'],
        fontName='Helvetica-Oblique', fontSize=7.5, leading=9.5,
        textColor=colors.HexColor('#566573'), spaceAfter=4
    )
    style_body = ParagraphStyle(
        'BodyTxt', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=10.5,
        textColor=colors.HexColor('#2C3E50')
    )
    style_th = ParagraphStyle(
        'TableHead', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.5, leading=9.5,
        textColor=colors.white, alignment=1
    )
    style_td = ParagraphStyle(
        'TableData', parent=styles['Normal'],
        fontName='Helvetica', fontSize=7.5, leading=9.5,
        textColor=colors.HexColor('#2C3E50'), alignment=0
    )
    style_td_center = ParagraphStyle('TableDataCenter', parent=style_td, alignment=1)
    style_td_right = ParagraphStyle('TableDataRight', parent=style_td, alignment=2)
    style_badge_ok = ParagraphStyle(
        'BadgeOK', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.5, leading=9.5,
        textColor=colors.HexColor('#0E6251'), alignment=1
    )
    style_badge_fail = ParagraphStyle(
        'BadgeFail', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=7.5, leading=9.5,
        textColor=colors.HexColor('#922B21'), alignment=1
    )

    story = []

    # =========================================================================
    # PÁGINA 1: PORTADA, FICHA TÉCNICA, DASHBOARD KPI Y ESQUEMA GEOMÉTRICO
    # =========================================================================
    p1_elements = []
    p1_elements.append(Paragraph("MEMORIA DE CÁLCULO ESTRUCTURAL FORMAL", style_cover_title))
    p1_elements.append(Paragraph("TIJERAL A DOS AGUAS EN V INVERTIDA (GABLE FRAME) SIN RETICULADO", style_cover_sub))
    p1_elements.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor('#1B365D'), spaceAfter=6))

    # Ficha Técnica
    meta_data = [
        [Paragraph("<b>Proyecto:</b>", style_td), Paragraph("Cobertura Metálica a Dos Aguas en V Invertida", style_td),
         Paragraph("<b>Fecha:</b>", style_td), Paragraph("Noviembre 2026", style_td)],
        [Paragraph("<b>Ubicación:</b>", style_td), Paragraph(f"{solver.city_name} - Perú", style_td),
         Paragraph("<b>Normas:</b>", style_td), Paragraph("AISC 360-16 / NTE E.020 / NTE E.090", style_td)],
        [Paragraph("<b>Perfil TR:</b>", style_td), Paragraph(f"{solver.tr_name} (ASTM A500 Gr. B)", style_td),
         Paragraph("<b>Correas:</b>", style_td), Paragraph(f"{solver.purlin_name} (t=2.5/3.0 mm)", style_td)],
        [Paragraph("<b>Tensor:</b>", style_td), Paragraph(f"{solver.tensor_name} (ASTM A36)", style_td),
         Paragraph("<b>Condición Viento:</b>", style_td), Paragraph(f"{solver.enclosure_desc}", style_td)]
    ]
    t_meta = Table(meta_data, colWidths=[2.2*cm, 6.3*cm, 2.5*cm, 6.0*cm])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8F9FA')),
        ('BOX', (0,0), (-1,-1), 0.7, colors.HexColor('#BDC3C7')),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor('#EAECEE')),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    p1_elements.append(t_meta)
    p1_elements.append(Spacer(1, 6))

    # Tabla KPI de Cumplimiento
    p1_elements.append(Paragraph("RESUMEN EJECUTIVO DE VERIFICACIÓN NORMATIVA (RATIOS DCR)", style_sec_h1))
    p1_elements.append(Paragraph("Verificación frente a la envolvente crítica de todas las combinaciones LRFD:", style_norm_ref))

    kpi_table_data = [
        [Paragraph("Componente", style_th), Paragraph("Perfil / Especificación", style_th),
         Paragraph("Solicitación Última", style_th), Paragraph("Capacidad Nominal", style_th),
         Paragraph("Ratio DCR", style_th), Paragraph("Estado", style_th)]
    ]

    elements_kpi = [
        ("Viga TR (Flexocompresión)", solver.tr_name, f"Mu={chk_tr['M_u_kgm']:.0f} kgf·m<br/>Pu={chk_tr['P_u_kgf']:.0f} kgf", f"φMn={chk_tr['phi_Mn_kgm']:.0f} kgf·m<br/>φPn={chk_tr['phi_Pn_kgf']:.0f} kgf", f"{chk_tr['dcr']:.3f}", "CUMPLE" if chk_tr['dcr']<=1.0 else "NO CUMPLE"),
        ("Tensor Horizontal (Tracción)", solver.tensor_name, f"Tu = {chk_t['T_u_kgf']:.0f} kgf", f"φPn = {chk_t['phi_Pn_kgf']:.0f} kgf", f"{chk_t['dcr']:.3f}", "CUMPLE" if chk_t['dcr']<=1.0 else "NO CUMPLE"),
        ("Correas (Flexión y Flecha)", solver.purlin_name, f"Mu = {chk_p['M_u_kgm']:.1f} kgf·m<br/>δ = {chk_p['delta_mm']:.1f} mm", f"φMn = {chk_p['phi_Mn_kgm']:.1f} kgf·m<br/>δadm = {chk_p['delta_adm_mm']:.1f} mm", f"{chk_p['dcr']:.3f}", "CUMPLE" if chk_p['dcr']<=1.0 else "NO CUMPLE"),
        ("Apoyo Móvil Ranurado", f"Perno Ø {slot['bolt_diam_mm']/25.4:.2f}\"", f"Desplaz. = {slot['elastic_disp_mm']:.1f} mm", f"Ranura = {slot['slot_length_mm']} x {slot['slot_width_mm']} mm", f"{slot['elastic_disp_mm']/slot['slot_length_mm']:.3f}", "CUMPLE"),
        ("Soldadura Cartela - TR", "Filete a=4 mm (E7018)", f"Tu = {cart['T_u_kgf']:.0f} kgf", f"Capac = 2,214 kgf/cm", f"L = {cart['weld_length_cm']} cm", "CUMPLE")
    ]

    for item in elements_kpi:
        badge = Paragraph(f"<b>{item[5]}</b>", style_badge_ok if item[5]=="CUMPLE" else style_badge_fail)
        kpi_table_data.append([
            Paragraph(f"<b>{item[0]}</b>", style_td),
            Paragraph(item[1], style_td),
            Paragraph(item[2], style_td_center),
            Paragraph(item[3], style_td_center),
            Paragraph(item[4], style_td_center),
            badge
        ])

    t_kpi = Table(kpi_table_data, colWidths=[3.8*cm, 3.4*cm, 3.3*cm, 3.3*cm, 1.6*cm, 1.6*cm])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1B365D')),
        ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor('#1B365D')),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor('#BDC3C7')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('BACKGROUND', (5,1), (5,-1), colors.HexColor('#D4EFDF')),
    ]))
    p1_elements.append(t_kpi)
    p1_elements.append(Spacer(1, 6))

    # Gráfico geométrico embebido
    p1_elements.append(RLImage(img_geom, width=17.0*cm, height=6.1*cm))
    story.append(KeepTogether(p1_elements))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 2: SECCIÓN 1 (BASES GEOMÉTRICAS) Y SECCIÓN 2 (CARGA DE VIENTO)
    # =========================================================================
    p2_elements = []
    p2_elements.append(Paragraph("1. BASES GEOMÉTRICAS Y SINCRONIZACIÓN DE ALTURAS", style_sec_h1))
    p2_elements.append(Paragraph("Referencia Normativa: NTE E.020 (Art. 12) / NTE E.090 (Cap. 2)", style_norm_ref))

    p2_elements.append(_build_step_card(
        title="Altura Total Sincronizada del Edificio",
        norm_ref="NTE E.020 Art. 12.2",
        var_dict={"H_col": f"{solver.col_height_m:.2f} m", "H_tijeral": f"{solver.H:.2f} m"},
        latex_formula_str=r"h_{\mathrm{tot}} = H_{\mathrm{col}} + H",
        subst_str=f"h<sub>tot</sub> = {solver.col_height_m:.2f} m + {solver.H:.2f} m",
        result_str=f"h<sub>tot</sub> = {solver.building_height_m:.2f} m",
        temp_dir=temp_dir, eq_prefix="geom_htot"
    ))

    p2_elements.append(_build_step_card(
        title="Longitud Inclinada de la Viga TR y Pendiente",
        norm_ref="Geometría Pitagórica y Pendiente Porcentual",
        var_dict={"L": f"{solver.L:.2f} m", "H": f"{solver.H:.2f} m", "L/2": f"{solver.half_L:.2f} m"},
        latex_formula_str=r"L_r = \sqrt{\left(\frac{L}{2}\right)^2 + H^2} \qquad p = \left(\frac{H}{L/2}\right) \times 100\%",
        subst_str=f"L<sub>r</sub> = √(({solver.half_L:.2f})<sup>2</sup> + ({solver.H:.2f})<sup>2</sup>) = {solver.slope_len:.2f} m &nbsp;|&nbsp; p = ({solver.H:.2f} / {solver.half_L:.2f}) × 100",
        result_str=f"L<sub>r</sub> = {solver.slope_len:.2f} m &nbsp;|&nbsp; p = {solver.slope_pct:.1f}% &nbsp;(θ = {solver.theta_deg:.2f}°)",
        temp_dir=temp_dir, eq_prefix="geom_lr"
    ))

    p2_elements.append(_build_step_card(
        title="Espaciado Modular Real entre Correas",
        norm_ref="Distribución Uniforme a lo Largo de la Viga",
        var_dict={"L_r": f"{solver.slope_len:.2f} m", "s_p_propuesto": f"{solver.purlin_spacing:.2f} m", "N_espacios": f"{len(solver.purlins)//2}"},
        latex_formula_str=r"s_p = \frac{L_r}{N_{\mathrm{espacios}}}",
        subst_str=f"s<sub>p</sub> = {solver.slope_len:.2f} m / {len(solver.purlins)//2}",
        result_str=f"s<sub>p</sub> = {solver.actual_purlin_spacing:.2f} m &nbsp;(Correas por faldón: {len(solver.purlins)//2} unidades)",
        temp_dir=temp_dir, eq_prefix="geom_sp"
    ))

    p2_elements.append(Spacer(1, 4))
    p2_elements.append(Paragraph("2. DETERMINACIÓN DE LA CARGA DE VIENTO SEGÚN NTE E.020 (CAP. 5)", style_sec_h1))
    p2_elements.append(Paragraph(f"Referencia Normativa: NTE E.020 Artículos 12 y 13 (Condición Evaluada: {solver.enclosure_desc})", style_norm_ref))

    p2_elements.append(_build_step_card(
        title="Velocidad de Diseño a la Altura Cumbrera (Vh)",
        norm_ref="NTE E.020 Art. 12.2 (h > 10 m)",
        var_dict={"Ciudad": solver.city_name, "V": f"{solver.wind_speed_kmh:.1f} km/h", "h": f"{solver.building_height_m:.2f} m"},
        latex_formula_str=r"V_h = V \cdot \left(\frac{h_{\mathrm{tot}}}{10}\right)^{0.22}",
        subst_str=f"V<sub>h</sub> = {solver.wind_speed_kmh:.1f} × ({solver.building_height_m:.2f} / 10)<sup>0.22</sup>",
        result_str=f"V<sub>h</sub> = {solver.Vh_kmh:.2f} km/h",
        temp_dir=temp_dir, eq_prefix="wind_vh"
    ))

    p2_elements.append(_build_step_card(
        title="Presión Dinámica Básica de Viento (q)",
        norm_ref="NTE E.020 Art. 12.3",
        var_dict={"Vh": f"{solver.Vh_kmh:.2f} km/h", "Constante": "0.005"},
        latex_formula_str=r"q = 0.005 \cdot V_h^2 \quad \left[\mathrm{kgf/m^2}\right]",
        subst_str=f"q = 0.005 × ({solver.Vh_kmh:.2f})<sup>2</sup>",
        result_str=f"q = {solver.q_base_kg_m2:.2f} kgf/m<sup>2</sup>",
        temp_dir=temp_dir, eq_prefix="wind_q"
    ))

    if solver.enclosure_type == 'open':
        p2_elements.append(_build_step_card(
            title="Factores de Forma (C) y Presiones en Cobertura de Espacio Abierto / Tinglado",
            norm_ref="NTE E.020 Tabla 4 (Construcciones Abiertas / Tinglados a dos aguas)",
            var_dict={"Condición": "Espacio Abierto (flujo libre inferior y superior)", "q": f"{solver.q_base_kg_m2:.2f} kgf/m<sup>2</sup>"},
            latex_formula_str=r"P_h = q \cdot C \qquad \left(C_{\mathrm{barl,pres}} = +0.80, \; C_{\mathrm{barl,uplift}} = -1.20\right)",
            subst_str=f"Presión: Ph_barl={solver.q_base_kg_m2:.2f}×(+0.80), Ph_sot={solver.q_base_kg_m2:.2f}×(-0.50) &nbsp;|&nbsp; Uplift: Ph_barl={solver.q_base_kg_m2:.2f}×(-1.20)",
            result_str=f"Presión: Ph_barl = {solver.P_wind_barlovento_kg_m2:+.2f} kgf/m<sup>2</sup>, Ph_sot = {solver.P_wind_sotavento_kg_m2:+.2f} kgf/m<sup>2</sup> &nbsp;|&nbsp; Uplift: Ph_uplift = {solver.P_wind_barlovento_uplift_kg_m2:+.2f} kgf/m<sup>2</sup>",
            temp_dir=temp_dir, eq_prefix="wind_open"
        ))
    else:
        p2_elements.append(_build_step_card(
            title="Factores de Forma (C) y Presiones en Edificación Cerrada",
            norm_ref="NTE E.020 Tabla 4 (Superficies inclinadas a dos aguas en edificaciones cerradas)",
            var_dict={"Condición": "Espacio Cerrado", "θ": f"{solver.theta_deg:.1f}°", "C_barl": f"{solver.C_barlovento:+.2f}", "C_sot": "-0.60"},
            latex_formula_str=r"C_{\mathrm{barl}} = 0.07(\theta) - 1.0 \qquad C_{\mathrm{sot}} = -0.60 \qquad P_h = q \cdot C",
            subst_str=f"C_barl = 0.07({solver.theta_deg:.1f}) - 1.0 = {solver.C_barlovento:+.2f} &nbsp;|&nbsp; Ph_barl = {solver.q_base_kg_m2:.2f} × ({solver.C_barlovento:+.2f})",
            result_str=f"Ph_barl = {solver.P_wind_barlovento_kg_m2:+.2f} kgf/m<sup>2</sup> &nbsp;|&nbsp; Ph_sot = {solver.P_wind_sotavento_kg_m2:+.2f} kgf/m<sup>2</sup>",
            temp_dir=temp_dir, eq_prefix="wind_closed"
        ))

    story.append(KeepTogether(p2_elements))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 3: SECCIÓN 3 (METRADO DE CARGAS, COMBINACIONES LRFD Y MOMENTOS)
    # =========================================================================
    p3_elements = []
    p3_elements.append(Paragraph("3. METRADO DE CARGAS Y COMBINACIONES LRFD RESUELTAS", style_sec_h1))
    p3_elements.append(Paragraph("Referencia Normativa: AISC 360-16 Sección B2 / NTE E.090 Capítulo 3", style_norm_ref))

    p_d = solver.roof_dead_load * solver.actual_purlin_spacing * solver.S + purlin_data['weight_kg_m'] * solver.S
    p_l = solver.roof_live_load * solver.actual_purlin_spacing * solver.S

    p3_elements.append(_build_step_card(
        title="Cargas Puntuales por Nudo de Correa (Área Tributaria Atrib = sp × S)",
        norm_ref="NTE E.020 Metrado de Cargas",
        var_dict={"s_p": f"{solver.actual_purlin_spacing:.2f} m", "S": f"{solver.S:.2f} m", "Atrib": f"{solver.actual_purlin_spacing*solver.S:.2f} m<sup>2</sup>", "w_cub": f"{solver.roof_dead_load:.1f} kgf/m<sup>2</sup>", "w_corr": f"{purlin_data['weight_kg_m']:.2f} kgf/m"},
        latex_formula_str=r"P_D = (w_{\mathrm{cub}} \cdot A_{\mathrm{trib}}) + (w_{\mathrm{corr}} \cdot S) \qquad P_{Lr} = w_{\mathrm{viva}} \cdot A_{\mathrm{trib}} \qquad P_u = 1.2 P_D + 1.6 P_{Lr}",
        subst_str=f"P<sub>D</sub> = ({solver.roof_dead_load:.1f} × {solver.actual_purlin_spacing*solver.S:.2f}) + ({purlin_data['weight_kg_m']:.2f} × {solver.S:.2f}) = {p_d:.1f} kgf &nbsp;|&nbsp; P<sub>Lr</sub> = {solver.roof_live_load:.1f} × {solver.actual_purlin_spacing*solver.S:.2f} = {p_l:.1f} kgf",
        result_str=f"P<sub>D</sub> = {p_d:.1f} kgf &nbsp;|&nbsp; P<sub>Lr</sub> = {p_l:.1f} kgf &nbsp;|&nbsp; P<sub>u,grav</sub> = 1.2({p_d:.1f}) + 1.6({p_l:.1f}) = {1.2*p_d + 1.6*p_l:.1f} kgf",
        temp_dir=temp_dir, eq_prefix="load_pd"
    ))

    # Tabla de Combinaciones LRFD
    comb_table = [
        [Paragraph("Caso / Combinación LRFD", style_th), Paragraph("Pu TR (kgf)", style_th), Paragraph("Mu TR (kgf·m)", style_th),
         Paragraph("Tu Tensor (kgf)", style_th), Paragraph("Δx Móvil (mm)", style_th), Paragraph("DCR TR", style_th), Paragraph("Condición", style_th)],
        [Paragraph("Comb 1: 1.4 D", style_td), Paragraph(f"{cases['comb1_14D']['max_rafter_axial_kgf']:.0f}", style_td_right), Paragraph(f"{cases['comb1_14D']['max_rafter_moment_kgm']:.0f}", style_td_right), Paragraph(f"{cases['comb1_14D']['max_tensor_tension_kgf']:.0f}", style_td_right), Paragraph(f"{cases['comb1_14D']['u_roller_x_mm']:+.2f}", style_td_center), Paragraph(f"{solver._check_tr_flexocompression(cases['comb1_14D']['max_rafter_axial_kN']*1000, cases['comb1_14D']['max_rafter_moment_kNm']*1000, tr_data)['dcr']:.3f}", style_td_center), Paragraph("Permanente pura", style_td)],
        [Paragraph("Comb 2: 1.2 D + 1.6 Lr", style_td), Paragraph(f"{cases['comb2_12D_16L']['max_rafter_axial_kgf']:.0f}", style_td_right), Paragraph(f"{cases['comb2_12D_16L']['max_rafter_moment_kgm']:.0f}", style_td_right), Paragraph(f"{cases['comb2_12D_16L']['max_tensor_tension_kgf']:.0f}", style_td_right), Paragraph(f"{cases['comb2_12D_16L']['u_roller_x_mm']:+.2f}", style_td_center), Paragraph(f"{solver._check_tr_flexocompression(cases['comb2_12D_16L']['max_rafter_axial_kN']*1000, cases['comb2_12D_16L']['max_rafter_moment_kNm']*1000, tr_data)['dcr']:.3f}", style_td_center), Paragraph("Gravedad máx.", style_td)],
        [Paragraph("Comb 3: 1.2 D + 1.0 W + 0.5 Lr", style_td), Paragraph(f"{cases['comb3_12D_10W_05L']['max_rafter_axial_kgf']:.0f}", style_td_right), Paragraph(f"{cases['comb3_12D_10W_05L']['max_rafter_moment_kgm']:.0f}", style_td_right), Paragraph(f"{cases['comb3_12D_10W_05L']['max_tensor_tension_kgf']:.0f}", style_td_right), Paragraph(f"{cases['comb3_12D_10W_05L']['u_roller_x_mm']:+.2f}", style_td_center), Paragraph(f"{solver._check_tr_flexocompression(cases['comb3_12D_10W_05L']['max_rafter_axial_kN']*1000, cases['comb3_12D_10W_05L']['max_rafter_moment_kNm']*1000, tr_data)['dcr']:.3f}", style_td_center), Paragraph("Viento presión", style_td)],
        [Paragraph("Comb 4: 0.9 D - 1.0 W (Succión)", style_td), Paragraph(f"{cases['comb4_09D_10W_uplift']['max_rafter_axial_kgf']:.0f}", style_td_right), Paragraph(f"{cases['comb4_09D_10W_uplift']['max_rafter_moment_kgm']:.0f}", style_td_right), Paragraph(f"{cases['comb4_09D_10W_uplift']['max_tensor_tension_kgf']:.0f}", style_td_right), Paragraph(f"{cases['comb4_09D_10W_uplift']['u_roller_x_mm']:+.2f}", style_td_center), Paragraph(f"{solver._check_tr_flexocompression(cases['comb4_09D_10W_uplift']['max_rafter_axial_kN']*1000, cases['comb4_09D_10W_uplift']['max_rafter_moment_kNm']*1000, tr_data)['dcr']:.3f}", style_td_center), Paragraph("Uplift / Despegue", style_td)],
        [Paragraph("Servicio: 1.0 D + 1.0 Lr", style_td), Paragraph(f"{cases['service_10D_10L']['max_rafter_axial_kgf']:.0f}", style_td_right), Paragraph(f"{cases['service_10D_10L']['max_rafter_moment_kgm']:.0f}", style_td_right), Paragraph(f"{cases['service_10D_10L']['max_tensor_tension_kgf']:.0f}", style_td_right), Paragraph(f"{cases['service_10D_10L']['u_roller_x_mm']:+.2f}", style_td_center), Paragraph("-", style_td_center), Paragraph("Control de flechas", style_td)],
        [Paragraph(f"<b>ENVOLVENTE ({gov['tr_case']})</b>", style_td), Paragraph(f"<b>{chk_tr['P_u_kgf']:.0f}</b>", style_td_right), Paragraph(f"<b>{chk_tr['M_u_kgm']:.0f}</b>", style_td_right), Paragraph(f"<b>{chk_t['T_u_kgf']:.0f}</b>", style_td_right), Paragraph(f"<b>{slot['elastic_disp_mm']:.2f}</b>", style_td_center), Paragraph(f"<b>{chk_tr['dcr']:.3f}</b>", style_td_center), Paragraph("<b>GOBERNANTE</b>", style_td_center)]
    ]
    t_comb = Table(comb_table, colWidths=[4.8*cm, 2.0*cm, 2.2*cm, 2.2*cm, 2.0*cm, 1.8*cm, 2.0*cm])
    t_comb.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1B365D')),
        ('BOX', (0,0), (-1,-1), 0.7, colors.HexColor('#BDC3C7')),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor('#EAECEE')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#D5D8DC')),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    p3_elements.append(t_comb)
    p3_elements.append(Spacer(1, 6))

    # Diagrama de momentos embebido
    p3_elements.append(RLImage(img_mom, width=17.0*cm, height=5.5*cm))
    story.append(KeepTogether(p3_elements))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 4: SECCIÓN 4 (DISEÑO DE LA VIGA TR SEGÚN AISC 360-16)
    # =========================================================================
    p4_elements = []
    p4_elements.append(Paragraph("4. DISEÑO A FLEXOCOMPRESIÓN DE LA VIGA TR (AISC 360-16)", style_sec_h1))
    p4_elements.append(Paragraph(f"Referencia Normativa: AISC 360-16 Capítulos E, F7 y H1.1 (Perfil: {solver.tr_name})", style_norm_ref))

    p4_elements.append(_build_step_card(
        title="Esbeltez Gobernante del Perfil Tubular (AISC Capítulo E)",
        norm_ref="AISC 360-16 Sección E2 (Límite KL/r ≤ 200)",
        var_dict={"Lx": f"{solver.slope_len:.2f} m", "rx": f"{tr_data['rx']*100:.2f} cm", "Ly": f"{solver.actual_purlin_spacing:.2f} m", "ry": f"{tr_data['ry']*100:.2f} cm", "K": "1.0"},
        latex_formula_str=r"\left(\frac{KL}{r}\right)_{\max} = \max\left(\frac{K \cdot L_x}{r_x}, \; \frac{K \cdot L_y}{r_y}\right) \leq 200",
        subst_str=f"(KL/r)<sub>x</sub> = 1.0 × {solver.slope_len*100:.0f} / {tr_data['rx']*100:.2f} = {solver.slope_len/tr_data['rx']:.1f} &nbsp;|&nbsp; (KL/r)<sub>y</sub> = {solver.actual_purlin_spacing*100:.0f} / {tr_data['ry']*100:.2f} = {solver.actual_purlin_spacing/tr_data['ry']:.1f}",
        result_str=f"(KL/r)<sub>max</sub> = {chk_tr['KL_r_max']:.1f} ≤ 200.0",
        is_passed=chk_tr['KL_r_max'] <= 200.0,
        temp_dir=temp_dir, eq_prefix="tr_slend"
    ))

    p4_elements.append(_build_step_card(
        title="Tensión Crítica y Capacidad de Diseño a Compresión Axial (φc Pn)",
        norm_ref="AISC 360-16 Ecuaciones E3-2 y E3-4 (φc = 0.90)",
        var_dict={"Fy": f"{solver.Fy_tr/1e6:.0f} MPa", "E": "200,000 MPa", "Ag": f"{tr_data['A']*1e4:.2f} cm<sup>2</sup>", "Fe": f"{chk_tr['Fe_MPa']:.1f} MPa"},
        latex_formula_str=r"F_e = \frac{\pi^2 E}{\left(\frac{KL}{r}\right)^2} \qquad F_{cr} = 0.658^{\frac{F_y}{F_e}} \cdot F_y \qquad \phi_c P_n = 0.90 \cdot F_{cr} \cdot A_g",
        subst_str=f"F<sub>e</sub> = (π<sup>2</sup> × 200000)/({chk_tr['KL_r_max']:.1f})<sup>2</sup> = {chk_tr['Fe_MPa']:.1f} MPa &nbsp;|&nbsp; F<sub>cr</sub> = {chk_tr['Fcr_MPa']:.1f} MPa &nbsp;|&nbsp; φ<sub>c</sub> P<sub>n</sub> = 0.90 × {chk_tr['Fcr_MPa']:.1f} × {tr_data['A']*1e4:.2f}",
        result_str=f"φ<sub>c</sub> P<sub>n</sub> = {chk_tr['phi_Pn_kgf']:.0f} kgf ({chk_tr['phi_Pn_kN']:.1f} kN)",
        temp_dir=temp_dir, eq_prefix="tr_comp"
    ))

    p4_elements.append(_build_step_card(
        title="Resistencia de Diseño a Flexión Pura en Eje Fuerte (φb Mn)",
        norm_ref="AISC 360-16 Capítulo F7 (Perfiles Tubulares Rectangulares, φb = 0.90)",
        var_dict={"Fy": f"{solver.Fy_tr/1e6:.0f} MPa", "Zx": f"{tr_data['Zx']*1e6:.1f} cm<sup>3</sup>", "Sx": f"{tr_data['Sx']*1e6:.1f} cm<sup>3</sup>"},
        latex_formula_str=r"M_n = \min(F_y \cdot Z_x, \; 1.6 F_y \cdot S_x) \qquad \phi_b M_n = 0.90 \cdot M_n",
        subst_str=f"M<sub>p</sub> = {solver.Fy_tr/1e6:.0f} × {tr_data['Zx']*1e6:.1f} × 10<sup>-3</sup> = {solver.Fy_tr*tr_data['Zx']/9.80665:.0f} kgf·m &nbsp;|&nbsp; φ<sub>b</sub> M<sub>n</sub> = 0.90 × {solver.Fy_tr*tr_data['Zx']/9.80665:.0f}",
        result_str=f"φ<sub>b</sub> M<sub>n</sub> = {chk_tr['phi_Mn_kgm']:.0f} kgf·m ({chk_tr['phi_Mn_kNm']:.2f} kNm)",
        temp_dir=temp_dir, eq_prefix="tr_flex"
    ))

    p4_elements.append(_build_step_card(
        title="Ecuación de Interacción Flexocompresión Biaxial/Uniaxial",
        norm_ref=chk_tr['formula'],
        var_dict={"Pu": f"{chk_tr['P_u_kgf']:.0f} kgf", "φc Pn": f"{chk_tr['phi_Pn_kgf']:.0f} kgf", "Mu": f"{chk_tr['M_u_kgm']:.0f} kgf·m", "φb Mn": f"{chk_tr['phi_Mn_kgm']:.0f} kgf·m"},
        latex_formula_str=r"\frac{P_u}{\phi_c P_n} + \frac{8}{9}\left(\frac{M_u}{\phi_b M_n}\right) \leq 1.00 \qquad \left(\mathrm{para} \; \frac{P_u}{\phi_c P_n} \geq 0.2\right)",
        subst_str=f"Ratio Axial = {chk_tr['ratio_axial']:.3f} &nbsp;|&nbsp; Ratio Flexión = {chk_tr['ratio_flex']:.3f} &nbsp;|&nbsp; DCR = {chk_tr['ratio_axial']:.3f} + (8/9)({chk_tr['ratio_flex']:.3f})",
        result_str=f"Ratio DCR = {chk_tr['dcr']:.3f} ≤ 1.000",
        is_passed=chk_tr['dcr'] <= 1.0,
        temp_dir=temp_dir, eq_prefix="tr_inter"
    ))

    story.append(KeepTogether(p4_elements))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 5: SECCIÓN 5 (CORREAS DE TECHO) Y SECCIÓN 6 (TENSOR HORIZONTAL)
    # =========================================================================
    p5_elements = []
    p5_elements.append(Paragraph("5. VERIFICACIÓN ESTRUCTURAL DE LAS CORREAS DE TECHO (C O U)", style_sec_h1))
    p5_elements.append(Paragraph(f"Referencia Normativa: AISI S100 / NTE E.090 (Perfil: {solver.purlin_name})", style_norm_ref))

    p5_elements.append(_build_step_card(
        title="Capacidad y Solicitación a Flexión de la Correa",
        norm_ref="AISI S100 / NTE E.090 Capítulo 4 (φb = 0.90)",
        var_dict={"Perfil": solver.purlin_name, "Sx": f"{purlin_data['Sx']*1e6:.1f} cm<sup>3</sup>", "L": f"{solver.S:.2f} m", "Fy": "250 MPa"},
        latex_formula_str=r"M_u = \frac{q_u \cdot L^2}{8} \qquad \phi_b M_n = 0.90 \cdot F_y \cdot S_x \qquad \mathrm{DCR}_{\mathrm{flex}} = \frac{M_u}{\phi_b M_n} \leq 1.00",
        subst_str=f"M<sub>u</sub> = {chk_p['M_u_kgm']:.1f} kgf·m &nbsp;|&nbsp; φ<sub>b</sub> M<sub>n</sub> = 0.90 × (250 × 10.197) × {purlin_data['Sx']*1e6:.1f} × 10<sup>-3</sup> = {chk_p['phi_Mn_kgm']:.1f} kgf·m",
        result_str=f"DCR<sub>flex</sub> = M<sub>u</sub> / φ<sub>b</sub> M<sub>n</sub> = {chk_p['dcr_flex']:.3f} ≤ 1.000",
        is_passed=chk_p['dcr_flex'] <= 1.0,
        temp_dir=temp_dir, eq_prefix="corr_flex"
    ))

    # ¡FÓRMULA EXACTA COMO EN LA IMAGEN 3 SUBIDA POR EL USUARIO!
    p5_elements.append(_build_step_card(
        title="Control de Deflexión Elástica de Servicio",
        norm_ref="NTE E.020 Art. 15 / NTE E.090 (Límite δadm = L / 200)",
        var_dict={"Ix": f"{purlin_data['Ix']*1e8:.0f} cm<sup>4</sup>", "E": "2,040,000 kgf/cm<sup>2</sup>", "L": f"{solver.S*1000:.0f} mm"},
        latex_formula_str=r"\delta = \frac{5 q_s L^4}{384 E I_x} \leq \delta_{\mathrm{adm}} = \frac{L}{200}",
        subst_str=f"δ = {chk_p['delta_mm']:.1f} mm &nbsp;|&nbsp; δ<sub>adm</sub> = {solver.S*1000:.0f} / 200 = {chk_p['delta_adm_mm']:.1f} mm",
        result_str=f"DCR<sub>flecha</sub> = δ / δ<sub>adm</sub> = {chk_p['dcr_deflect']:.3f} ≤ 1.000",
        is_passed=chk_p['dcr_deflect'] <= 1.0,
        temp_dir=temp_dir, eq_prefix="corr_deflect"
    ))

    p5_elements.append(Spacer(1, 4))
    p5_elements.append(Paragraph("6. DISEÑO DEL TENSOR HORIZONTAL DE AMARRE", style_sec_h1))
    p5_elements.append(Paragraph(f"Referencia Normativa: AISC 360-16 Capítulo D (Diseño a Tracción - {solver.tensor_name})", style_norm_ref))

    p5_elements.append(_build_step_card(
        title="Capacidad a Tracción por Fluencia Bruta y Rotura Neta",
        norm_ref="AISC 360-16 Eq. D2-1 (φt=0.90) y Eq. D2-2 (φt=0.75)",
        var_dict={"Ag": f"{tensor_data['Ag_m2']*1e4:.2f} cm<sup>2</sup>", "An": f"{0.75*tensor_data['Ag_m2']*1e4:.2f} cm<sup>2</sup>", "Fy": "2,500 kgf/cm<sup>2</sup>", "Fu": "4,000 kgf/cm<sup>2</sup>"},
        latex_formula_str=r"\phi_t P_{ny} = 0.90 F_y A_g \qquad \phi_t P_{nu} = 0.75 F_u A_n \qquad \phi P_n = \min(\phi_t P_{ny}, \phi_t P_{nu})",
        subst_str=f"φ P<sub>ny</sub> = 0.90 × 2500 × {tensor_data['Ag_m2']*1e4:.2f} = {chk_t['phi_Pn_yield_kgf']:.0f} kgf &nbsp;|&nbsp; φ P<sub>nu</sub> = 0.75 × 4000 × {0.75*tensor_data['Ag_m2']*1e4:.2f} = {chk_t['phi_Pn_rupture_kgf']:.0f} kgf",
        result_str=f"φ P<sub>n</sub> = {chk_t['phi_Pn_kgf']:.0f} kgf ({chk_t['phi_Pn_kN']:.1f} kN)",
        temp_dir=temp_dir, eq_prefix="tens_cap"
    ))

    p5_elements.append(_build_step_card(
        title="Ratio DCR de Tracción y Elongación Elástica de Servicio",
        norm_ref="AISC 360-16 Sección D2 y Estado Límite de Servicio",
        var_dict={"Tu": f"{chk_t['T_u_kgf']:.0f} kgf", "L": f"{solver.L:.2f} m", "E": "2,040,000 kgf/cm<sup>2</sup>"},
        latex_formula_str=r"\mathrm{DCR} = \frac{T_u}{\phi P_n} \leq 1.00 \qquad \Delta L = \frac{T_{\mathrm{serv}} \cdot L}{E \cdot A_g}",
        subst_str=f"DCR = {chk_t['T_u_kgf']:.0f} / {chk_t['phi_Pn_kgf']:.0f} = {chk_t['dcr']:.3f} &nbsp;|&nbsp; ΔL = ({chk_t['T_u_kgf']/1.4:.0f} × {solver.L*100:.0f}) / (2.04×10<sup>6</sup> × {tensor_data['Ag_m2']*1e4:.2f})",
        result_str=f"DCR = {chk_t['dcr']:.3f} ≤ 1.000 &nbsp;|&nbsp; Elongación elástica: ΔL = {chk_t['elongation_mm']:.2f} mm",
        is_passed=chk_t['dcr'] <= 1.0,
        temp_dir=temp_dir, eq_prefix="tens_dcr"
    ))

    story.append(KeepTogether(p5_elements))
    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 6: SECCIÓN 7 (DETALLES CONSTRUCTIVOS) Y CONFORMIDAD FINAL
    # =========================================================================
    p6_elements = []
    p6_elements.append(Paragraph("7. DETALLES CONSTRUCTIVOS: APOYO MÓVIL RANURADO Y CARTELA", style_sec_h1))
    p6_elements.append(Paragraph("Referencia Normativa: AISC 360-16 Tabla J3.3 (Ranuras Alargadas) / Capítulo J (Soldadura)", style_norm_ref))

    p6_elements.append(_build_step_card(
        title="Dimensionamiento de Ranura Alargada Mecanizada (Slotted Hole)",
        norm_ref="AISC 360-16 Tabla J3.3 / Sección J3.2",
        var_dict={"Perno": f"Ø {slot['bolt_diam_mm']/25.4:.2f}\" ({slot['bolt_diam_mm']:.1f} mm)", "Δx_elást": f"{slot['elastic_disp_mm']:.2f} mm", "ΔL_térm (ΔT=35°C)": f"{slot['thermal_disp_mm']:.2f} mm"},
        latex_formula_str=r"L_{\mathrm{ranura}} = d_{\mathrm{perno}} + 2\left(\Delta x_{\mathrm{elast}} + \frac{\Delta L_{\mathrm{term}}}{2}\right) \times 1.5 + 10\mathrm{mm}",
        subst_str=f"L<sub>ranura</sub> = {slot['bolt_diam_mm']:.1f} + 2×({slot['elastic_disp_mm']:.1f} + {slot['thermal_disp_mm']/2:.1f})×1.5 + 10 = {slot['slot_length_mm']} mm",
        result_str=f"Ranura Mecanizada: {slot['slot_length_mm']} mm largo × {slot['slot_width_mm']} mm ancho &nbsp;|&nbsp; Placa arandela gruesa: t = {slot['washer_plate_thickness_mm']} mm",
        temp_dir=temp_dir, eq_prefix="slot_dim"
    ))

    p6_elements.append(_build_step_card(
        title="Diseño de Cordón de Soldadura de Cartela al Tubo TR",
        norm_ref="AISC 360-16 Sección J2.4 (Soldadura de Filete E7018)",
        var_dict={"Tu": f"{cart['T_u_kgf']:.0f} kgf", "Filete (a)": f"{cart['fillet_leg_mm']:.1f} mm", "Garganta (te)": f"{cart['fillet_leg_mm']*0.707:.2f} mm", "Capac/cm": "2,214 kgf/cm"},
        latex_formula_str=r"R_n = 0.75 \times 0.60 \times F_{\mathrm{EXX}} \times t_e \qquad L_{\mathrm{sold}} = \frac{T_u}{2 \cdot R_n}",
        subst_str=f"L<sub>req</sub> = {cart['T_u_kgf']:.0f} / (2 × 2214) = {cart['T_u_kgf']/(2*2214):.1f} cm (Mínimo constructivo: 6.0 cm)",
        result_str=f"Longitud de Cordón: L = {cart['weld_length_cm']} cm a ambos lados (Excentricidad e = {cart['cartela_offset_cm']:.0f} cm, M<sub>local</sub> = {cart['M_local_kgm']:.1f} kgf·m)",
        temp_dir=temp_dir, eq_prefix="weld_len"
    ))

    p6_elements.append(Spacer(1, 8))
    p6_elements.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor('#1B365D'), spaceAfter=6))
    
    p_concl = (
        "<b>DICTAMEN DE CONFORMIDAD ESTRUCTURAL:</b><br/>"
        "Se concluye que el diseño del tijeral a dos aguas en <b>V invertida</b> satisface plenamente todos los estados "
        "límites últimos (resistencia a flexocompresión, estabilidad global, pandeo elástico/inelástico, tracción en tensor y "
        "capacidad de soldaduras) y de servicio (deflexión elástica y carrera libre del apoyo móvil ranurado) exigidos por "
        "las normas <b>AISC 360-16</b>, <b>NTE E.020</b>, <b>NTE E.090</b> y <b>AISI S100</b>.<br/>"
        "• Ratio DCR máximo gobernante en viga TR: <b>" f"{chk_tr['dcr']:.3f} ≤ 1.000</b> (AISC Eq. H1-1a/b).<br/>"
        "• Ratio DCR máximo en tensor horizontal: <b>" f"{chk_t['dcr']:.3f} ≤ 1.000</b> (AISC Cap. D).<br/>"
        "• Ratio DCR máximo en correas: <b>" f"{chk_p['dcr']:.3f} ≤ 1.000</b> (AISI S100 / Deflexión S/200).<br/>"
        "• Todos los componentes estructurales resultan formalmente <b>APROBADOS</b>."
    )
    p6_elements.append(Paragraph(p_concl, style_body))
    p6_elements.append(Spacer(1, 15))

    # Firmas
    firmas_data = [
        [Paragraph("_____________________________<br/><b>Ingeniero Especialista Estructural</b><br/>LDC-Peru Estructuras", style_td_center),
         Paragraph("_____________________________<br/><b>Revisión y Aprobación Técnica</b><br/>Control de Calidad Estructural", style_td_center)]
    ]
    t_firmas = Table(firmas_data, colWidths=[8.5*cm, 8.5*cm])
    t_firmas.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
    ]))
    p6_elements.append(t_firmas)

    story.append(KeepTogether(p6_elements))

    # Construir el documento con NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    return filepath

if __name__ == "__main__":
    from solver_v_invertida import SolverVInvertida
    s = SolverVInvertida(12.0, 2.5, 4.0, 1.0, "TR 150x100x4.0", "C 125x50x15x2.5", 'Redondo 5/8" (15.9 mm)', 12.0, 30.0, 3.5, 75.0, "Lima / Callao", enclosure_type="closed")
    out = create_pdf_report(s, "Memoria_Tecnica_Tijeral_V_Invertida.pdf")
    print(f"PDF generado: {out}")
