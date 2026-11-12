"""
Módulo para exportación de la estructura en V Invertida (Gable Frame) a DXF (AutoCAD).
Genera capas ordenadas para Vigas TR, Tensor, Correas C/U, Apoyo Ranurado y Cotas.
"""

import ezdxf
from ezdxf import colors

def export_v_invertida_to_dxf(filename, solver, results):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()

    # Capas
    layers = [
        ("VIGAS_TR", colors.RED, "CONTINUOUS"),
        ("TENSOR_HORIZONTAL", colors.BLUE, "CONTINUOUS"),
        ("PENDOLON_VERTICAL", colors.GREEN, "DASHED"),
        ("CORREAS_C_U", colors.MAGENTA, "CONTINUOUS"),
        ("APOYOS_DETALLE", colors.CYAN, "CONTINUOUS"),
        ("COTAS_TEXTOS", colors.WHITE, "CONTINUOUS"),
    ]

    for name, col, ltype in layers:
        if name not in doc.layers:
            layer = doc.layers.add(name)
            layer.color = col

    # 1. Dibujar Vigas Rafter TR
    for el in solver.elements:
        ni = solver.nodes[el['i']]
        nj = solver.nodes[el['j']]
        p1 = (ni['x'], ni['y'])
        p2 = (nj['x'], nj['y'])

        if 'rafter' in el['type']:
            msp.add_line(p1, p2, dxfattribs={'layer': 'VIGAS_TR'})
        elif el['type'] == 'tensor':
            msp.add_line(p1, p2, dxfattribs={'layer': 'TENSOR_HORIZONTAL'})
        elif el['type'] == 'hanger':
            msp.add_line(p1, p2, dxfattribs={'layer': 'PENDOLON_VERTICAL'})

    # 2. Dibujar Correas C o U sobre las vigas TR
    for p in solver.purlins:
        px, py = p['x'], p['y']
        size = 0.15 # 15 cm representación visual
        # Dibujar perfil C/U esquemático
        msp.add_lwpolyline(
            [(px - size/2, py), (px + size/2, py), (px + size/2, py + size), (px - size/2, py + size)],
            close=False, dxfattribs={'layer': 'CORREAS_C_U'}
        )

    # 3. Apoyo Fijo (Izquierdo en x=0, y=0)
    msp.add_lwpolyline([(0, 0), (-0.3, -0.4), (0.3, -0.4)], close=True, dxfattribs={'layer': 'APOYOS_DETALLE'})
    msp.add_line((-0.4, -0.4), (0.4, -0.4), dxfattribs={'layer': 'APOYOS_DETALLE'})
    msp.add_text("APOYO FIJO (PINNED)", dxfattribs={'layer': 'COTAS_TEXTOS', 'height': 0.14}).set_placement((-0.6, -0.65))

    # 4. Apoyo Móvil con Agujero Alargado (Derecho en x=L, y=0)
    L = solver.L
    slot = results['slot_design']
    msp.add_lwpolyline([(L, 0), (L - 0.3, -0.4), (L + 0.3, -0.4)], close=True, dxfattribs={'layer': 'APOYOS_DETALLE'})
    # Ruedas / ranura
    msp.add_circle((L - 0.18, -0.48), 0.08, dxfattribs={'layer': 'APOYOS_DETALLE'})
    msp.add_circle((L + 0.18, -0.48), 0.08, dxfattribs={'layer': 'APOYOS_DETALLE'})
    msp.add_line((L - 0.45, -0.56), (L + 0.45, -0.56), dxfattribs={'layer': 'APOYOS_DETALLE'})

    txt_slot = f"APOYO MOVIL (RANURA: {slot['slot_length_mm']} mm x {slot['slot_width_mm']} mm)"
    msp.add_text(txt_slot, dxfattribs={'layer': 'COTAS_TEXTOS', 'height': 0.14}).set_placement((L - 1.5, -0.85))

    # 5. Textos y Cotas
    msp.add_text(f"LUZ LIBRE = {solver.L:.2f} m", dxfattribs={'layer': 'COTAS_TEXTOS', 'height': 0.22}).set_placement((solver.L/2 - 1.0, -0.45))
    msp.add_text(f"ALTURA CUMBRERA = {solver.H:.2f} m (Pendiente = {solver.slope_pct:.1f}%)", dxfattribs={'layer': 'COTAS_TEXTOS', 'height': 0.20}).set_placement((solver.L/2 + 0.3, solver.H + 0.15))
    msp.add_text(f"VIGAS: {solver.tr_name}", dxfattribs={'layer': 'COTAS_TEXTOS', 'height': 0.18}).set_placement((solver.L/4 - 1.0, solver.H/2 + 0.3))
    msp.add_text(f"CORREAS: {solver.purlin_name} @ {solver.purlin_spacing:.2f}m", dxfattribs={'layer': 'COTAS_TEXTOS', 'height': 0.18}).set_placement((3*solver.L/4 - 1.0, solver.H/2 + 0.3))
    msp.add_text(f"TENSOR: {solver.tensor_name}", dxfattribs={'layer': 'COTAS_TEXTOS', 'height': 0.18}).set_placement((solver.L/2 - 1.2, 0.15))

    doc.saveas(filename)
    return True
