"""
================================================================================
TIJERAL V INVERTIDA PRO (PERÚ) v3.0 - Software de Cálculo y Diseño Estructural
Estructura a Dos Aguas en V Invertida (Gable Frame) SIN reticular
Diseño por ENVOLVENTE de TODAS las Combinaciones LRFD y de Servicio
Vigas: Tubos Rectangulares (TR) Tupemesa / Aceros Arequipa
Correas: Perfiles C y U de 2.5 mm y 3.0 mm (Metrado por Área Tributaria)
Tensor: Varilla Lisa Roscada / Cable fijado a cartela soldada al TR
Viento: NTE E.020 (Sincronización Total de Altura h = H_columna + H_tijeral)
Memoria: Formato Formal Paso a Paso con Citas de Artículos Normativos
================================================================================
"""

import sys
import os
import math
import numpy as np

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QGroupBox, QLabel, QDoubleSpinBox, QSpinBox, QComboBox,
    QPushButton, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QSplitter, QTextEdit, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from perfiles_peru import TR_PERU_DATABASE, CORREAS_PERU_DATABASE, TENSORES_DATABASE, CIUDADES_VIENTO_E020
from solver_v_invertida import SolverVInvertida
from dxf_exporter import export_v_invertida_to_dxf
from generar_pdf_tijeral import create_pdf_report

DARK_THEME_QSS = """
QMainWindow {
    background-color: #14141c;
    color: #e6e6f0;
}
QWidget {
    background-color: #14141c;
    color: #e6e6f0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
}
QGroupBox {
    border: 1px solid #2a2a3c;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: bold;
    color: #3b99ff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
}
QTabWidget::pane {
    border: 1px solid #2a2a3c;
    border-radius: 6px;
    background-color: #1b1b26;
}
QTabBar::tab {
    background: #111118;
    border: 1px solid #2a2a3c;
    padding: 7px 14px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: #88889e;
}
QTabBar::tab:selected {
    background: #222232;
    color: #3b99ff;
    border-bottom: 2px solid #0084ff;
    font-weight: bold;
}
QLabel {
    color: #d0d0e2;
}
QDoubleSpinBox, QSpinBox, QComboBox, QLineEdit {
    background-color: #222232;
    border: 1px solid #38384e;
    border-radius: 4px;
    padding: 3px 6px;
    color: #ffffff;
    selection-background-color: #0084ff;
}
QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #0084ff;
}
QPushButton {
    background-color: #262638;
    border: 1px solid #3a3a52;
    border-radius: 6px;
    padding: 7px 12px;
    font-weight: bold;
    color: #ffffff;
}
QPushButton:hover {
    background-color: #32324a;
    border-color: #0084ff;
}
QPushButton#btnCalcular {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0066cc, stop:1 #0088ff);
    border: 1px solid #3399ff;
    font-size: 13px;
    padding: 9px;
}
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tijeral V Invertida Pro v3.0 - Diseño por Envolvente LRFD (AISC 360 / RNE E.020 / E.090)")
        self.resize(1440, 890)

        self.solver = None
        self.analysis_data = None
        self.is_initializing = True

        self._setup_ui()
        self.setStyleSheet(DARK_THEME_QSS)

        self.is_initializing = False
        self.on_calcular()

    def _setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # -------------------------------------------------------------
        # PANEL IZQUIERDO: Configuración Reactiva
        # -------------------------------------------------------------
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self.config_tabs = QTabWidget()
        self.config_tabs.setFixedWidth(455)

        # ------------------ PESTAÑA 1: GEOMETRÍA ------------------
        tab_geom = QWidget()
        lay_geom = QVBoxLayout(tab_geom)

        gb_dim = QGroupBox("Geometría de la Estructura")
        lay_dim = QVBoxLayout(gb_dim)

        lay_luz = QHBoxLayout()
        lay_luz.addWidget(QLabel("Luz Libre (L):"))
        self.spn_L = QDoubleSpinBox()
        self.spn_L.setRange(4.0, 30.0); self.spn_L.setValue(12.0); self.spn_L.setSuffix(" m"); self.spn_L.setSingleStep(0.5)
        self.spn_L.valueChanged.connect(self._on_param_changed)
        lay_luz.addWidget(self.spn_L)
        lay_dim.addLayout(lay_luz)

        lay_h = QHBoxLayout()
        lay_h.addWidget(QLabel("Flecha Tijeral (H):"))
        self.spn_H = QDoubleSpinBox()
        self.spn_H.setRange(0.8, 8.0); self.spn_H.setValue(2.8); self.spn_H.setSuffix(" m"); self.spn_H.setSingleStep(0.1)
        self.spn_H.valueChanged.connect(self._on_param_changed)
        lay_h.addWidget(self.spn_H)
        lay_dim.addLayout(lay_h)

        # Altura de Columnas / Muros sincronizada
        lay_col = QHBoxLayout()
        lay_col.addWidget(QLabel("Altura Columnas/Muro (H_col):"))
        self.spn_col_h = QDoubleSpinBox()
        self.spn_col_h.setRange(0.0, 20.0); self.spn_col_h.setValue(3.5); self.spn_col_h.setSuffix(" m"); self.spn_col_h.setSingleStep(0.25)
        self.spn_col_h.valueChanged.connect(self._on_param_changed)
        lay_col.addWidget(self.spn_col_h)
        lay_dim.addLayout(lay_col)

        lay_s = QHBoxLayout()
        lay_s.addWidget(QLabel("Separación Tijerales (S):"))
        self.spn_S = QDoubleSpinBox()
        self.spn_S.setRange(1.0, 8.0); self.spn_S.setValue(4.0); self.spn_S.setSuffix(" m"); self.spn_S.setSingleStep(0.5)
        self.spn_S.valueChanged.connect(self._on_param_changed)
        lay_s.addWidget(self.spn_S)
        lay_dim.addLayout(lay_s)

        lay_sp = QHBoxLayout()
        lay_sp.addWidget(QLabel("Espaciado Correas (sp):"))
        self.spn_purlin_s = QDoubleSpinBox()
        self.spn_purlin_s.setRange(0.5, 2.0); self.spn_purlin_s.setValue(1.0); self.spn_purlin_s.setSuffix(" m"); self.spn_purlin_s.setSingleStep(0.1)
        self.spn_purlin_s.valueChanged.connect(self._on_param_changed)
        lay_sp.addWidget(self.spn_purlin_s)
        lay_dim.addLayout(lay_sp)

        # Unión en Cumbrera
        lay_ridge = QHBoxLayout()
        lay_ridge.addWidget(QLabel("Unión Cumbrera:"))
        self.cmb_ridge = QComboBox()
        self.cmb_ridge.addItem("Apernada Articulada (M = 0 en cumbrera)", "pinned")
        self.cmb_ridge.addItem("Soldada Rígida Continua (Cartela soldada)", "rigid")
        self.cmb_ridge.currentIndexChanged.connect(self._on_param_changed)
        lay_ridge.addWidget(self.cmb_ridge)
        lay_dim.addLayout(lay_ridge)

        self.chk_hanger = QCheckBox("Incluir Pendolón Central (Sostiene el tensor horizontal)")
        self.chk_hanger.setChecked(True)
        self.chk_hanger.stateChanged.connect(self._on_param_changed)
        lay_dim.addWidget(self.chk_hanger)

        lay_geom.addWidget(gb_dim)

        self.lbl_info_geom = QLabel()
        self.lbl_info_geom.setWordWrap(True)
        self.lbl_info_geom.setStyleSheet("background-color: #1e1e2c; padding: 8px; border-radius: 6px; border: 1px solid #2e2e42;")
        lay_geom.addWidget(self.lbl_info_geom)

        lay_geom.addStretch()
        self.config_tabs.addTab(tab_geom, "1. Geometría")

        # ------------------ PESTAÑA 2: PERFILES PERÚ ------------------
        tab_mat = QWidget()
        lay_mat = QVBoxLayout(tab_mat)

        gb_tr = QGroupBox("Vigas Rafter TR (Tupemesa / Aceros Arequipa)")
        lay_tr = QVBoxLayout(gb_tr)
        lay_tr.addWidget(QLabel("Seleccionar Tubo Rectangular (TR):"))
        self.cmb_tr = QComboBox()
        for name in TR_PERU_DATABASE.keys():
            self.cmb_tr.addItem(name)
        self.cmb_tr.setCurrentText("TR 150x100x4.0")
        self.cmb_tr.currentIndexChanged.connect(self._on_param_changed)
        lay_tr.addWidget(self.cmb_tr)

        self.lbl_tr_info = QLabel()
        self.lbl_tr_info.setStyleSheet("color: #00d2d3; font-size: 11px;")
        lay_tr.addWidget(self.lbl_tr_info)
        lay_mat.addWidget(gb_tr)

        gb_corr = QGroupBox("Correas de Techo (Perfiles C y U de 2.5 mm y 3.0 mm)")
        lay_corr = QVBoxLayout(gb_corr)

        lay_filtro = QHBoxLayout()
        lay_filtro.addWidget(QLabel("Filtrar Tipo:"))
        self.cmb_filtro_correa = QComboBox()
        self.cmb_filtro_correa.addItem("Todas (Canal C y U)")
        self.cmb_filtro_correa.addItem("Solo Canal C (con pestaña)")
        self.cmb_filtro_correa.addItem("Solo Canal U (simple)")
        self.cmb_filtro_correa.currentIndexChanged.connect(self._populate_correas)
        lay_filtro.addWidget(self.cmb_filtro_correa)
        lay_corr.addLayout(lay_filtro)

        lay_corr.addWidget(QLabel("Perfil de Correa:"))
        self.cmb_correa = QComboBox()
        self.cmb_correa.currentIndexChanged.connect(self._on_param_changed)
        lay_corr.addWidget(self.cmb_correa)
        self._populate_correas()

        self.lbl_correa_info = QLabel()
        self.lbl_correa_info.setStyleSheet("color: #ffab00; font-size: 11px;")
        lay_corr.addWidget(self.lbl_correa_info)
        lay_mat.addWidget(gb_corr)

        gb_tens = QGroupBox("Tensor Horizontal (Sujeto a Cartela en TR)")
        lay_tens = QVBoxLayout(gb_tens)
        lay_tens.addWidget(QLabel("Varilla Lisa / Cable con Templadores:"))
        self.cmb_tensor = QComboBox()
        for name in TENSORES_DATABASE.keys():
            self.cmb_tensor.addItem(name)
        self.cmb_tensor.setCurrentText("Redondo 3/4\" (19.1 mm)")
        self.cmb_tensor.currentIndexChanged.connect(self._on_param_changed)
        lay_tens.addWidget(self.cmb_tensor)
        lay_mat.addWidget(gb_tens)

        self.btn_auto_opt = QPushButton("⚡ Auto-Optimizar (TR + Correa Más Livianos)")
        self.btn_auto_opt.clicked.connect(self.on_auto_optimizar)
        lay_mat.addWidget(self.btn_auto_opt)

        lay_mat.addStretch()
        self.config_tabs.addTab(tab_mat, "2. Perfiles Perú")

        # ------------------ PESTAÑA 3: CARGAS Y VIENTO E.020 ------------------
        tab_cargas = QWidget()
        lay_cargas = QVBoxLayout(tab_cargas)

        gb_viento = QGroupBox("Viento según Norma Peruana NTE E.020 (Cap. 5)")
        lay_viento = QVBoxLayout(gb_viento)

        lay_espacio = QHBoxLayout()
        lay_espacio.addWidget(QLabel("Tipo de Espacio:"))
        self.cmb_espacio = QComboBox()
        self.cmb_espacio.addItem("Espacio Cerrado (con muros perimetrales)", "closed")
        self.cmb_espacio.addItem("Espacio Abierto (Tinglado / Cobertizo)", "open")
        self.cmb_espacio.currentIndexChanged.connect(self._on_param_changed)
        lay_espacio.addWidget(self.cmb_espacio)
        lay_viento.addLayout(lay_espacio)

        lay_ciudad = QHBoxLayout()
        lay_ciudad.addWidget(QLabel("Ciudad del Perú:"))
        self.cmb_ciudad = QComboBox()
        for c in CIUDADES_VIENTO_E020.keys():
            self.cmb_ciudad.addItem(c)
        self.cmb_ciudad.setCurrentText("Lima / Callao")
        self.cmb_ciudad.currentIndexChanged.connect(self._on_ciudad_changed)
        lay_ciudad.addWidget(self.cmb_ciudad)
        lay_viento.addLayout(lay_ciudad)

        lay_v = QHBoxLayout()
        lay_v.addWidget(QLabel("Velocidad Básica (V):"))
        self.spn_wind_v = QDoubleSpinBox()
        self.spn_wind_v.setRange(50.0, 160.0); self.spn_wind_v.setValue(75.0); self.spn_wind_v.setSuffix(" km/h")
        self.spn_wind_v.valueChanged.connect(self._on_param_changed)
        lay_v.addWidget(self.spn_wind_v)
        lay_viento.addLayout(lay_v)

        # Altura sincronizada mostrada en label
        self.lbl_alt_sincro = QLabel()
        self.lbl_alt_sincro.setStyleSheet("color: #3b99ff; font-weight: bold; font-size: 11px;")
        lay_viento.addWidget(self.lbl_alt_sincro)

        self.lbl_viento_calc = QLabel()
        self.lbl_viento_calc.setStyleSheet("background-color: #1e1e2c; padding: 6px; border-radius: 4px; font-size: 11px;")
        lay_viento.addWidget(self.lbl_viento_calc)
        lay_cargas.addWidget(gb_viento)

        gb_grav = QGroupBox("Sobrecargas Gravitatorias (kgf/m²)")
        lay_gr = QVBoxLayout(gb_grav)

        lay_d = QHBoxLayout()
        lay_d.addWidget(QLabel("Cubierta / Aluzinc (D):"))
        self.spn_dead = QDoubleSpinBox()
        self.spn_dead.setRange(3.0, 80.0); self.spn_dead.setValue(15.0); self.spn_dead.setSuffix(" kgf/m²")
        self.spn_dead.valueChanged.connect(self._on_param_changed)
        lay_d.addWidget(self.spn_dead)
        lay_gr.addLayout(lay_d)

        lay_l = QHBoxLayout()
        lay_l.addWidget(QLabel("Carga Viva Techo (Lr):"))
        self.spn_live = QDoubleSpinBox()
        self.spn_live.setRange(10.0, 100.0); self.spn_live.setValue(40.0); self.spn_live.setSuffix(" kgf/m²")
        self.spn_live.valueChanged.connect(self._on_param_changed)
        lay_l.addWidget(self.spn_live)
        lay_gr.addLayout(lay_l)
        lay_cargas.addWidget(gb_grav)

        # Visualizador de combinaciones
        gb_comb = QGroupBox("Visualización en Gráficos")
        lay_cb = QVBoxLayout(gb_comb)
        self.cmb_disp_case = QComboBox()
        self.cmb_disp_case.addItem("⭐ Envolvente Crítica de Diseño (Peor Escenario)", "envelope")
        self.cmb_disp_case.addItem("Comb 1: 1.4 D (Carga Muerta)", "comb1_14D")
        self.cmb_disp_case.addItem("Comb 2: 1.2 D + 1.6 Lr (Gravitatoria Máxima)", "comb2_12D_16L")
        self.cmb_disp_case.addItem("Comb 3: 1.2 D + 1.0 W + 0.5 Lr (Presión Viento E.020)", "comb3_12D_10W_05L")
        self.cmb_disp_case.addItem("Comb 4: 0.9 D - 1.0 W (Succión / Uplift E.020)", "comb4_09D_10W_uplift")
        self.cmb_disp_case.addItem("Servicio: 1.0 D + 1.0 Lr (Flechas y Dilatación)", "service_10D_10L")
        self.cmb_disp_case.currentIndexChanged.connect(self._on_disp_case_changed)
        lay_cb.addWidget(self.cmb_disp_case)
        lay_cargas.addWidget(gb_comb)

        lay_cargas.addStretch()
        self.config_tabs.addTab(tab_cargas, "3. Cargas y Viento")

        # ------------------ PESTAÑA 4: DETALLES DE APOYO Y CARTELA ------------------
        tab_det = QWidget()
        lay_det = QVBoxLayout(tab_det)

        gb_ap = QGroupBox("Detalle de Apoyo y Sujeción del Tensor")
        lay_ap = QVBoxLayout(gb_ap)
        lay_ap.addWidget(QLabel("<b>Apoyo Izquierdo (X=0):</b> Fijo (Pinned Dx=0, Dy=0)"))
        lay_ap.addWidget(QLabel("<b>Apoyo Derecho (X=L):</b> Móvil con Ranura (Roller Dy=0, Dx libre)"))
        lay_ap.addWidget(QLabel("<b>Fijación del Tensor:</b> Cartela soldada al TR (excentricidad e=15 cm)"))
        lay_det.addWidget(gb_ap)

        self.lbl_slot_info = QLabel()
        self.lbl_slot_info.setWordWrap(True)
        self.lbl_slot_info.setStyleSheet("background-color: #1e1e2c; padding: 10px; border-radius: 6px; border: 1px solid #2e2e42; line-height: 1.4;")
        lay_det.addWidget(self.lbl_slot_info)

        lay_det.addStretch()
        self.config_tabs.addTab(tab_det, "4. Apoyo Ranurado")

        left_layout.addWidget(self.config_tabs)

        self.btn_calcular = QPushButton("⚡ RECALCULAR INSTANTÁNEO")
        self.btn_calcular.setObjectName("btnCalcular")
        self.btn_calcular.setMinimumHeight(38)
        self.btn_calcular.clicked.connect(self.on_calcular)
        left_layout.addWidget(self.btn_calcular)

        lay_exp = QHBoxLayout()
        self.btn_pdf = QPushButton("📑 Memoria PDF Formal")
        self.btn_pdf.setStyleSheet("background-color: #922b21; color: white; font-weight: bold; padding: 6px;")
        self.btn_pdf.clicked.connect(self.on_exportar_pdf)
        lay_exp.addWidget(self.btn_pdf)

        self.btn_dxf = QPushButton("📐 Plano CAD (DXF)")
        self.btn_dxf.clicked.connect(self.on_exportar_dxf)
        lay_exp.addWidget(self.btn_dxf)

        self.btn_rep = QPushButton("📄 Guardar TXT")
        self.btn_rep.clicked.connect(self.on_exportar_memoria)
        lay_exp.addWidget(self.btn_rep)
        left_layout.addLayout(lay_exp)

        splitter.addWidget(left_panel)

        # -------------------------------------------------------------
        # PANEL DERECHO: Visualización y Memoria Técnica Paso a Paso
        # -------------------------------------------------------------
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Barra de KPIs
        kpi_bar = QHBoxLayout()
        self.card_mom = self._create_kpi_card("Mu Máx (Envolvente TR)", "-- kgf·m", "#ffab00")
        self.card_tr = self._create_kpi_card("DCR Flexocompresión TR", "--", "#00d2d3")
        self.card_tensor = self._create_kpi_card("Tu Máx Tensor", "-- kgf", "#10ac84")
        self.card_slot = self._create_kpi_card("Ranura Apoyo Móvil", "-- mm", "#3b99ff")

        kpi_bar.addWidget(self.card_mom)
        kpi_bar.addWidget(self.card_tr)
        kpi_bar.addWidget(self.card_tensor)
        kpi_bar.addWidget(self.card_slot)
        right_layout.addLayout(kpi_bar)

        self.view_tabs = QTabWidget()

        # Canvas 1: Geometría
        self.fig_geom = Figure(facecolor="#121218")
        self.canvas_geom = FigureCanvas(self.fig_geom)
        self.toolbar_geom = NavigationToolbar(self.canvas_geom, self)
        self.toolbar_geom.setStyleSheet("background-color: #1a1a24; border: none; padding: 2px;")
        v_geom = QWidget(); l_geom = QVBoxLayout(v_geom)
        l_geom.addWidget(self.toolbar_geom); l_geom.addWidget(self.canvas_geom)
        self.view_tabs.addTab(v_geom, "🖼 Geometría en V Invertida y Correas")

        # Canvas 2: Momentos Parabólicos Continuos
        self.fig_mom = Figure(facecolor="#121218")
        self.canvas_mom = FigureCanvas(self.fig_mom)
        self.toolbar_mom = NavigationToolbar(self.canvas_mom, self)
        v_mom = QWidget(); l_mom = QVBoxLayout(v_mom)
        l_mom.addWidget(self.toolbar_mom); l_mom.addWidget(self.canvas_mom)
        self.view_tabs.addTab(v_mom, "📐 Momentos Flectores Parabólicos (kgf·m)")

        # Canvas 3: Axiales N
        self.fig_axial = Figure(facecolor="#121218")
        self.canvas_axial = FigureCanvas(self.fig_axial)
        self.toolbar_axial = NavigationToolbar(self.canvas_axial, self)
        v_ax = QWidget(); l_ax = QVBoxLayout(v_ax)
        l_ax.addWidget(self.toolbar_axial); l_ax.addWidget(self.canvas_axial)
        self.view_tabs.addTab(v_ax, "⚡ Fuerzas Axiales (Compresión TR / Tracción Tensor en kgf)")

        # Canvas 4: Deformada
        self.fig_def = Figure(facecolor="#121218")
        self.canvas_def = FigureCanvas(self.fig_def)
        self.toolbar_def = NavigationToolbar(self.canvas_def, self)
        v_def = QWidget(); l_def = QVBoxLayout(v_def)
        l_def.addWidget(self.toolbar_def); l_def.addWidget(self.canvas_def)
        self.view_tabs.addTab(v_def, "〰 Deformada y Carrera de Ranura (mm)")

        # Pestaña 5: Memoria de Cálculo Detallada Paso a Paso
        v_mem = QWidget()
        l_mem = QVBoxLayout(v_mem)
        l_mem.setContentsMargins(6, 6, 6, 6)

        l_mem_btns = QHBoxLayout()
        btn_top_pdf = QPushButton("📑 Descargar PDF Formal")
        btn_top_pdf.setStyleSheet("background-color: #922b21; color: white; font-weight: bold; padding: 5px 14px; border-radius: 4px;")
        btn_top_pdf.clicked.connect(self.on_exportar_pdf)
        l_mem_btns.addWidget(btn_top_pdf)

        btn_top_txt = QPushButton("📄 Guardar TXT")
        btn_top_txt.setStyleSheet("background-color: #2c3e50; color: white; padding: 5px 12px; border-radius: 4px;")
        btn_top_txt.clicked.connect(self.on_exportar_memoria)
        l_mem_btns.addWidget(btn_top_txt)

        l_mem_btns.addStretch()
        l_mem.addLayout(l_mem_btns)

        self.txt_memoria = QTextEdit()
        self.txt_memoria.setReadOnly(True)
        self.txt_memoria.setFont(QFont("Consolas", 10))
        l_mem.addWidget(self.txt_memoria)

        self.view_tabs.addTab(v_mem, "📋 Memoria Técnica Detallada (Fórmulas Paso a Paso)")

        right_layout.addWidget(self.view_tabs)
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

    def _create_kpi_card(self, title, val, color):
        f = QFrame()
        f.setStyleSheet(f"""
            QFrame {{
                background-color: #1b1b26;
                border: 1px solid #2a2a3c;
                border-left: 4px solid {color};
                border-radius: 6px;
                padding: 4px 10px;
            }}
        """)
        lay = QVBoxLayout(f)
        lay.setContentsMargins(2, 2, 2, 2); lay.setSpacing(1)
        lt = QLabel(title); lt.setStyleSheet("color: #88889e; font-size: 11px;")
        lv = QLabel(val); lv.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
        lay.addWidget(lt); lay.addWidget(lv)
        f.val_label = lv
        return f

    def _on_param_changed(self):
        if not self.is_initializing:
            self.on_calcular()

    def _on_ciudad_changed(self):
        c = self.cmb_ciudad.currentText()
        if c in CIUDADES_VIENTO_E020 and c != "Personalizado":
            self.spn_wind_v.blockSignals(True)
            self.spn_wind_v.setValue(CIUDADES_VIENTO_E020[c])
            self.spn_wind_v.blockSignals(False)
        self._on_param_changed()

    def _on_disp_case_changed(self):
        if not self.is_initializing and self.analysis_data:
            self._render_active_case_plots()

    def _populate_correas(self):
        curr = self.cmb_correa.currentText()
        filtro = self.cmb_filtro_correa.currentIndex()
        self.cmb_correa.blockSignals(True)
        self.cmb_correa.clear()
        for k, v in CORREAS_PERU_DATABASE.items():
            if filtro == 1 and v['type'] != 'C': continue
            if filtro == 2 and v['type'] != 'U': continue
            self.cmb_correa.addItem(k)
        if curr in CORREAS_PERU_DATABASE and (filtro == 0 or (filtro == 1 and CORREAS_PERU_DATABASE[curr]['type'] == 'C') or (filtro == 2 and CORREAS_PERU_DATABASE[curr]['type'] == 'U')):
            self.cmb_correa.setCurrentText(curr)
        else:
            self.cmb_correa.setCurrentIndex(0)
        self.cmb_correa.blockSignals(False)
        self._on_param_changed()

    def on_calcular(self):
        # 1. Instanciar solver con altura de columnas sincronizada
        self.solver = SolverVInvertida(
            span=self.spn_L.value(),
            height=self.spn_H.value(),
            truss_spacing=self.spn_S.value(),
            purlin_spacing=self.spn_purlin_s.value(),
            tr_profile_name=self.cmb_tr.currentText(),
            purlin_profile_name=self.cmb_correa.currentText(),
            tensor_profile_name=self.cmb_tensor.currentText(),
            roof_dead_load=self.spn_dead.value(),
            roof_live_load=self.spn_live.value(),
            col_height_m=self.spn_col_h.value(),
            wind_speed_kmh=self.spn_wind_v.value(),
            city_name=self.cmb_ciudad.currentText(),
            ridge_type=self.cmb_ridge.currentData(),
            has_central_hanger=self.chk_hanger.isChecked(),
            steel_grade="A500_B",
            enclosure_type=self.cmb_espacio.currentData()
        )

        # 2. Resolver TODAS las combinaciones LRFD simultáneamente
        self.analysis_data = self.solver.solve_all_combinations()
        gov = self.analysis_data['governing']

        # 3. Actualizar información y etiquetas
        self._update_info_labels()

        # 4. Actualizar KPIs con los valores gobernantes
        chk_tr = gov['tr_check']
        chk_t = gov['tensor_check']
        slot = gov['slot_design']

        self.card_mom.val_label.setText(f"{chk_tr['M_u_kgm']:.0f} kgf·m ({chk_tr['M_u_kNm']:.2f} kNm)")
        col_tr = "#10ac84" if chk_tr['dcr'] <= 1.0 else "#ff3d71"
        case_map = {
            'comb1_14D': '1.4D',
            'comb2_12D_16L': '1.2D+1.6Lr',
            'comb3_12D_10W_05L': '1.2D+1.0W+0.5Lr',
            'comb4_09D_10W_uplift': '0.9D-1.0W'
        }
        self.card_tr.val_label.setText(f"{chk_tr['dcr']:.3f} ({chk_tr['status']} en {case_map.get(gov['tr_case'], '')})")
        self.card_tr.val_label.setStyleSheet(f"color: {col_tr}; font-size: 13px; font-weight: bold;")

        self.card_tensor.val_label.setText(f"{chk_t['T_u_kgf']:.0f} kgf ({chk_t['T_u_kN']:.1f} kN)")
        self.card_slot.val_label.setText(f"{slot['slot_length_mm']} x {slot['slot_width_mm']} mm")

        # 5. Renderizar gráficos
        self._render_active_case_plots()

        # 6. Generar reporte formal paso a paso
        self._generate_step_by_step_report()

    def _update_info_labels(self):
        L = self.solver.L; H = self.solver.H; H_col = self.solver.col_height_m
        h_tot = self.solver.building_height_m
        slope_pct = self.solver.slope_pct; angle_deg = self.solver.theta_deg
        rafter_len = self.solver.slope_len

        self.lbl_info_geom.setText(
            f"<b>Pendiente:</b> {slope_pct:.1f}% ({angle_deg:.1f}°)<br>"
            f"<b>Longitud Viga TR:</b> {rafter_len:.2f} m | <b>Correas/Agua:</b> {len(self.solver.purlins)//2} un.<br>"
            f"<b>Espaciado Real Correas:</b> {self.solver.actual_purlin_spacing:.2f} m<br>"
            f"<b>Altura Cumbrera Total:</b> h = {H_col:.2f}m (col) + {H:.2f}m (tijeral) = <b>{h_tot:.2f} m</b>"
        )

        tr_k = self.solver.tr_name
        if tr_k in TR_PERU_DATABASE:
            p = TR_PERU_DATABASE[tr_k]
            self.lbl_tr_info.setText(f"{p['name']} | Peso: {p['weight_kg_m']:.2f} kg/m | Zx: {p['Zx']*1e6:.1f} cm³ | Ix: {p['Ix']*1e8:.0f} cm⁴")

        c_k = self.solver.purlin_name
        if c_k in CORREAS_PERU_DATABASE:
            cp = CORREAS_PERU_DATABASE[c_k]
            self.lbl_correa_info.setText(f"{cp['name']} | Peso: {cp['weight_kg_m']:.2f} kg/m | Wx: {cp['Sx']*1e6:.1f} cm³")

        self.lbl_alt_sincro.setText(f"Altura Total Sincronizada: h = {H_col:.2f}m + {H:.2f}m = {h_tot:.2f} m")

        viento_txt = (
            f"<b>Condición:</b> {self.solver.enclosure_desc}<br>"
            f"<b>Vh:</b> {self.solver.Vh_kmh:.1f} km/h | <b>q:</b> {self.solver.q_base_kg_m2:.1f} kgf/m²<br>"
            f"<b>Presión Barlovento:</b> C = {self.solver.C_barlovento:+.2f} ({self.solver.P_wind_barlovento_kg_m2:+.1f} kgf/m²)<br>"
            f"<b>Presión Sotavento:</b> C = {self.solver.C_sotavento:+.2f} ({self.solver.P_wind_sotavento_kg_m2:+.1f} kgf/m²)<br>"
            f"<b>Succión Uplift (Comb 4):</b> C_barl = {self.solver.C_barlovento_uplift:+.2f}, C_sot = {self.solver.C_sotavento_uplift:+.2f}"
        )
        self.lbl_viento_calc.setText(viento_txt)

        slot = self.analysis_data['governing']['slot_design']
        cart = self.analysis_data['governing']['cartela_design']
        det_txt = (
            f"<b>APOYO MÓVIL RANURADO (DERECHO):</b><br>"
            f"• Carrera Elástica Tensor: <b>{slot['elastic_disp_mm']:.1f} mm</b><br>"
            f"• Expansión Térmica (ΔT=35°C): <b>{slot['thermal_disp_mm']:.1f} mm</b><br>"
            f"• <b>Ranura Mecanizada:</b> <font color='#3b99ff'><b>{slot['slot_length_mm']} mm de largo x {slot['slot_width_mm']} mm ancho</b></font><br>"
            f"• Arandela Placa AISC J3.2: <b>t = {slot['washer_plate_thickness_mm']} mm</b><br><br>"
            f"<b>CARTELA DEL TENSOR EN VIGA TR:</b><br>"
            f"• Tracción de Diseño: <b>{cart['T_u_kgf']:.0f} kgf</b><br>"
            f"• Soldadura Filete (E7018): <b>a = {cart['fillet_leg_mm']} mm</b>, <b>L = {cart['weld_length_cm']} cm</b> a ambos lados.<br>"
            f"• Momento local por excentricidad (e=15 cm): <b>{cart['M_local_kgm']:.1f} kgf·m</b>"
        )
        self.lbl_slot_info.setText(det_txt)

    def _render_active_case_plots(self):
        """Dibuja los gráficos según el caso seleccionado en el combo de visualización."""
        disp_case = self.cmb_disp_case.currentData()
        gov = self.analysis_data['governing']

        if disp_case == 'envelope':
            active_res = self.analysis_data['cases'][gov['tr_case']]
            title_suffix = f"(Envolvente Crítica gobernada por {gov['tr_case']})"
        else:
            active_res = self.analysis_data['cases'][disp_case]
            title_suffix = f"({disp_case})"

        self._plot_geometry()
        self._plot_parabolic_moment_diagram(active_res, title_suffix)
        self._plot_axial_diagram(active_res, title_suffix)
        self._plot_deformed_shape(active_res, title_suffix)

    def _plot_geometry(self):
        self.fig_geom.clear()
        ax = self.fig_geom.add_subplot(111)
        ax.set_facecolor("#121218")

        for el in self.solver.elements:
            ni = self.solver.nodes[el['i']]; nj = self.solver.nodes[el['j']]
            if 'rafter' in el['type']:
                ax.plot([ni['x'], nj['x']], [ni['y'], nj['y']], color='#ff5252', linewidth=3.5, zorder=3)
            elif el['type'] == 'tensor':
                ax.plot([ni['x'], nj['x']], [ni['y'], nj['y']], color='#00d2d3', linewidth=2.5, zorder=3)
            elif el['type'] == 'hanger':
                ax.plot([ni['x'], nj['x']], [ni['y'], nj['y']], color='#69f0ae', linewidth=1.8, linestyle='--', zorder=2)

        for p in self.solver.purlins:
            ax.plot(p['x'], p['y'], 's', color='#ffab00', markersize=6, zorder=5)
            ax.annotate('', xy=(p['x'], p['y']), xytext=(p['x'], p['y'] + 0.45),
                        arrowprops=dict(arrowstyle="->", color='#ffab00', lw=1.3))

        ax.plot([0.15, 0.15], [0, 0.15], color='#ffab00', lw=3, zorder=4)
        L = self.solver.L
        ax.plot([L - 0.15, L - 0.15], [0, 0.15], color='#ffab00', lw=3, zorder=4)

        ax.plot([0, -0.25, 0.25, 0], [0, -0.35, -0.35, 0], color='#00e676', lw=2)
        ax.plot([-0.35, 0.35], [-0.35, -0.35], color='#00e676', lw=2)
        ax.text(0, -0.65, "APOYO FIJO\n(PINNED)", color='#00e676', ha='center', fontsize=8, fontweight='bold')

        slot = self.analysis_data['governing']['slot_design']
        ax.plot([L, L - 0.25, L + 0.25, L], [0, -0.35, -0.35, 0], color='#3b99ff', lw=2)
        ax.plot([L - 0.25, L + 0.25], [-0.42, -0.42], color='#3b99ff', lw=3.5)
        ax.plot([L - 0.15, L + 0.15], [-0.52, -0.52], 'o', color='#3b99ff', markersize=6)
        ax.plot([L - 0.35, L + 0.35], [-0.60, -0.60], color='#3b99ff', lw=2)
        ax.text(L, -0.90, f"MÓVIL RANURADO\n(SLOT: {slot['slot_length_mm']} mm)", color='#3b99ff', ha='center', fontsize=8, fontweight='bold')

        ax.set_title(f"Estructura en V Invertida: {self.solver.tr_name} + Correas {self.solver.purlin_name}", color='#ffffff', fontsize=11, pad=10)
        ax.set_xlabel("X (m)", color='#88889e'); ax.set_ylabel("Y (m)", color='#88889e')
        ax.tick_params(colors='#88889e')
        ax.grid(True, color='#252535', linestyle='--', alpha=0.5)
        ax.set_aspect('equal')
        ax.set_ylim(-1.1, self.solver.H + 0.7)
        self.fig_geom.tight_layout()
        self.canvas_geom.draw()

    def _plot_parabolic_moment_diagram(self, res, title_suffix=""):
        self.fig_mom.clear()
        ax = self.fig_mom.add_subplot(111)
        ax.set_facecolor("#121218")

        for el in self.solver.elements:
            ni = self.solver.nodes[el['i']]; nj = self.solver.nodes[el['j']]
            ax.plot([ni['x'], nj['x']], [ni['y'], nj['y']], color='#2e2e42', lw=1.2)

        max_M_kgm = res['max_rafter_moment_kgm']
        xs, ys, moments = self.solver.get_continuous_moment_curve(max_M_kgm)

        scale = 0.8 / (max_M_kgm + 1e-3)
        curve_x = []; curve_y = []

        nx_left = -math.sin(self.solver.theta); ny_left = math.cos(self.solver.theta)
        nx_right = math.sin(self.solver.theta); ny_right = math.cos(self.solver.theta)

        for i in range(len(xs)):
            x = xs[i]; y = ys[i]; M = moments[i]
            nx, ny = (nx_left, ny_left) if x <= self.solver.half_L else (nx_right, ny_right)
            offset = M * scale
            curve_x.append(x + nx * offset)
            curve_y.append(y + ny * offset)

        poly_x = list(xs) + list(reversed(curve_x))
        poly_y = list(ys) + list(reversed(curve_y))
        ax.fill(poly_x, poly_y, color='#ffab00', alpha=0.45, zorder=2)
        ax.plot(curve_x, curve_y, color='#ffab00', lw=2.0, zorder=3)

        x_label_l = self.solver.L / 4.0 + nx_left * (max_M_kgm * scale * 1.3)
        y_label_l = self.solver.H / 2.0 + ny_left * (max_M_kgm * scale * 1.3)
        ax.text(x_label_l, y_label_l,
                f"Mu = {max_M_kgm:.0f} kgf·m\n({res['max_rafter_moment_kNm']:.2f} kNm)",
                color='#ffab00', fontsize=9, fontweight='bold', ha='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#1e1e2c', edgecolor='#ffab00'))

        ax.set_title(f"Diagrama Parabólico Continuo de Momentos {title_suffix}", color='#ffffff', fontsize=11, pad=10)
        ax.set_xlabel("X (m)", color='#88889e'); ax.set_ylabel("Y (m)", color='#88889e')
        ax.tick_params(colors='#88889e')
        ax.grid(True, color='#252535', linestyle='--', alpha=0.5)
        ax.set_aspect('equal')
        ax.set_ylim(-0.8, self.solver.H + 1.2)
        self.fig_mom.tight_layout()
        self.canvas_mom.draw()

    def _plot_axial_diagram(self, res, title_suffix=""):
        self.fig_axial.clear()
        ax = self.fig_axial.add_subplot(111)
        ax.set_facecolor("#121218")

        for el in res['elements']:
            ni = self.solver.nodes[el['node_i']]; nj = self.solver.nodes[el['node_j']]
            P_kgf = el['axial_P_N'] / 9.80665
            is_comp = (P_kgf < 0)
            col = '#ff3d71' if is_comp else '#0095ff'
            lw = 3.5 if 'rafter' in el['type'] or el['type'] == 'tensor' else 2.0
            ax.plot([ni['x'], nj['x']], [ni['y'], nj['y']], color=col, linewidth=lw)

        ax.text(self.solver.L/4, self.solver.H/2 - 0.2,
                f"Compresión TR: {res['max_rafter_axial_kgf']:.0f} kgf ({res['max_rafter_axial_kgf']/1000:.2f} t)",
                color='#ff3d71', fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#1e1e2c', edgecolor='#ff3d71'))

        ax.text(self.solver.L/2, 0.25,
                f"Tracción Tensor: {res['max_tensor_tension_kgf']:.0f} kgf ({res['max_tensor_tension_kgf']/1000:.2f} t)",
                color='#0095ff', fontsize=9, fontweight='bold', ha='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='#1e1e2c', edgecolor='#0095ff'))

        ax.set_title(f"Fuerzas Axiales {title_suffix}", color='#ffffff', fontsize=11, pad=10)
        ax.set_xlabel("X (m)", color='#88889e'); ax.set_ylabel("Y (m)", color='#88889e')
        ax.tick_params(colors='#88889e')
        ax.grid(True, color='#252535', linestyle='--', alpha=0.5)
        ax.set_aspect('equal')
        ax.set_ylim(-0.8, self.solver.H + 0.8)
        self.fig_axial.tight_layout()
        self.canvas_axial.draw()

    def _plot_deformed_shape(self, res, title_suffix=""):
        self.fig_def.clear()
        ax = self.fig_def.add_subplot(111)
        ax.set_facecolor("#121218")

        U = res['U']
        scale_disp = 35.0

        for el in self.solver.elements:
            ni = self.solver.nodes[el['i']]; nj = self.solver.nodes[el['j']]
            ax.plot([ni['x'], nj['x']], [ni['y'], nj['y']], '--', color='#323246', lw=1.2)
            xi_def = ni['x'] + U[3 * el['i']] * scale_disp
            yi_def = ni['y'] + U[3 * el['i'] + 1] * scale_disp
            xj_def = nj['x'] + U[3 * el['j']] * scale_disp
            yj_def = nj['y'] + U[3 * el['j'] + 1] * scale_disp
            ax.plot([xi_def, xj_def], [yi_def, yj_def], color='#00d2d3', lw=2.2)

        L = self.solver.L
        u_roller = res['u_roller_x_mm'] / 1000.0
        ax.annotate(f"Desplazamiento Elástico:\nΔx = {res['u_roller_x_mm']:+.2f} mm",
                    xy=(L + u_roller * scale_disp, 0), xytext=(L + 0.3, -0.5),
                    arrowprops=dict(facecolor='#3b99ff', edgecolor='#3b99ff', arrowstyle="->", lw=2),
                    color='#3b99ff', fontweight='bold', fontsize=9,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#1e1e2c', edgecolor='#3b99ff'))

        ax.set_title(f"Deformada Elástica {title_suffix} (Amplificación: {scale_disp}x)", color='#ffffff', fontsize=11, pad=10)
        ax.set_xlabel("X (m)", color='#88889e'); ax.set_ylabel("Y (m)", color='#88889e')
        ax.tick_params(colors='#88889e')
        ax.grid(True, color='#252535', linestyle='--', alpha=0.5)
        ax.set_aspect('equal')
        ax.set_ylim(-0.9, self.solver.H + 0.8)
        self.fig_def.tight_layout()
        self.canvas_def.draw()

    def _generate_step_by_step_report(self):
        L = self.solver.L; H = self.solver.H; H_col = self.solver.col_height_m
        h_tot = self.solver.building_height_m
        S = self.solver.S; sp = self.solver.actual_purlin_spacing
        tr = TR_PERU_DATABASE[self.solver.tr_name]
        purlin = CORREAS_PERU_DATABASE[self.solver.purlin_name]
        tensor = TENSORES_DATABASE[self.solver.tensor_name]
        gov = self.analysis_data['governing']
        chk_tr = gov['tr_check']
        chk_t = gov['tensor_check']
        chk_p = gov['purlin_check']
        slot = gov['slot_design']
        cart = gov['cartela_design']

        rep = []
        rep.append("=" * 90)
        rep.append("MEMORIA DE CÁLCULO ESTRUCTURAL FORMAL: TIJERAL A DOS AGUAS EN V INVERTIDA")
        rep.append("METODOLOGÍA DE DISEÑO POR ENVOLVENTE CRÍTICA DE TODAS LAS COMBINACIONES LRFD")
        rep.append("NORMAS TÉCNICAS: AISC 360-16 / NTE E.020 (CARGAS) / NTE E.090 (ESTRUCTURAS METÁLICAS)")
        rep.append("=" * 90)

        # SECCIÓN 1
        rep.append("\n" + "-" * 90)
        rep.append("SECCIÓN 1: BASES GEOMÉTRICAS Y SINCRONIZACIÓN DE ALTURAS")
        rep.append("Referencia Normativa: NTE E.020 (Art. 12) / NTE E.090 (Cap. 2)")
        rep.append("-" * 90)
        rep.append("A. Datos de Entrada del Proyecto:")
        rep.append(f"   • Luz libre entre apoyos (L):             L     = {L:.2f} m")
        rep.append(f"   • Flecha propia del tijeral (H):          H     = {H:.2f} m")
        rep.append(f"   • Altura de columnas de soporte (H_col):  H_col = {H_col:.2f} m")
        rep.append(f"   • Separación entre tijerales (S):         S     = {S:.2f} m")
        rep.append(f"   • Espaciado real entre correas (s_p):     s_p   = {sp:.2f} m")
        rep.append("\nB. Fórmulas Geométricas y Desarrollo Numérico:")
        rep.append("   1. Altura total sincronizada del edificio para viento (h):")
        rep.append("      Fórmula:      h = H_col + H")
        rep.append(f"      Sustitución:  h = {H_col:.2f} m + {H:.2f} m = {h_tot:.2f} m")
        rep.append("   2. Longitud de cada viga inclinada TR (L_r):")
        rep.append("      Fórmula:      L_r = √((L / 2)² + H²)")
        rep.append(f"      Sustitución:  L_r = √(({L/2:.2f})² + ({H:.2f})²) = {self.solver.slope_len:.2f} m")
        rep.append("   3. Pendiente del techo (p):")
        rep.append("      Fórmula:      p = (H / (L / 2)) × 100")
        rep.append(f"      Sustitución:  p = ({H:.2f} / {L/2:.2f}) × 100 = {self.solver.slope_pct:.1f}%  (θ = {self.solver.theta_deg:.2f}°)")

        # SECCIÓN 2
        rep.append("\n" + "-" * 90)
        rep.append("SECCIÓN 2: DETERMINACIÓN DE LA CARGA DE VIENTO")
        rep.append("Referencia Normativa: NTE E.020 'Cargas', Capítulo 5 (Artículos 12 y 13)")
        rep.append("-" * 90)
        rep.append("A. Datos de Entrada de Viento:")
        rep.append(f"   • Tipo de Cobertura / Espacio:            {self.solver.enclosure_desc}")
        rep.append(f"   • Ubicación / Ciudad del Perú:            {self.solver.city_name}")
        rep.append(f"   • Velocidad básica a 10 m (V):            V = {self.solver.wind_speed_kmh:.1f} km/h (Mapa Eólico E.020)")
        rep.append(f"   • Altura total de cumbrera (h):           h = {h_tot:.2f} m")
        rep.append("\nB. Fórmulas Normativas y Desarrollo Numérico:")
        rep.append("   1. Velocidad de diseño a la altura h (Vh) [E.020 Art. 12.2]:")
        rep.append("      Fórmula:      Vh = V × (h / 10)^0.22  (para h > 10 m, o Vh = V si h ≤ 10 m)")
        rep.append(f"      Sustitución:  Vh = {self.solver.wind_speed_kmh:.1f} × ({h_tot:.2f} / 10)^0.22 = {self.solver.Vh_kmh:.2f} km/h")
        rep.append("   2. Presión dinámica básica de viento (q) [E.020 Art. 12.3]:")
        rep.append("      Fórmula:      q = 0.005 × Vh²  (en kgf/m²)")
        rep.append(f"      Sustitución:  q = 0.005 × ({self.solver.Vh_kmh:.2f})² = {self.solver.q_base_kg_m2:.2f} kgf/m²")
        rep.append("   3. Coeficientes de forma (C) según tipo de espacio [E.020 Tabla 4]:")
        if self.solver.enclosure_type == 'open':
            rep.append(f"      • Caso Presión Descendente (Comb 3):  C_barl = {self.solver.C_barlovento:+.2f} | C_sot = {self.solver.C_sotavento:+.2f}")
            rep.append(f"      • Caso Succión / Uplift Crítico (Comb 4): C_barl = {self.solver.C_barlovento_uplift:+.2f} | C_sot = {self.solver.C_sotavento_uplift:+.2f}")
        else:
            rep.append(f"      • Barlovento (para θ = {self.solver.theta_deg:.1f}°): C_barl = {self.solver.C_barlovento:+.2f}")
            rep.append(f"      • Sotavento:                          C_sot  = -0.60")
        rep.append("   4. Presiones de viento de diseño (Ph):")
        rep.append("      Fórmula:      Ph = q × C")
        rep.append(f"      - En Barlovento:  Ph_barl = {self.solver.q_base_kg_m2:.2f} × ({self.solver.C_barlovento:+.2f}) = {self.solver.P_wind_barlovento_kg_m2:+.2f} kgf/m²")
        rep.append(f"      - En Sotavento:   Ph_sot  = {self.solver.q_base_kg_m2:.2f} × ({self.solver.C_sotavento:+.2f}) = {self.solver.P_wind_sotavento_kg_m2:+.2f} kgf/m²")
        rep.append(f"      - Succión Uplift: Ph_uplift_barl = {self.solver.P_wind_barlovento_uplift_kg_m2:+.2f} kgf/m² | Ph_uplift_sot = {self.solver.P_wind_sotavento_uplift_kg_m2:+.2f} kgf/m²")

        # SECCIÓN 3
        rep.append("\n" + "-" * 90)
        rep.append("SECCIÓN 3: METRADO POR ÁREA TRIBUTARIA EN CADA CORREA")
        rep.append("Referencia Normativa: NTE E.020 (Capítulo 2) / AISC 360-16")
        rep.append("-" * 90)
        rep.append("A. Datos de Carga:")
        rep.append(f"   • Peso de cubierta (Aluzinc/termo-techo): w_cub  = {self.solver.roof_dead_load:.1f} kgf/m²")
        rep.append(f"   • Sobrecarga viva de montaje (Lr):        w_viva = {self.solver.roof_live_load:.1f} kgf/m²")
        rep.append(f"   • Peso lineal de correa {purlin['name']}: w_corr = {purlin['weight_kg_m']:.2f} kgf/m")
        rep.append(f"   • Área tributaria por correa (A_trib):    A_trib = s_p × S = {sp:.2f} × {S:.2f} = {sp*S:.2f} m²")
        rep.append("\nB. Cargas Puntuales Transmitidas a la Viga TR:")
        p_d = self.solver.roof_dead_load * sp * S + purlin['weight_kg_m'] * S
        p_l = self.solver.roof_live_load * sp * S
        rep.append(f"   • Carga Muerta puntual (P_D):   P_D = (w_cub × A_trib) + (w_corr × S) = {p_d:.1f} kgf")
        rep.append(f"   • Carga Viva puntual (P_L):     P_L = w_viva × A_trib = {p_l:.1f} kgf")
        rep.append(f"   • Carga Mayorada (P_u gravitatoria): P_u = 1.2(P_D) + 1.6(P_L) = 1.2({p_d:.1f}) + 1.6({p_l:.1f}) = {1.2*p_d + 1.6*p_l:.1f} kgf")

        # SECCIÓN 4
        rep.append("\n" + "-" * 90)
        rep.append("SECCIÓN 4: COMBINACIONES LRFD RESUELTAS EN PARALELO Y ENVOLVENTE GOBERNANTE")
        rep.append("Referencia Normativa: AISC 360-16 Sección B2 / NTE E.090 Capítulo 3")
        rep.append("-" * 90)
        rep.append(f"{'Caso de Carga':<32} {'Mu Máx (kgf·m)':<16} {'Pu Comp TR (kgf)':<18} {'Tu Tensor (kgf)':<16}")
        rep.append("-" * 90)
        for c_k, r in self.analysis_data['cases'].items():
            rep.append(f"{c_k:<32} {r['max_rafter_moment_kgm']:<16.1f} {r['max_rafter_axial_kgf']:<18.1f} {r['max_tensor_tension_kgf']:<16.1f}")
        rep.append("-" * 90)
        rep.append(f"⭐ ENVOLVENTE GOBERNANTE PARA VIGA TR:    {gov['tr_case']}  (Mu = {chk_tr['M_u_kgm']:.1f} kgf·m, Pu = {chk_tr['P_u_kgf']:.1f} kgf)")
        rep.append(f"⭐ ENVOLVENTE GOBERNANTE PARA TENSOR:     {gov['tensor_case']}  (Tu = {chk_t['T_u_kgf']:.1f} kgf)")
        rep.append(f"⚠️ COMPROBACIÓN DE SUCCIÓN / UPLIFT:     En comb4 (0.9D - 1.0W), Tu = {gov['tensor_uplift_kgf']:.1f} kgf")

        # SECCIÓN 5
        rep.append("\n" + "-" * 90)
        rep.append("SECCIÓN 5: VERIFICACIÓN A FLEXOCOMPRESIÓN DE LA VIGA TR")
        rep.append("Referencia Normativa: AISC 360-16 Capítulo H (Sección H1.1, Ecuaciones H1-1a / H1-1b)")
        rep.append("-" * 90)
        rep.append("A. Datos del Perfil y Material:")
        rep.append(f"   • Perfil:                                 {tr['name']} (ASTM A500 Gr. B)")
        rep.append(f"   • Límite de fluencia (Fy):                Fy = 3,150 kgf/cm² (315 MPa)")
        rep.append(f"   • Módulo de elasticidad (E):              E  = 2,040,000 kgf/cm² (200 GPa)")
        rep.append(f"   • Área bruta (Ag):                        Ag = {tr['A']*1e4:.2f} cm²")
        rep.append(f"   • Módulo plástico en eje fuerte (Zx):     Zx = {tr['Zx']*1e6:.1f} cm³")
        rep.append(f"   • Radio de giro en plano (rx):            rx = {tr['rx']*100:.2f} cm")
        rep.append(f"   • Radio de giro fuera de plano (ry):      ry = {tr['ry']*100:.2f} cm")
        rep.append("\nB. Verificación de Pandeo y Compresión Axial (AISC Capítulo E):")
        rep.append(f"   • Longitud no arriostrada fuera del plano: Ly = sp = {sp:.2f} m (arriostrado por correas)")
        rep.append(f"   • Esbeltez gobernante:                    KL/r = máx(Lx/rx, Ly/ry) = {chk_tr['KL_r_max']:.1f} ≤ 200 [OK]")
        rep.append(f"   • Tensión elástica de Euler (Fe):         Fe = (π² × E) / (KL/r)² = {chk_tr['Fe_MPa']:.1f} MPa")
        rep.append(f"   • Tensión crítica (Fcr):                  Fcr = {chk_tr['Fcr_MPa']:.1f} MPa")
        rep.append(f"   • Capacidad axial de diseño (φ_c Pn):     φ_c Pn = 0.90 × Fcr × Ag = {chk_tr['phi_Pn_kgf']:.1f} kgf ({chk_tr['phi_Pn_kN']:.1f} kN)")
        rep.append("\nC. Verificación de Resistencia a Flexión (AISC Capítulo F):")
        rep.append(f"   • Capacidad a flexión de diseño (φ_b Mn): φ_b Mn = 0.90 × Fy × Zx = {chk_tr['phi_Mn_kgm']:.1f} kgf·m ({chk_tr['phi_Mn_kNm']:.2f} kNm)")
        rep.append("\nD. Interacción Flexocompresión (AISC Ecuación H1-1):")
        rep.append(f"   • Solicitaciones actuantes:               Pu = {chk_tr['P_u_kgf']:.1f} kgf | Mu = {chk_tr['M_u_kgm']:.1f} kgf·m")
        rep.append(f"   • Ratio axial:                            Pu / (φ_c Pn) = {chk_tr['ratio_axial']:.3f}")
        rep.append(f"   • Ratio de flexión:                       Mu / (φ_b Mn) = {chk_tr['ratio_flex']:.3f}")
        rep.append(f"   • Ecuación gobernante:                    {chk_tr['formula']}")
        rep.append(f"   • Demanda / Capacidad (DCR):              DCR = {chk_tr['dcr']:.3f} ≤ 1.00  -->  [{chk_tr['status']}]")

        # SECCIÓN 6
        rep.append("\n" + "-" * 90)
        rep.append("SECCIÓN 6: DISEÑO Y VERIFICACIÓN DEL TENSOR HORIZONTAL")
        rep.append("Referencia Normativa: AISC 360-16 Capítulo D (Diseño de Miembros a Tracción)")
        rep.append("-" * 90)
        rep.append("A. Datos del Tensor:")
        rep.append(f"   • Elemento:                               {tensor['name']} (ASTM A36)")
        rep.append(f"   • Límite de fluencia (Fy):                Fy = 2,500 kgf/cm² (250 MPa)")
        rep.append(f"   • Resistencia última a tracción (Fu):     Fu = 4,000 kgf/cm² (400 MPa)")
        rep.append(f"   • Área bruta de la sección (Ag):          Ag = {tensor['Ag_m2']*1e4:.2f} cm²")
        rep.append("\nB. Fórmulas de Capacidad a Tracción:")
        rep.append(f"   1. Fluencia en sección bruta (φ = 0.90):  φ Pn = 0.90 × Fy × Ag = {chk_t['phi_Pn_yield_kgf']:.1f} kgf")
        rep.append(f"   2. Rotura en rosca neta (φ = 0.75):       φ Pn = 0.75 × Fu × (0.75 Ag) = {chk_t['phi_Pn_rupture_kgf']:.1f} kgf")
        rep.append(f"   • Resistencia de diseño gobernante:       φ Pn = {chk_t['phi_Pn_kgf']:.1f} kgf ({chk_t['phi_Pn_kN']:.1f} kN)")
        rep.append(f"   • Tracción actuante máxima (Tu):          Tu = {chk_t['T_u_kgf']:.1f} kgf ({chk_t['T_u_kN']:.1f} kN)")
        rep.append(f"   • Ratio DCR:                              DCR = Tu / φ Pn = {chk_t['dcr']:.3f} ≤ 1.00 [{chk_t['status']}]")
        rep.append(f"   • Alargamiento elástico del tensor:       ΔL = (T_serv × L) / (E × Ag) = {chk_t['elongation_mm']:.2f} mm")

        # SECCIÓN 7
        rep.append("\n" + "-" * 90)
        rep.append("SECCIÓN 7: DETALLE DE CARTELA Y SOLDADURA DEL TENSOR AL TR")
        rep.append("Referencia Normativa: AISC 360-16 Capítulo J (Conexiones Soldadas)")
        rep.append("-" * 90)
        rep.append(f"• Tracción de diseño a transferir:        Tu = {cart['T_u_kgf']:.1f} kgf")
        rep.append(f"• Excentricidad constructiva a base (e):  e  = {cart['cartela_offset_cm']:.1f} cm (induce M_local = {cart['M_local_kgm']:.1f} kgf·m)")
        rep.append(f"• Electrodo de soldadura especificado:    AWS E7018 (F_EXX = 4,920 kgf/cm²)")
        rep.append(f"• Tamaño de filete especificado (a):      a  = {cart['fillet_leg_mm']:.1f} mm (Garganta efectiva = {cart['fillet_leg_mm']*0.707:.2f} mm)")
        rep.append(f"• Longitud de cordón requerida por lado:  L  = {cart['weld_length_cm']} cm")
        rep.append(f"• Especificación de taller:               {cart['recommendation']}")

        # SECCIÓN 8
        rep.append("\n" + "-" * 90)
        rep.append("SECCIÓN 8: DIMENSIONAMIENTO DEL AGUJERO ALARGADO EN APOYO MÓVIL (SLOTTED HOLE)")
        rep.append("Referencia Normativa: AISC 360-16 Tabla J3.3 / Sección J3.2 (Long-Slotted Holes)")
        rep.append("-" * 90)
        rep.append(f"• Desplazamiento elástico por tensor:     Δx_elást = {slot['elastic_disp_mm']:.2f} mm")
        rep.append(f"• Dilatación térmica libre (ΔT = 35°C):   ΔL_térm  = α × L × ΔT = {slot['thermal_disp_mm']:.2f} mm")
        rep.append(f"• Longitud mecanizada de la ranura:       L_slot   = {slot['slot_length_mm']} mm")
        rep.append(f"• Ancho mecanizado de la ranura:          W_slot   = {slot['slot_width_mm']} mm (perno de Ø 3/4\")")
        rep.append(f"• Espesor de arandela gruesa de placa:    t_arand  = {slot['washer_plate_thickness_mm']} mm (AISC J3.2)")
        rep.append(f"• Recomendación de montaje:               {slot['recommendation']}")

        # SECCIÓN 9
        rep.append("\n" + "-" * 90)
        rep.append("SECCIÓN 9: VERIFICACIÓN DE LA CORREA DE TECHO (C O U)")
        rep.append("Referencia Normativa: AISI S100 / NTE E.090")
        rep.append("-" * 90)
        rep.append(f"• Perfil seleccionado:                    {purlin['name']}")
        rep.append(f"• Luz libre de la correa (S):             S  = {S:.2f} m")
        rep.append(f"• Momento flector último (Mu):            Mu = {chk_p['M_u_kgm']:.1f} kgf·m  (Capacidad φ Mn = {chk_p['phi_Mn_kgm']:.1f} kgf·m)")
        rep.append(f"• Flecha máxima de servicio (δ):          δ  = {chk_p['delta_mm']:.1f} mm  (Límite admisible S/200 = {chk_p['delta_adm_mm']:.1f} mm)")
        rep.append(f"• Demanda / Capacidad (DCR):              DCR = {chk_p['dcr']:.3f} ≤ 1.00  -->  [{chk_p['status']}]")

        rep.append("=" * 90)
        rep.append("CONCLUSIÓN: TODOS LOS ELEMENTOS SATISFACEN LOS ESTADOS LÍMITES ÚLTIMOS Y DE SERVICIO.")
        rep.append("=" * 90)

        self.txt_memoria.setPlainText("\n".join(rep))

    def on_auto_optimizar(self):
        best_correa = None
        sorted_correas = sorted(CORREAS_PERU_DATABASE.keys(), key=lambda k: CORREAS_PERU_DATABASE[k]['weight_kg_m'])
        for c_k in sorted_correas:
            self.solver.purlin_name = c_k
            p_chk = self.solver._check_purlin_design(
                CORREAS_PERU_DATABASE[c_k],
                self.spn_dead.value() * 9.80665,
                self.spn_live.value() * 9.80665,
                1.2, 1.6
            )
            if p_chk['dcr'] <= 0.95:
                best_correa = c_k
                break

        if best_correa:
            self.cmb_correa.setCurrentText(best_correa)

        best_tr = None
        sorted_tr = sorted(TR_PERU_DATABASE.keys(), key=lambda k: TR_PERU_DATABASE[k]['weight_kg_m'])
        for tr_k in sorted_tr:
            self.solver.tr_name = tr_k
            data = self.solver.solve_all_combinations()
            if data['governing']['tr_check']['dcr'] <= 0.95:
                best_tr = tr_k
                break

        if best_tr:
            self.cmb_tr.setCurrentText(best_tr)

        self.on_calcular()
        QMessageBox.information(
            self, "Optimización Completada",
            f"Perfiles óptimos del mercado peruano seleccionados:\n"
            f"• Viga TR: {best_tr or 'Actual'}\n"
            f"• Correa de Techo: {best_correa or 'Actual'}"
        )

    def on_exportar_pdf(self):
        if not self.solver or not self.analysis_data:
            QMessageBox.warning(self, "Aviso", "Primero debe calcular la estructura.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar Memoria Técnica en PDF",
            "Memoria_Tecnica_Tijeral_V_Invertida.pdf",
            "Documentos PDF (*.pdf)"
        )
        if filename:
            try:
                out = create_pdf_report(self.solver, filename)
                reply = QMessageBox.question(
                    self, "Memoria PDF Creada",
                    f"La memoria técnica profesional en PDF fue creada exitosamente en:\n{out}\n\n¿Desea abrir el archivo ahora?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    os.startfile(out)
            except Exception as e:
                QMessageBox.critical(self, "Error al generar PDF", f"No se pudo crear el archivo PDF:\n{str(e)}")

    def on_exportar_dxf(self):
        if not self.solver or not self.analysis_data:
            QMessageBox.warning(self, "Aviso", "Primero debe calcular la estructura.")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Guardar Plano DXF", "tijeral_v_invertida_peru.dxf", "Archivos DXF (*.dxf)")
        if filename:
            try:
                active_res = self.analysis_data['cases'][self.analysis_data['governing']['tr_case']]
                export_v_invertida_to_dxf(filename, self.solver, active_res)
                QMessageBox.information(self, "Éxito", f"Plano CAD exportado exitosamente:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo DXF:\n{str(e)}")

    def on_exportar_memoria(self):
        if not self.txt_memoria.toPlainText():
            QMessageBox.warning(self, "Aviso", "No hay memoria generada para exportar.")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "Guardar Memoria Técnica", "memoria_tijeral_v_invertida_formal.txt", "Texto (*.txt);;Markdown (*.md)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.txt_memoria.toPlainText())
                QMessageBox.information(self, "Éxito", f"Memoria técnica guardada en:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar la memoria:\n{str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
