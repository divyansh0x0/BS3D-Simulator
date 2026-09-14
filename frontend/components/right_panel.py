import flet as ft
from typing import Callable
from frontend.StateManager import StateManager

class RightPanel(ft.Container):
    state: StateManager
    on_canvas_redraw: Callable[[], None]

    def __init__(self, state: StateManager, on_canvas_redraw: Callable[[], None]) -> None:
        super().__init__()
        self.state = state
        self.on_canvas_redraw = on_canvas_redraw

        self.expand = 1
        self.bgcolor = ft.Colors.SURFACE_CONTAINER_LOW
        self.padding = 15

        self.pos_x_val = ft.Text("0.00", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, size=14)
        self.pos_y_val = ft.Text("0.00", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, size=14)
        self.b_val = ft.Text("0.00", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, size=14)
        self.q_val = ft.Text("0.00", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, size=14)
        self.i_val = ft.Text("0.00", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, size=14)
        
        self.sf_val = ft.Text("0.00", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, size=14)
        self.bm_val = ft.Text("0.00", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, size=14)
        self.ss_val = ft.Text("0.00", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, size=14)
        self.bs_val = ft.Text("0.00", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, size=14)

        def make_table_row(label: str, unit: str, val_control: ft.Text) -> ft.Container:
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(label, color=ft.Colors.ON_SURFACE_VARIANT, size=12, expand=2),
                        val_control,
                        ft.Text(unit, color=ft.Colors.ON_SURFACE_VARIANT, size=12, expand=1, text_align=ft.TextAlign.RIGHT),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.Padding.symmetric(vertical=6),
                border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT))
            )

        self.content = ft.Column(
            controls=[
                ft.Text("Cross Section Analysis", color=ft.Colors.ON_SURFACE, size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=5),
                
                ft.Text("Position", color=ft.Colors.PRIMARY, size=14, weight=ft.FontWeight.W_600),
                make_table_row("Cross-Section X", "m", self.pos_x_val),
                make_table_row("Position Y", "mm", self.pos_y_val),
                
                ft.Container(height=10),
                ft.Text("Geometric Properties", color=ft.Colors.PRIMARY, size=14, weight=ft.FontWeight.W_600),
                make_table_row("Breadth (b)", "mm", self.b_val),
                make_table_row("First Moment (Q)", "mm³", self.q_val),
                make_table_row("Second Moment (I)", "mm⁴", self.i_val),

                ft.Container(height=10),
                ft.Text("Force & Moment", color=ft.Colors.PRIMARY, size=14, weight=ft.FontWeight.W_600),
                make_table_row("Shear Force (V)", "kN", self.sf_val),
                make_table_row("Bending Moment (M)", "kN·m", self.bm_val),
                
                ft.Container(height=10),
                ft.Text("Stress Distribution", color=ft.Colors.PRIMARY, size=14, weight=ft.FontWeight.W_600),
                make_table_row("Shear Stress (τ)", "MPa", self.ss_val),
                make_table_row("Bending Stress (σ)", "MPa", self.bs_val),
                ft.Container(height=10),
            ],
            spacing=2,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

    def refresh(self) -> None:
        try:
            sf = self.state.get_shear_force(self.state.cross_section_x)
            bm = self.state.get_bending_moment(self.state.cross_section_x)
            ss = self.state.get_shear_stress(self.state.cross_section_y_meters)
            bs = self.state.get_bending_stress(self.state.cross_section_y_meters)
            
            if self.state._beam is not None:
                b = self.state._beam.get_width(self.state.cross_section_y_meters)
                Q = self.state._beam.get_first_moment_of_area(self.state.cross_section_y_meters)
                I = self.state._beam.get_second_moment_of_area()
            else:
                b = Q = I = 0.0

            def format_scientific_unicode(val: float) -> str:
                if val == 0: return "0.00"
                s = f"{val:.2e}"
                mantissa, exp_str = s.split('e')
                exp_int = int(exp_str)
                if exp_int == 0: return f"{float(mantissa):.2f}"
                if -2 <= exp_int <= 2: return f"{val:.2f}"
                
                superscripts = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', 
                                '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', '-': '⁻'}
                exp_unicode = "".join(superscripts.get(c, c) for c in str(exp_int))
                return f"{mantissa} × 10{exp_unicode}"

            self.pos_x_val.value = f"{self.state.cross_section_x:.2f}"
            self.pos_y_val.value = f"{self.state.cross_section_y_meters * 1000:.2f}"
            
            self.b_val.value = f"{b * 1000:.2f}"
            
            self.q_val.value = format_scientific_unicode(Q * 1e9)
            self.i_val.value = format_scientific_unicode(I * 1e12)

            self.sf_val.value = f"{sf:.2f}"
            self.bm_val.value = f"{bm:.2f}"
            self.ss_val.value = f"{ss:.2f}"
            self.bs_val.value = f"{bs:.2f}"

            self.pos_x_val.update()
            self.pos_y_val.update()
            self.b_val.update()
            self.q_val.update()
            self.i_val.update()
            self.sf_val.update()
            self.bm_val.update()
            self.ss_val.update()
            self.bs_val.update()
        except Exception:
            pass
