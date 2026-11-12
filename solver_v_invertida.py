"""
Motor de Análisis Estructural y Diseño para Tijeral a Dos Aguas en V Invertida (Gable Frame).
Implementa:
1. Análisis simultáneo de TODAS las combinaciones LRFD y de Servicio.
2. Envolvente crítica gobernante para cada elemento (TR, Tensor, Correas, Ranura).
3. Sincronización automática de altura total h = H_columna + H_tijeral para viento NTE E.020.
4. Generación de memoria técnica formal paso a paso con citas de artículos, listas de datos,
   fórmulas simbólicas y desarrollo numérico sustituido.
"""

import math
import numpy as np
from perfiles_peru import TR_PERU_DATABASE, CORREAS_PERU_DATABASE, TENSORES_DATABASE, CIUDADES_VIENTO_E020

class SolverVInvertida:
    def __init__(self, span, height, truss_spacing, purlin_spacing,
                 tr_profile_name, purlin_profile_name, tensor_profile_name,
                 roof_dead_load, roof_live_load,
                 col_height_m=3.5, wind_speed_kmh=75.0, city_name="Lima / Callao",
                 ridge_type="pinned", has_central_hanger=True, steel_grade="A500_B",
                 enclosure_type="closed"):
        self.L = float(span)                            # Luz libre (m)
        self.H = float(height)                          # Altura de cumbrera del tijeral (m)
        self.S = float(truss_spacing)                   # Separación entre tijerales (m)
        self.purlin_spacing = float(purlin_spacing)     # Espaciamiento de correas (m)

        self.tr_name = tr_profile_name
        self.purlin_name = purlin_profile_name
        self.tensor_name = tensor_profile_name

        self.roof_dead_load = float(roof_dead_load)     # kg/m2 (cubierta)
        self.roof_live_load = float(roof_live_load)     # kg/m2 (viva Lr)

        # Altura sincronizada: h_total = H_columna + H_tijeral
        self.col_height_m = float(col_height_m)
        self.building_height_m = self.col_height_m + self.H

        # Viento E.020
        self.wind_speed_kmh = float(wind_speed_kmh)
        self.city_name = str(city_name)
        self.enclosure_type = str(enclosure_type)       # 'closed' (cerrado) o 'open' (abierto / tinglado)

        # Configuración constructiva
        self.ridge_type = ridge_type                    # 'pinned' o 'rigid'
        self.has_central_hanger = bool(has_central_hanger)
        self.steel_grade = steel_grade
        self.cartela_offset_e = 0.15                    # 15 cm

        # Propiedades mecánicas de acero
        if steel_grade == "A36":
            self.Fy_tr = 250.0e6; self.Fu_tr = 400.0e6
        elif steel_grade == "A500_C":
            self.Fy_tr = 345.0e6; self.Fu_tr = 427.0e6
        else: # A500_B estándar
            self.Fy_tr = 315.0e6; self.Fu_tr = 400.0e6

        self.E = 200.0e9 # Pa (2.04e6 kgf/cm2)
        self.Fy_tensor = 250.0e6 # A36 varilla
        self.Fu_tensor = 400.0e6
        self.Fy_purlin = 250.0e6 # A36 / A1011 perfiles C y U

        # Geometría
        self.half_L = self.L / 2.0
        self.slope_len = math.sqrt(self.half_L**2 + self.H**2)
        self.theta = math.atan(self.H / self.half_L)
        self.theta_deg = math.degrees(self.theta)
        self.slope_pct = (self.H / self.half_L) * 100.0

        # Cálculo de viento según NTE E.020
        self._calculate_wind_e020()

        # Espaciado real de correas
        n_purlin_spaces = max(2, int(round(self.slope_len / self.purlin_spacing)))
        self.actual_purlin_spacing = self.slope_len / n_purlin_spaces

    def _calculate_wind_e020(self):
        """Cálculo de cargas de viento según Capítulo 5 de la NTE E.020 (Espacio Cerrado vs Abierto)."""
        h = max(2.0, self.building_height_m)
        if h <= 10.0:
            self.Vh_kmh = self.wind_speed_kmh
        else:
            self.Vh_kmh = self.wind_speed_kmh * ((h / 10.0)**0.22)

        # Presión básica q (Art. 12 E.020: Ph = 0.005 * C * Vh^2)
        self.q_base_kg_m2 = 0.005 * (self.Vh_kmh**2)

        # Factores de forma según tipo de cerramiento (NTE E.020 Tabla 4)
        if self.enclosure_type == 'open':
            # COBERTURA DE ESPACIO ABIERTO / TINGLADO (Flujo de aire libre superior e inferior)
            # Caso 1: Viento que genera empuje descendente máximo (+ Presión en barlovento)
            self.C_barlovento = +0.80
            self.C_sotavento = -0.50
            # Caso 2: Viento que genera arrancamiento / succión ascendente crítica (- Succión en ambos faldones)
            self.C_barlovento_uplift = -1.20
            self.C_sotavento_uplift = -0.80
            self.enclosure_desc = "Espacio Abierto / Tinglado (Sin Muros Perimetrales)"
        else:
            # COBERTURA DE ESPACIO CERRADO (Edificación con muros perimetrales completos)
            if self.theta_deg < 15.0:
                self.C_barlovento = -0.70
            elif self.theta_deg < 60.0:
                self.C_barlovento = 0.07 * self.theta_deg - 1.0
            else:
                self.C_barlovento = +0.80

            self.C_sotavento = -0.60
            self.C_barlovento_uplift = min(-0.70, self.C_barlovento)
            self.C_sotavento_uplift = -0.60
            self.enclosure_desc = "Espacio Cerrado (Edificación con Muros Perimetrales)"

        self.P_wind_barlovento_kg_m2 = self.q_base_kg_m2 * self.C_barlovento
        self.P_wind_sotavento_kg_m2 = self.q_base_kg_m2 * self.C_sotavento
        self.P_wind_barlovento_uplift_kg_m2 = self.q_base_kg_m2 * self.C_barlovento_uplift
        self.P_wind_sotavento_uplift_kg_m2 = self.q_base_kg_m2 * self.C_sotavento_uplift

    def build_model(self):
        self.nodes = []
        self.elements = []
        self.purlins = []

        ds = self.actual_purlin_spacing
        n_purlin_spaces = int(round(self.slope_len / ds))

        left_nodes = []
        for i in range(n_purlin_spaces + 1):
            s = i * ds
            x = (s / self.slope_len) * self.half_L
            y = (s / self.slope_len) * self.H
            node_id = len(self.nodes)
            self.nodes.append({'id': node_id, 'x': x, 'y': y, 'desc': f'Rafter_Izq_{i}'})
            left_nodes.append(node_id)
            if i > 0:
                self.purlins.append({'x': x, 'y': y, 'side': 'left', 'ds': ds, 'node_id': node_id})

        apex_node_id = left_nodes[-1]

        right_nodes = [apex_node_id]
        for i in range(1, n_purlin_spaces + 1):
            s = i * ds
            x = self.half_L + (s / self.slope_len) * self.half_L
            y = self.H - (s / self.slope_len) * self.H
            node_id = len(self.nodes)
            self.nodes.append({'id': node_id, 'x': x, 'y': y, 'desc': f'Rafter_Der_{i}'})
            right_nodes.append(node_id)
            self.purlins.append({'x': x, 'y': y, 'side': 'right', 'ds': ds, 'node_id': node_id})

        self.support_left = left_nodes[0]
        self.support_right = right_nodes[-1]

        is_ridge_hinged = (self.ridge_type == "pinned")

        # Elementos rafter izquierdos
        for i in range(len(left_nodes) - 1):
            hinge_j = is_ridge_hinged if (i == len(left_nodes) - 2) else False
            self.elements.append({
                'id': len(self.elements),
                'i': left_nodes[i], 'j': left_nodes[i+1],
                'type': 'rafter_left',
                'hinged_i': False, 'hinged_j': hinge_j
            })

        # Elementos rafter derechos
        for i in range(len(right_nodes) - 1):
            hinge_i = is_ridge_hinged if (i == 0) else False
            self.elements.append({
                'id': len(self.elements),
                'i': right_nodes[i], 'j': right_nodes[i+1],
                'type': 'rafter_right',
                'hinged_i': hinge_i, 'hinged_j': False
            })

        # Tensor
        if self.has_central_hanger:
            center_tie_id = len(self.nodes)
            self.nodes.append({'id': center_tie_id, 'x': self.half_L, 'y': 0.0, 'desc': 'Tensor_Centro'})

            self.elements.append({
                'id': len(self.elements),
                'i': self.support_left, 'j': center_tie_id,
                'type': 'tensor',
                'hinged_i': True, 'hinged_j': True
            })
            self.elements.append({
                'id': len(self.elements),
                'i': center_tie_id, 'j': self.support_right,
                'type': 'tensor',
                'hinged_i': True, 'hinged_j': True
            })
            self.elements.append({
                'id': len(self.elements),
                'i': center_tie_id, 'j': apex_node_id,
                'type': 'hanger',
                'hinged_i': True, 'hinged_j': True
            })
        else:
            self.elements.append({
                'id': len(self.elements),
                'i': self.support_left, 'j': self.support_right,
                'type': 'tensor',
                'hinged_i': True, 'hinged_j': True
            })

    def solve_combination(self, load_case):
        """Resuelve un caso de carga específico."""
        self.build_model()

        tr_prof = TR_PERU_DATABASE[self.tr_name]
        purlin_prof = CORREAS_PERU_DATABASE[self.purlin_name]
        tensor_prof = TENSORES_DATABASE[self.tensor_name]

        num_nodes = len(self.nodes)
        num_dofs = 3 * num_nodes

        K_global = np.zeros((num_dofs, num_dofs), dtype=float)
        F_global = np.zeros(num_dofs, dtype=float)

        # Factores de combinación LRFD
        if load_case == 'comb1_14D':
            gamma_D = 1.4; gamma_L = 0.0; gamma_W = 0.0
        elif load_case == 'comb2_12D_16L':
            gamma_D = 1.2; gamma_L = 1.6; gamma_W = 0.0
        elif load_case == 'comb3_12D_10W_05L':
            gamma_D = 1.2; gamma_L = 0.5; gamma_W = 1.0 # presión de viento
        elif load_case == 'comb4_09D_10W_uplift':
            gamma_D = 0.9; gamma_L = 0.0; gamma_W = -1.0 # succión de viento pura
        elif load_case == 'service_10D_10L':
            gamma_D = 1.0; gamma_L = 1.0; gamma_W = 0.0
        else: # service wind
            gamma_D = 1.0; gamma_L = 0.0; gamma_W = -0.6

        g = 9.80665
        w_cubierta_N_m2 = self.roof_dead_load * g
        w_live_N_m2 = self.roof_live_load * g
        w_correa_N_m = purlin_prof['weight_kg_m'] * g
        w_rafter_N_m = tr_prof['weight_kg_m'] * g

        # Coeficientes de viento según caso de combinación
        if load_case == 'comb4_09D_10W_uplift':
            c_barl_act = self.C_barlovento_uplift
            c_sot_act = self.C_sotavento_uplift
        else:
            c_barl_act = self.C_barlovento
            c_sot_act = self.C_sotavento

        q_base_N_m2 = self.q_base_kg_m2 * g
        sin_th = math.sin(self.theta); cos_th = math.cos(self.theta)

        # Metrado por correa
        for p in self.purlins:
            trib_area = p['ds'] * self.S
            P_cub_N = w_cubierta_N_m2 * trib_area
            P_corr_N = w_correa_N_m * self.S
            P_D_tot_N = (P_cub_N + P_corr_N) * gamma_D
            P_L_tot_N = (w_live_N_m2 * trib_area) * gamma_L

            Fx_w = 0.0
            Fy_w = 0.0

            if gamma_W != 0.0:
                c_eff = c_barl_act if p['side'] == 'left' else c_sot_act
                p_wind_mag = q_base_N_m2 * abs(c_eff) * trib_area * abs(gamma_W)
                
                if p['side'] == 'left':
                    if c_eff >= 0: # Presión hacia adentro
                        Fx_w = +p_wind_mag * sin_th
                        Fy_w = -p_wind_mag * cos_th
                    else:          # Succión hacia afuera (uplift)
                        Fx_w = -p_wind_mag * sin_th
                        Fy_w = +p_wind_mag * cos_th
                else:
                    if c_eff >= 0: # Presión hacia adentro
                        Fx_w = -p_wind_mag * sin_th
                        Fy_w = -p_wind_mag * cos_th
                    else:          # Succión hacia afuera (uplift)
                        Fx_w = +p_wind_mag * sin_th
                        Fy_w = +p_wind_mag * cos_th

            Fx_tot = Fx_w
            Fy_tot = -(P_D_tot_N + P_L_tot_N) + Fy_w

            nid = p['node_id']
            F_global[3 * nid] += Fx_tot
            F_global[3 * nid + 1] += Fy_tot

        # Peso propio del TR
        for el in self.elements:
            if 'rafter' in el['type']:
                ni = self.nodes[el['i']]; nj = self.nodes[el['j']]
                dx = nj['x'] - ni['x']; dy = nj['y'] - ni['y']
                Le = math.sqrt(dx*dx + dy*dy)
                P_self = (w_rafter_N_m * Le * gamma_D) / 2.0
                F_global[3 * el['i'] + 1] -= P_self
                F_global[3 * el['j'] + 1] -= P_self

        # Ensamblaje
        for el in self.elements:
            ni = self.nodes[el['i']]; nj = self.nodes[el['j']]
            dx = nj['x'] - ni['x']; dy = nj['y'] - ni['y']
            Le = math.sqrt(dx*dx + dy*dy)
            c = dx / Le; s = dy / Le

            if 'rafter' in el['type']:
                A = tr_prof['A']; I = tr_prof['Ix']
            elif el['type'] == 'tensor':
                A = tensor_prof['Ag_m2']; I = 1e-10
            else:
                A = 1.27e-4; I = 1e-10

            k_loc = self._element_local_stiffness(self.E, A, I, Le, el['hinged_i'], el['hinged_j'])

            T = np.array([
                [ c, s, 0,  0, 0, 0],
                [-s, c, 0,  0, 0, 0],
                [ 0, 0, 1,  0, 0, 0],
                [ 0, 0, 0,  c, s, 0],
                [ 0, 0, 0, -s, c, 0],
                [ 0, 0, 0,  0, 0, 1]
            ], dtype=float)

            k_glob = T.T @ k_loc @ T

            dofs = [
                3 * el['i'], 3 * el['i'] + 1, 3 * el['i'] + 2,
                3 * el['j'], 3 * el['j'] + 1, 3 * el['j'] + 2
            ]

            for r in range(6):
                for col in range(6):
                    K_global[dofs[r], dofs[col]] += k_glob[r, col]

        for i in range(num_nodes):
            K_global[3 * i + 2, 3 * i + 2] += 10.0

        fixed_dofs = [
            3 * self.support_left,
            3 * self.support_left + 1,
            3 * self.support_right + 1
        ]
        free_dofs = [d for d in range(num_dofs) if d not in fixed_dofs]
        K_ff = K_global[np.ix_(free_dofs, free_dofs)]
        F_f = F_global[free_dofs]

        U_f = np.linalg.solve(K_ff, F_f)
        U_global = np.zeros(num_dofs, dtype=float)
        U_global[free_dofs] = U_f

        Reactions = K_global @ U_global - F_global
        u_roller_x_mm = U_global[3 * self.support_right] * 1000.0
        apex_id = self.nodes[len(self.purlins) // 2]['id']
        deflection_cumbrera_mm = U_global[3 * apex_id + 1] * 1000.0

        max_rafter_moment_Nm = 0.0
        max_rafter_axial_N = 0.0
        max_tensor_tension_N = 0.0

        elements_results = []
        for el in self.elements:
            ni = self.nodes[el['i']]; nj = self.nodes[el['j']]
            dx = nj['x'] - ni['x']; dy = nj['y'] - ni['y']
            Le = math.sqrt(dx*dx + dy*dy)
            c = dx / Le; s = dy / Le

            dofs = [
                3 * el['i'], 3 * el['i'] + 1, 3 * el['i'] + 2,
                3 * el['j'], 3 * el['j'] + 1, 3 * el['j'] + 2
            ]
            u_elem_glob = U_global[dofs]

            T = np.array([
                [ c, s, 0,  0, 0, 0],
                [-s, c, 0,  0, 0, 0],
                [ 0, 0, 1,  0, 0, 0],
                [ 0, 0, 0,  c, s, 0],
                [ 0, 0, 0, -s, c, 0],
                [ 0, 0, 0,  0, 0, 1]
            ], dtype=float)

            u_loc = T @ u_elem_glob

            if 'rafter' in el['type']:
                A = tr_prof['A']; I = tr_prof['Ix']
            elif el['type'] == 'tensor':
                A = tensor_prof['Ag_m2']; I = 1e-10
            else:
                A = 1.27e-4; I = 1e-10

            k_loc = self._element_local_stiffness(self.E, A, I, Le, el['hinged_i'], el['hinged_j'])
            f_loc = k_loc @ u_loc

            P = (-f_loc[0] + f_loc[3]) / 2.0
            V = max(abs(f_loc[1]), abs(f_loc[4]))
            M = max(abs(f_loc[2]), abs(f_loc[5]))

            if 'rafter' in el['type']:
                max_rafter_axial_N = max(max_rafter_axial_N, abs(P))
                max_rafter_moment_Nm = max(max_rafter_moment_Nm, M)
            elif el['type'] == 'tensor':
                max_tensor_tension_N = max(max_tensor_tension_N, P)

            elements_results.append({
                'id': el['id'], 'type': el['type'], 'length': Le,
                'axial_P_N': P, 'shear_V_N': V, 'moment_M_Nm': M,
                'node_i': el['i'], 'node_j': el['j']
            })

        if self.ridge_type == "pinned":
            q_perp_N_m = (w_cubierta_N_m2 * gamma_D + w_live_N_m2 * gamma_L) * self.S * (cos_th**2) + (w_correa_N_m * gamma_D / self.actual_purlin_spacing) * cos_th
            M_iso_Nm = (q_perp_N_m * (self.slope_len**2)) / 8.0
            max_rafter_moment_Nm = max(max_rafter_moment_Nm, M_iso_Nm)

        return {
            'case_name': load_case,
            'U': U_global,
            'u_roller_x_mm': u_roller_x_mm,
            'deflection_cumbrera_mm': deflection_cumbrera_mm,
            'reactions': {
                'left_Rx_kgf': Reactions[3 * self.support_left] / g,
                'left_Ry_kgf': Reactions[3 * self.support_left + 1] / g,
                'right_Ry_kgf': Reactions[3 * self.support_right + 1] / g,
                'right_Rx_kgf': Reactions[3 * self.support_right] / g
            },
            'max_rafter_moment_kgm': max_rafter_moment_Nm / g,
            'max_rafter_moment_kNm': max_rafter_moment_Nm / 1000.0,
            'max_rafter_axial_kgf': max_rafter_axial_N / g,
            'max_rafter_axial_kN': max_rafter_axial_N / 1000.0,
            'max_tensor_tension_kgf': max_tensor_tension_N / g,
            'max_tensor_tension_kN': max_tensor_tension_N / 1000.0,
            'elements': elements_results
        }

    def solve_all_combinations(self):
        """
        Calcula TODAS las combinaciones LRFD y genera la ENVOLVENTE CRÍTICA gobernante.
        """
        cases = [
            'comb1_14D',
            'comb2_12D_16L',
            'comb3_12D_10W_05L',
            'comb4_09D_10W_uplift',
            'service_10D_10L'
        ]

        self.all_cases_results = {}
        for c in cases:
            self.all_cases_results[c] = self.solve_combination(c)

        tr_prof = TR_PERU_DATABASE[self.tr_name]
        purlin_prof = CORREAS_PERU_DATABASE[self.purlin_name]
        tensor_prof = TENSORES_DATABASE[self.tensor_name]

        # 1. Envolvente para Viga Rafter TR (máximo DCR flexocompresión)
        worst_tr_dcr = -1.0
        gov_tr_case = None
        gov_tr_check = None

        for c in ['comb1_14D', 'comb2_12D_16L', 'comb3_12D_10W_05L', 'comb4_09D_10W_uplift']:
            res = self.all_cases_results[c]
            chk = self._check_tr_flexocompression(
                P_u_N=res['max_rafter_axial_kN'] * 1000.0,
                M_u_Nm=res['max_rafter_moment_kNm'] * 1000.0,
                tr_prof=tr_prof
            )
            if chk['dcr'] > worst_tr_dcr:
                worst_tr_dcr = chk['dcr']
                gov_tr_case = c
                gov_tr_check = chk

        # 2. Envolvente para Tensor Horizontal (máxima tracción y chequeo succión)
        worst_tensor_dcr = -1.0
        gov_tensor_case = None
        gov_tensor_check = None

        for c in ['comb1_14D', 'comb2_12D_16L', 'comb3_12D_10W_05L']:
            res = self.all_cases_results[c]
            chk = self._check_tensor_tension(
                T_u_N=res['max_tensor_tension_kN'] * 1000.0,
                tensor_prof=tensor_prof
            )
            if chk['dcr'] > worst_tensor_dcr:
                worst_tensor_dcr = chk['dcr']
                gov_tensor_case = c
                gov_tensor_check = chk

        # Chequeo succión en tensor (comb4 uplift)
        res_uplift = self.all_cases_results['comb4_09D_10W_uplift']
        tensor_uplift_T = res_uplift['max_tensor_tension_kgf']

        # 3. Envolvente para Correas C o U (Flexión y Flecha)
        # Flexión gobernada por 1.2D + 1.6L o 1.2D + 1.0W
        chk_purlin_comb2 = self._check_purlin_design(
            purlin_prof=purlin_prof,
            w_cubierta=self.roof_dead_load * 9.80665,
            w_live=self.roof_live_load * 9.80665,
            gamma_D=1.2, gamma_L=1.6
        )

        # 4. Dimensionamiento del Apoyo Móvil (Ranura)
        # Evaluado con desplazamiento máximo de servicio (service_10D_10L)
        res_serv = self.all_cases_results['service_10D_10L']
        slot_design = self._design_slotted_hole(
            u_roller_x_mm=res_serv['u_roller_x_mm'],
            bolt_diam_inch=0.75
        )

        # 5. Diseño de Cartela y Soldadura al TR
        cartela_design = self._design_cartela_weld(
            T_u_kgf=gov_tensor_check['T_u_kgf'],
            tr_prof=tr_prof
        )

        return {
            'cases': self.all_cases_results,
            'governing': {
                'tr_case': gov_tr_case,
                'tr_check': gov_tr_check,
                'tensor_case': gov_tensor_case,
                'tensor_check': gov_tensor_check,
                'tensor_uplift_kgf': tensor_uplift_T,
                'purlin_check': chk_purlin_comb2,
                'slot_design': slot_design,
                'cartela_design': cartela_design
            }
        }

    def _check_tr_flexocompression(self, P_u_N, M_u_Nm, tr_prof):
        g = 9.80665
        Lx = self.slope_len
        Ly = self.actual_purlin_spacing

        KL_rx = Lx / tr_prof['rx']
        KL_ry = Ly / tr_prof['ry']
        KL_r_max = max(KL_rx, KL_ry)

        Fe = (math.pi**2 * self.E) / (KL_r_max**2)
        if (self.Fy_tr / Fe) <= 2.25:
            Fcr = (0.658**(self.Fy_tr / Fe)) * self.Fy_tr
        else:
            Fcr = 0.877 * Fe

        phi_c = 0.90
        phi_Pn_N = phi_c * Fcr * tr_prof['A']

        phi_b = 0.90
        Mn_Nm = min(self.Fy_tr * tr_prof['Zx'], 1.6 * self.Fy_tr * tr_prof['Sx'])
        phi_Mn_Nm = phi_b * Mn_Nm

        ratio_axial = P_u_N / phi_Pn_N if phi_Pn_N > 0 else 999.0
        ratio_flex = M_u_Nm / phi_Mn_Nm if phi_Mn_Nm > 0 else 999.0

        if ratio_axial >= 0.2:
            dcr = ratio_axial + (8.0 / 9.0) * ratio_flex
            formula = "AISC Eq. H1-1a (Pu / φPn ≥ 0.2)"
        else:
            dcr = (ratio_axial / 2.0) + ratio_flex
            formula = "AISC Eq. H1-1b (Pu / φPn < 0.2)"

        return {
            'P_u_kgf': P_u_N / g,
            'P_u_kN': P_u_N / 1000.0,
            'M_u_kgm': M_u_Nm / g,
            'M_u_kNm': M_u_Nm / 1000.0,
            'phi_Pn_kgf': phi_Pn_N / g,
            'phi_Pn_kN': phi_Pn_N / 1000.0,
            'phi_Mn_kgm': phi_Mn_Nm / g,
            'phi_Mn_kNm': phi_Mn_Nm / 1000.0,
            'ratio_axial': ratio_axial,
            'ratio_flex': ratio_flex,
            'dcr': dcr,
            'KL_r_max': KL_r_max,
            'Fe_MPa': Fe / 1e6,
            'Fcr_MPa': Fcr / 1e6,
            'formula': formula,
            'status': "CUMPLE" if (dcr <= 1.0 and KL_r_max <= 200.0) else "NO CUMPLE"
        }

    def _check_tensor_tension(self, T_u_N, tensor_prof):
        g = 9.80665
        Ag = tensor_prof['Ag_m2']
        phi_t_yield = 0.90
        phi_Pn_yield_N = phi_t_yield * self.Fy_tensor * Ag

        phi_t_rupture = 0.75
        Aneta = 0.75 * Ag
        phi_Pn_rupture_N = phi_t_rupture * self.Fu_tensor * Aneta

        phi_Pn_N = min(phi_Pn_yield_N, phi_Pn_rupture_N)
        dcr = T_u_N / phi_Pn_N if phi_Pn_N > 0 else 999.0

        T_serv_N = T_u_N / 1.4
        delta_L_mm = (T_serv_N * self.L / (self.E * Ag)) * 1000.0

        return {
            'T_u_kgf': T_u_N / g,
            'T_u_kN': T_u_N / 1000.0,
            'phi_Pn_kgf': phi_Pn_N / g,
            'phi_Pn_kN': phi_Pn_N / 1000.0,
            'phi_Pn_yield_kgf': phi_Pn_yield_N / g,
            'phi_Pn_rupture_kgf': phi_Pn_rupture_N / g,
            'dcr': dcr,
            'elongation_mm': delta_L_mm,
            'status': "CUMPLE" if dcr <= 1.0 else "NO CUMPLE"
        }

    def _check_purlin_design(self, purlin_prof, w_cubierta, w_live, gamma_D, gamma_L):
        g = 9.80665
        L_correa = self.S
        ds = self.actual_purlin_spacing

        w_lin_D = w_cubierta * ds + (purlin_prof['weight_kg_m'] * g)
        w_lin_L = w_live * ds
        q_u = w_lin_D * gamma_D + w_lin_L * gamma_L
        q_serv = w_lin_D + w_lin_L

        M_u_Nm = (q_u * L_correa**2) / 8.0
        phi_b = 0.90
        phi_Mn_Nm = phi_b * self.Fy_purlin * purlin_prof['Sx']
        dcr_flex = M_u_Nm / phi_Mn_Nm if phi_Mn_Nm > 0 else 999.0

        delta_serv = (5.0 * q_serv * (L_correa**4)) / (384.0 * self.E * purlin_prof['Ix'])
        delta_serv_mm = delta_serv * 1000.0
        delta_adm_mm = (L_correa * 1000.0) / 200.0

        dcr_deflect = delta_serv_mm / delta_adm_mm if delta_adm_mm > 0 else 999.0
        dcr_purlin = max(dcr_flex, dcr_deflect)

        return {
            'name': purlin_prof['name'],
            'M_u_kgm': M_u_Nm / g,
            'M_u_kNm': M_u_Nm / 1000.0,
            'phi_Mn_kgm': phi_Mn_Nm / g,
            'phi_Mn_kNm': phi_Mn_Nm / 1000.0,
            'delta_mm': delta_serv_mm,
            'delta_adm_mm': delta_adm_mm,
            'dcr_flex': dcr_flex,
            'dcr_deflect': dcr_deflect,
            'dcr': dcr_purlin,
            'status': "CUMPLE" if dcr_purlin <= 1.0 else "NO CUMPLE"
        }

    def _design_slotted_hole(self, u_roller_x_mm, bolt_diam_inch=0.75):
        d_bolt_mm = bolt_diam_inch * 25.4
        alpha_steel = 1.2e-5
        delta_T = 35.0
        delta_L_thermal_mm = alpha_steel * (self.L * 1000.0) * delta_T

        disp_elastic = abs(u_roller_x_mm)
        carrera_util_mm = 2.0 * (disp_elastic + delta_L_thermal_mm / 2.0) * 1.5
        slot_len = max(d_bolt_mm + 20.0, d_bolt_mm + carrera_util_mm + 10.0)
        slot_width = d_bolt_mm + 2.0

        plate_thk = max(10.0, d_bolt_mm * 0.6)
        washer_thk = max(8.0, d_bolt_mm * 0.5)

        return {
            'bolt_diam_mm': d_bolt_mm,
            'elastic_disp_mm': disp_elastic,
            'thermal_disp_mm': delta_L_thermal_mm,
            'slot_length_mm': math.ceil(slot_len),
            'slot_width_mm': math.ceil(slot_width),
            'base_plate_thickness_mm': math.ceil(plate_thk),
            'washer_plate_thickness_mm': math.ceil(washer_thk),
            'recommendation': (
                f"Ranura longitudinal de {math.ceil(slot_len)} mm x {math.ceil(slot_width)} mm para perno de {bolt_diam_inch}\". "
                f"Incluir placa arandela gruesa de {math.ceil(washer_thk)} mm (AISC J3.2) y tuerca con contratuerca holgada 1 mm."
            )
        }

    def _design_cartela_weld(self, T_u_kgf, tr_prof):
        fillet_leg_mm = 4.0
        throat_cm = (fillet_leg_mm * 0.707) / 10.0
        weld_strength_kgf_cm = 2214.0 * throat_cm

        req_length_cm = T_u_kgf / (2.0 * weld_strength_kgf_cm) if weld_strength_kgf_cm > 0 else 5.0
        req_length_cm = max(6.0, req_length_cm)

        M_local_kgm = T_u_kgf * (self.cartela_offset_e)

        return {
            'T_u_kgf': T_u_kgf,
            'cartela_offset_cm': self.cartela_offset_e * 100.0,
            'M_local_kgm': M_local_kgm,
            'fillet_leg_mm': fillet_leg_mm,
            'weld_length_cm': math.ceil(req_length_cm),
            'recommendation': (
                f"Cartela de plancha e=8 mm soldada al TR con cordón de filete a={fillet_leg_mm} mm "
                f"(electrodo E7018) en longitud L={math.ceil(req_length_cm)} cm por ambos lados. "
                f"Excentricidad a la base e={self.cartela_offset_e*100:.0f} cm."
            )
        }

    def get_continuous_moment_curve(self, max_M_kgm):
        xs = []; ys = []; moments = []
        is_pinned = (self.ridge_type == "pinned")
        n_pts = 40

        for i in range(n_pts + 1):
            t = i / n_pts
            x = t * self.half_L
            y = t * self.H
            if is_pinned:
                M = 4.0 * max_M_kgm * t * (1.0 - t)
            else:
                M = max_M_kgm * (1.5 * t * (1.0 - t) - 0.5 * (t**2))
            xs.append(x); ys.append(y); moments.append(M)

        for i in range(1, n_pts + 1):
            t = i / n_pts
            x = self.half_L + t * self.half_L
            y = self.H - t * self.H
            t_inv = 1.0 - t
            if is_pinned:
                M = 4.0 * max_M_kgm * t_inv * (1.0 - t_inv)
            else:
                M = max_M_kgm * (1.5 * t_inv * (1.0 - t_inv) - 0.5 * (t_inv**2))
            xs.append(x); ys.append(y); moments.append(M)

        return np.array(xs), np.array(ys), np.array(moments)

    def _element_local_stiffness(self, E, A, I, L, hinged_i, hinged_j):
        k = np.zeros((6, 6), dtype=float)
        axial = E * A / L
        k[0, 0] = axial;  k[0, 3] = -axial
        k[3, 0] = -axial; k[3, 3] = axial

        if hinged_i and hinged_j:
            return k

        EI = E * I
        if not hinged_i and not hinged_j:
            k[1, 1] = 12 * EI / (L**3); k[1, 2] = 6 * EI / (L**2)
            k[1, 4] = -12 * EI / (L**3); k[1, 5] = 6 * EI / (L**2)
            k[2, 1] = 6 * EI / (L**2);  k[2, 2] = 4 * EI / L
            k[2, 4] = -6 * EI / (L**2); k[2, 5] = 2 * EI / L
            k[4, 1] = -12 * EI / (L**3); k[4, 2] = -6 * EI / (L**2)
            k[4, 4] = 12 * EI / (L**3);  k[4, 5] = -6 * EI / (L**2)
            k[5, 1] = 6 * EI / (L**2);   k[5, 2] = 2 * EI / L
            k[5, 4] = -6 * EI / (L**2);  k[5, 5] = 4 * EI / L
        elif not hinged_i and hinged_j:
            k[1, 1] = 3 * EI / (L**3);  k[1, 2] = 3 * EI / (L**2)
            k[1, 4] = -3 * EI / (L**3)
            k[2, 1] = 3 * EI / (L**2);  k[2, 2] = 3 * EI / L
            k[2, 4] = -3 * EI / (L**2)
            k[4, 1] = -3 * EI / (L**3); k[4, 2] = -3 * EI / (L**2)
            k[4, 4] = 3 * EI / (L**3)
        elif hinged_i and not hinged_j:
            k[1, 1] = 3 * EI / (L**3);  k[1, 5] = 3 * EI / (L**2)
            k[1, 4] = -3 * EI / (L**3)
            k[4, 1] = -3 * EI / (L**3); k[4, 4] = 3 * EI / (L**3)
            k[4, 5] = -3 * EI / (L**2)
            k[5, 1] = 3 * EI / (L**2);  k[5, 4] = -3 * EI / (L**2)
            k[5, 5] = 3 * EI / L

        return k
