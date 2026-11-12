"""
Base de datos de perfiles comerciales del mercado peruano (Tupemesa, Aceros Arequipa, Siderperu)
y mapa eólico de velocidades de viento de la norma técnica peruana NTE E.020.
"""

# ----------------------------------------------------------------------
# 1. MAPA EÓLICO DE CIUDADES DEL PERÚ (NTE E.020 - ANEXO 2 / CAPÍTULO 5)
# Velocidades básicas de viento a 10 m de altura en km/h
# ----------------------------------------------------------------------
CIUDADES_VIENTO_E020 = {
    "Lima / Callao": 75.0,
    "Ica": 100.0,
    "Pisco / Paracas": 110.0,
    "Nazca / Palpa": 85.0,
    "Piura": 85.0,
    "Talara / Paita": 90.0,
    "Chiclayo / Lambayeque": 80.0,
    "Trujillo / La Libertad": 80.0,
    "Chimbote / Casma": 80.0,
    "Arequipa": 80.0,
    "Camaná / Mollendo": 80.0,
    "Tacna": 75.0,
    "Moquegua / Ilo": 75.0,
    "Cusco": 75.0,
    "Huancayo / Junín": 75.0,
    "Puno / Juliaca": 85.0,
    "Ayacucho": 75.0,
    "Cajamarca": 75.0,
    "Huaraz / Callejón de Huaylas": 75.0,
    "Iquitos / Loreto": 75.0,
    "Pucallpa / Ucayali": 75.0,
    "Tarapoto / San Martín": 75.0,
    "Personalizado": 75.0
}

# ----------------------------------------------------------------------
# 2. TUBOS RECTANGULARES (TR) - MERCADO PERUANO (Tupemesa / Aceros Arequipa)
# Propiedades: dimensiones en mm/m, áreas en m2, inercias en m4, módulos en m3.
# ----------------------------------------------------------------------
TR_PERU_DATABASE = {
    "TR 50x25x2.0": {
        "name": "TR 50x25x2.0 (2\"x1\")", "H_mm": 50, "B_mm": 25, "t_mm": 2.0,
        "A": 2.70e-4, "Ix": 8.78e-8, "Iy": 2.92e-8, "Sx": 3.51e-6, "Sy": 2.34e-6,
        "Zx": 4.56e-6, "Zy": 2.85e-6, "rx": 0.0180, "ry": 0.0104, "weight_kg_m": 2.12
    },
    "TR 75x38x2.0": {
        "name": "TR 75x38x2.0 (3\"x1 1/2\")", "H_mm": 75, "B_mm": 38, "t_mm": 2.0,
        "A": 4.22e-4, "Ix": 3.12e-7, "Iy": 1.05e-7, "Sx": 8.32e-6, "Sy": 5.53e-6,
        "Zx": 1.08e-5, "Zy": 6.80e-6, "rx": 0.0272, "ry": 0.0158, "weight_kg_m": 3.31
    },
    "TR 75x38x2.5": {
        "name": "TR 75x38x2.5 (3\"x1 1/2\")", "H_mm": 75, "B_mm": 38, "t_mm": 2.5,
        "A": 5.17e-4, "Ix": 3.73e-7, "Iy": 1.25e-7, "Sx": 9.95e-6, "Sy": 6.58e-6,
        "Zx": 1.31e-5, "Zy": 8.20e-6, "rx": 0.0269, "ry": 0.0156, "weight_kg_m": 4.06
    },
    "TR 75x38x3.0": {
        "name": "TR 75x38x3.0 (3\"x1 1/2\")", "H_mm": 75, "B_mm": 38, "t_mm": 3.0,
        "A": 6.07e-4, "Ix": 4.27e-7, "Iy": 1.43e-7, "Sx": 1.14e-5, "Sy": 7.53e-6,
        "Zx": 1.52e-5, "Zy": 9.50e-6, "rx": 0.0265, "ry": 0.0153, "weight_kg_m": 4.77
    },
    "TR 100x50x2.0": {
        "name": "TR 100x50x2.0 (4\"x2\")", "H_mm": 100, "B_mm": 50, "t_mm": 2.0,
        "A": 5.72e-4, "Ix": 7.78e-7, "Iy": 2.65e-7, "Sx": 1.56e-5, "Sy": 1.06e-5,
        "Zx": 1.98e-5, "Zy": 1.28e-5, "rx": 0.0369, "ry": 0.0215, "weight_kg_m": 4.49
    },
    "TR 100x50x2.5": {
        "name": "TR 100x50x2.5 (4\"x2\")", "H_mm": 100, "B_mm": 50, "t_mm": 2.5,
        "A": 7.04e-4, "Ix": 9.42e-7, "Iy": 3.19e-7, "Sx": 1.88e-5, "Sy": 1.28e-5,
        "Zx": 2.42e-5, "Zy": 1.56e-5, "rx": 0.0366, "ry": 0.0213, "weight_kg_m": 5.53
    },
    "TR 100x50x3.0": {
        "name": "TR 100x50x3.0 (4\"x2\")", "H_mm": 100, "B_mm": 50, "t_mm": 3.0,
        "A": 8.32e-4, "Ix": 1.09e-6, "Iy": 3.68e-7, "Sx": 2.18e-5, "Sy": 1.47e-5,
        "Zx": 2.83e-5, "Zy": 1.82e-5, "rx": 0.0362, "ry": 0.0210, "weight_kg_m": 6.53
    },
    "TR 100x50x4.0": {
        "name": "TR 100x50x4.0 (4\"x2\")", "H_mm": 100, "B_mm": 50, "t_mm": 4.0,
        "A": 1.07e-3, "Ix": 1.35e-6, "Iy": 4.51e-7, "Sx": 2.70e-5, "Sy": 1.80e-5,
        "Zx": 3.58e-5, "Zy": 2.28e-5, "rx": 0.0355, "ry": 0.0205, "weight_kg_m": 8.41
    },
    "TR 120x60x2.5": {
        "name": "TR 120x60x2.5", "H_mm": 120, "B_mm": 60, "t_mm": 2.5,
        "A": 8.54e-4, "Ix": 1.62e-6, "Iy": 5.46e-7, "Sx": 2.70e-5, "Sy": 1.82e-5,
        "Zx": 3.44e-5, "Zy": 2.20e-5, "rx": 0.0435, "ry": 0.0253, "weight_kg_m": 6.70
    },
    "TR 120x60x3.0": {
        "name": "TR 120x60x3.0", "H_mm": 120, "B_mm": 60, "t_mm": 3.0,
        "A": 1.01e-3, "Ix": 1.88e-6, "Iy": 6.32e-7, "Sx": 3.13e-5, "Sy": 2.11e-5,
        "Zx": 4.04e-5, "Zy": 2.58e-5, "rx": 0.0431, "ry": 0.0250, "weight_kg_m": 7.94
    },
    "TR 120x60x4.0": {
        "name": "TR 120x60x4.0", "H_mm": 120, "B_mm": 60, "t_mm": 4.0,
        "A": 1.31e-3, "Ix": 2.36e-6, "Iy": 7.85e-7, "Sx": 3.93e-5, "Sy": 2.62e-5,
        "Zx": 5.16e-5, "Zy": 3.28e-5, "rx": 0.0424, "ry": 0.0245, "weight_kg_m": 10.30
    },
    "TR 150x50x2.5": {
        "name": "TR 150x50x2.5 (6\"x2\")", "H_mm": 150, "B_mm": 50, "t_mm": 2.5,
        "A": 9.54e-4, "Ix": 2.65e-6, "Iy": 4.22e-7, "Sx": 3.53e-5, "Sy": 1.69e-5,
        "Zx": 4.62e-5, "Zy": 2.14e-5, "rx": 0.0527, "ry": 0.0210, "weight_kg_m": 7.49
    },
    "TR 150x50x3.0": {
        "name": "TR 150x50x3.0 (6\"x2\")", "H_mm": 150, "B_mm": 50, "t_mm": 3.0,
        "A": 1.13e-3, "Ix": 3.09e-6, "Iy": 4.88e-7, "Sx": 4.12e-5, "Sy": 1.95e-5,
        "Zx": 5.43e-5, "Zy": 2.51e-5, "rx": 0.0523, "ry": 0.0208, "weight_kg_m": 8.89
    },
    "TR 150x50x4.0": {
        "name": "TR 150x50x4.0 (6\"x2\")", "H_mm": 150, "B_mm": 50, "t_mm": 4.0,
        "A": 1.47e-3, "Ix": 3.90e-6, "Iy": 6.03e-7, "Sx": 5.20e-5, "Sy": 2.41e-5,
        "Zx": 6.96e-5, "Zy": 3.18e-5, "rx": 0.0515, "ry": 0.0202, "weight_kg_m": 11.55
    },
    "TR 150x100x3.0": {
        "name": "TR 150x100x3.0 (6\"x4\")", "H_mm": 150, "B_mm": 100, "t_mm": 3.0,
        "A": 1.43e-3, "Ix": 4.54e-6, "Iy": 2.43e-6, "Sx": 6.05e-5, "Sy": 4.86e-5,
        "Zx": 7.55e-5, "Zy": 5.82e-5, "rx": 0.0563, "ry": 0.0412, "weight_kg_m": 11.25
    },
    "TR 150x100x4.0": {
        "name": "TR 150x100x4.0 (6\"x4\")", "H_mm": 150, "B_mm": 100, "t_mm": 4.0,
        "A": 1.87e-3, "Ix": 5.80e-6, "Iy": 3.08e-6, "Sx": 7.73e-5, "Sy": 6.16e-5,
        "Zx": 9.77e-5, "Zy": 7.50e-5, "rx": 0.0557, "ry": 0.0406, "weight_kg_m": 14.70
    },
    "TR 150x100x4.5": {
        "name": "TR 150x100x4.5 (6\"x4\")", "H_mm": 150, "B_mm": 100, "t_mm": 4.5,
        "A": 2.09e-3, "Ix": 6.38e-6, "Iy": 3.38e-6, "Sx": 8.51e-5, "Sy": 6.76e-5,
        "Zx": 1.08e-4, "Zy": 8.30e-5, "rx": 0.0553, "ry": 0.0402, "weight_kg_m": 16.39
    },
    "TR 200x100x3.0": {
        "name": "TR 200x100x3.0 (8\"x4\")", "H_mm": 200, "B_mm": 100, "t_mm": 3.0,
        "A": 1.73e-3, "Ix": 9.48e-6, "Iy": 3.32e-6, "Sx": 9.48e-5, "Sy": 6.64e-5,
        "Zx": 1.18e-4, "Zy": 7.82e-5, "rx": 0.0740, "ry": 0.0438, "weight_kg_m": 13.60
    },
    "TR 200x100x4.0": {
        "name": "TR 200x100x4.0 (8\"x4\")", "H_mm": 200, "B_mm": 100, "t_mm": 4.0,
        "A": 2.27e-3, "Ix": 1.22e-5, "Iy": 4.24e-6, "Sx": 1.22e-4, "Sy": 8.48e-5,
        "Zx": 1.54e-4, "Zy": 1.01e-4, "rx": 0.0733, "ry": 0.0432, "weight_kg_m": 17.84
    },
    "TR 200x100x4.5": {
        "name": "TR 200x100x4.5 (8\"x4\")", "H_mm": 200, "B_mm": 100, "t_mm": 4.5,
        "A": 2.54e-3, "Ix": 1.35e-5, "Iy": 4.67e-6, "Sx": 1.35e-4, "Sy": 9.34e-5,
        "Zx": 1.71e-4, "Zy": 1.12e-4, "rx": 0.0729, "ry": 0.0429, "weight_kg_m": 19.92
    },
    "TR 250x100x4.5": {
        "name": "TR 250x100x4.5 (10\"x4\")", "H_mm": 250, "B_mm": 100, "t_mm": 4.5,
        "A": 2.99e-3, "Ix": 2.41e-5, "Iy": 5.95e-6, "Sx": 1.93e-4, "Sy": 1.19e-4,
        "Zx": 2.51e-4, "Zy": 1.45e-4, "rx": 0.0898, "ry": 0.0446, "weight_kg_m": 23.45
    }
}

# ----------------------------------------------------------------------
# 3. CORREAS C Y U DE 2.5 mm Y 3.0 mm (MERCADO PERUANO)
# ----------------------------------------------------------------------
CORREAS_PERU_DATABASE = {
    # Perfiles C con labio atiesador (costaneras)
    "C 100x50x15x2.5": {
        "name": "Canal C 100x50x15x2.5 mm", "type": "C", "H_mm": 100, "B_mm": 50, "t_mm": 2.5,
        "A": 5.01e-4, "Ix": 6.48e-7, "Iy": 1.72e-7, "Sx": 1.30e-5, "Sy": 5.25e-6,
        "Zx": 1.58e-5, "Zy": 8.20e-6, "rx": 0.0360, "ry": 0.0185, "weight_kg_m": 3.93
    },
    "C 100x50x15x3.0": {
        "name": "Canal C 100x50x15x3.0 mm", "type": "C", "H_mm": 100, "B_mm": 50, "t_mm": 3.0,
        "A": 5.88e-4, "Ix": 7.56e-7, "Iy": 1.99e-7, "Sx": 1.51e-5, "Sy": 6.10e-6,
        "Zx": 1.86e-5, "Zy": 9.60e-6, "rx": 0.0358, "ry": 0.0184, "weight_kg_m": 4.62
    },
    "C 125x50x15x2.5": {
        "name": "Canal C 125x50x15x2.5 mm", "type": "C", "H_mm": 125, "B_mm": 50, "t_mm": 2.5,
        "A": 5.63e-4, "Ix": 1.08e-6, "Iy": 1.86e-7, "Sx": 1.72e-5, "Sy": 5.35e-6,
        "Zx": 2.12e-5, "Zy": 8.40e-6, "rx": 0.0438, "ry": 0.0182, "weight_kg_m": 4.42
    },
    "C 125x50x15x3.0": {
        "name": "Canal C 125x50x15x3.0 mm", "type": "C", "H_mm": 125, "B_mm": 50, "t_mm": 3.0,
        "A": 6.63e-4, "Ix": 1.26e-6, "Iy": 2.16e-7, "Sx": 2.02e-5, "Sy": 6.22e-6,
        "Zx": 2.51e-5, "Zy": 9.90e-6, "rx": 0.0436, "ry": 0.0180, "weight_kg_m": 5.21
    },
    "C 150x50x17x2.5": {
        "name": "Canal C 150x50x17x2.5 mm", "type": "C", "H_mm": 150, "B_mm": 50, "t_mm": 2.5,
        "A": 6.38e-4, "Ix": 1.69e-6, "Iy": 2.09e-7, "Sx": 2.26e-5, "Sy": 5.58e-6,
        "Zx": 2.81e-5, "Zy": 8.90e-6, "rx": 0.0515, "ry": 0.0181, "weight_kg_m": 5.01
    },
    "C 150x50x17x3.0": {
        "name": "Canal C 150x50x17x3.0 mm", "type": "C", "H_mm": 150, "B_mm": 50, "t_mm": 3.0,
        "A": 7.54e-4, "Ix": 1.99e-6, "Iy": 2.43e-7, "Sx": 2.66e-5, "Sy": 6.51e-6,
        "Zx": 3.34e-5, "Zy": 1.05e-5, "rx": 0.0514, "ry": 0.0179, "weight_kg_m": 5.92
    },
    "C 200x50x17x2.5": {
        "name": "Canal C 200x50x17x2.5 mm", "type": "C", "H_mm": 200, "B_mm": 50, "t_mm": 2.5,
        "A": 7.64e-4, "Ix": 3.42e-6, "Iy": 2.34e-7, "Sx": 3.42e-5, "Sy": 5.75e-6,
        "Zx": 4.35e-5, "Zy": 9.40e-6, "rx": 0.0669, "ry": 0.0175, "weight_kg_m": 6.00
    },
    "C 200x50x17x3.0": {
        "name": "Canal C 200x50x17x3.0 mm", "type": "C", "H_mm": 200, "B_mm": 50, "t_mm": 3.0,
        "A": 9.04e-4, "Ix": 4.05e-6, "Iy": 2.73e-7, "Sx": 4.05e-5, "Sy": 6.72e-6,
        "Zx": 5.18e-5, "Zy": 1.11e-5, "rx": 0.0668, "ry": 0.0174, "weight_kg_m": 7.10
    },

    # Perfiles U (canales simples sin labio)
    "U 100x50x2.5": {
        "name": "Canal U 100x50x2.5 mm", "type": "U", "H_mm": 100, "B_mm": 50, "t_mm": 2.5,
        "A": 4.69e-4, "Ix": 5.82e-7, "Iy": 1.21e-7, "Sx": 1.16e-5, "Sy": 3.65e-6,
        "Zx": 1.42e-5, "Zy": 6.80e-6, "rx": 0.0352, "ry": 0.0161, "weight_kg_m": 3.68
    },
    "U 100x50x3.0": {
        "name": "Canal U 100x50x3.0 mm", "type": "U", "H_mm": 100, "B_mm": 50, "t_mm": 3.0,
        "A": 5.53e-4, "Ix": 6.78e-7, "Iy": 1.39e-7, "Sx": 1.36e-5, "Sy": 4.22e-6,
        "Zx": 1.68e-5, "Zy": 8.00e-6, "rx": 0.0350, "ry": 0.0159, "weight_kg_m": 4.34
    },
    "U 125x50x2.5": {
        "name": "Canal U 125x50x2.5 mm", "type": "U", "H_mm": 125, "B_mm": 50, "t_mm": 2.5,
        "A": 5.31e-4, "Ix": 9.65e-7, "Iy": 1.31e-7, "Sx": 1.54e-5, "Sy": 3.75e-6,
        "Zx": 1.91e-5, "Zy": 7.00e-6, "rx": 0.0426, "ry": 0.0157, "weight_kg_m": 4.17
    },
    "U 125x50x3.0": {
        "name": "Canal U 125x50x3.0 mm", "type": "U", "H_mm": 125, "B_mm": 50, "t_mm": 3.0,
        "A": 6.28e-4, "Ix": 1.13e-6, "Iy": 1.51e-7, "Sx": 1.81e-5, "Sy": 4.35e-6,
        "Zx": 2.27e-5, "Zy": 8.30e-6, "rx": 0.0424, "ry": 0.0155, "weight_kg_m": 4.93
    },
    "U 150x50x2.5": {
        "name": "Canal U 150x50x2.5 mm", "type": "U", "H_mm": 150, "B_mm": 50, "t_mm": 2.5,
        "A": 5.94e-4, "Ix": 1.52e-6, "Iy": 1.38e-7, "Sx": 2.02e-5, "Sy": 3.82e-6,
        "Zx": 2.54e-5, "Zy": 7.20e-6, "rx": 0.0506, "ry": 0.0153, "weight_kg_m": 4.66
    },
    "U 150x50x3.0": {
        "name": "Canal U 150x50x3.0 mm", "type": "U", "H_mm": 150, "B_mm": 50, "t_mm": 3.0,
        "A": 7.03e-4, "Ix": 1.79e-6, "Iy": 1.60e-7, "Sx": 2.38e-5, "Sy": 4.45e-6,
        "Zx": 3.02e-5, "Zy": 8.50e-6, "rx": 0.0504, "ry": 0.0151, "weight_kg_m": 5.52
    },
    "U 200x50x2.5": {
        "name": "Canal U 200x50x2.5 mm", "type": "U", "H_mm": 200, "B_mm": 50, "t_mm": 2.5,
        "A": 7.19e-4, "Ix": 3.06e-6, "Iy": 1.51e-7, "Sx": 3.06e-5, "Sy": 3.92e-6,
        "Zx": 3.96e-5, "Zy": 7.50e-6, "rx": 0.0653, "ry": 0.0145, "weight_kg_m": 5.64
    },
    "U 200x50x3.0": {
        "name": "Canal U 200x50x3.0 mm", "type": "U", "H_mm": 200, "B_mm": 50, "t_mm": 3.0,
        "A": 8.53e-4, "Ix": 3.63e-6, "Iy": 1.75e-7, "Sx": 3.63e-5, "Sy": 4.58e-6,
        "Zx": 4.73e-5, "Zy": 8.90e-6, "rx": 0.0651, "ry": 0.0143, "weight_kg_m": 6.70
    }
}

# ----------------------------------------------------------------------
# 4. TENSORES DE ACERO REDONDO LISO (ASTM A36) CON EXTREMOS ROSCADOS
# ----------------------------------------------------------------------
TENSORES_DATABASE = {
    "Redondo 1/2\" (12.7 mm)": {"name": "Varilla Lisa Ø 1/2\" (12.7 mm)", "d_mm": 12.7, "Ag_m2": 1.27e-4, "weight_kg_m": 0.99},
    "Redondo 5/8\" (15.9 mm)": {"name": "Varilla Lisa Ø 5/8\" (15.9 mm)", "d_mm": 15.9, "Ag_m2": 1.98e-4, "weight_kg_m": 1.55},
    "Redondo 3/4\" (19.1 mm)": {"name": "Varilla Lisa Ø 3/4\" (19.1 mm)", "d_mm": 19.1, "Ag_m2": 2.85e-4, "weight_kg_m": 2.24},
    "Redondo 7/8\" (22.2 mm)": {"name": "Varilla Lisa Ø 7/8\" (22.2 mm)", "d_mm": 22.2, "Ag_m2": 3.88e-4, "weight_kg_m": 3.04},
    "Redondo 1\" (25.4 mm)": {"name": "Varilla Lisa Ø 1\" (25.4 mm)", "d_mm": 25.4, "Ag_m2": 5.07e-4, "weight_kg_m": 3.98},
    "Redondo 1 1/8\" (28.6 mm)": {"name": "Varilla Lisa Ø 1 1/8\" (28.6 mm)", "d_mm": 28.6, "Ag_m2": 6.41e-4, "weight_kg_m": 5.03},
    "Redondo 1 1/4\" (31.8 mm)": {"name": "Varilla Lisa Ø 1 1/4\" (31.8 mm)", "d_mm": 31.8, "Ag_m2": 7.92e-4, "weight_kg_m": 6.21},
    "Cable Acero 3/8\" (9.5 mm)": {"name": "Cable de Acero Ø 3/8\" EIPS", "d_mm": 9.5, "Ag_m2": 7.10e-5, "weight_kg_m": 0.36},
    "Cable Acero 1/2\" (12.7 mm)": {"name": "Cable de Acero Ø 1/2\" EIPS", "d_mm": 12.7, "Ag_m2": 1.27e-4, "weight_kg_m": 0.65}
}
