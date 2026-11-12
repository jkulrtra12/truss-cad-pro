from solver_v_invertida import SolverVInvertida
from generar_pdf_tijeral import create_pdf_report

def main():
    s = SolverVInvertida(
        span=12.0,
        height=2.5,
        truss_spacing=4.0,
        purlin_spacing=1.0,
        tr_profile_name="TR 150x100x4.0",
        purlin_profile_name="C 125x50x15x2.5",
        tensor_profile_name='Redondo 5/8" (15.9 mm)',
        roof_dead_load=12.0,
        roof_live_load=30.0,
        col_height_m=3.5,
        wind_speed_kmh=75.0,
        city_name="Lima / Callao",
        ridge_type="pinned",
        has_central_hanger=True,
        steel_grade="A500_B"
    )
    
    pdf_path = create_pdf_report(s, "Memoria_Tecnica_Tijeral_V_Invertida.pdf")
    print(f"PDF formal generado exitosamente: {pdf_path}")

if __name__ == '__main__':
    main()
