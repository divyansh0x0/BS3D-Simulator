import flet as ft
from typing import Callable, Any
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

        self.sf_val = ft.Text("0.00", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, size=16)
        self.bm_val = ft.Text("0.00", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, size=16)
        self.ss_val = ft.Text("0.00", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, size=16)
        self.bs_val = ft.Text("0.00", color=ft.Colors.ON_SURFACE, weight=ft.FontWeight.BOLD, size=16)

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
                padding=ft.Padding.symmetric(vertical=8),
                border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT))
            )

        self.content = ft.Column(
            controls=[
                ft.Text("Cross Section Analysis", color=ft.Colors.ON_SURFACE, size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                ft.Text("Force & Moment", color=ft.Colors.PRIMARY, size=14, weight=ft.FontWeight.W_600),
                make_table_row("Shear Force", "kN", self.sf_val),
                make_table_row("Bending Moment", "kN·m", self.bm_val),
                ft.Container(height=15),
                ft.Text("Stress Distribution", color=ft.Colors.PRIMARY, size=14, weight=ft.FontWeight.W_600),
                make_table_row("Shear Stress", "MPa", self.ss_val),
                make_table_row("Bending Stress", "MPa", self.bs_val),
            ],
            spacing=5,
            expand=True,
        )

    def refresh(self) -> None:
        try:
            sf = self.state.get_shear_force(self.state.cross_section_x)
            bm = self.state.get_bending_moment(self.state.cross_section_x)
            ss = self.state.get_shear_stress(self.state.cross_section_y_meters)
            bs = self.state.get_bending_stress(self.state.cross_section_y_meters)

            self.sf_val.value = f"{sf:.2f}"
            self.bm_val.value = f"{bm:.2f}"
            self.ss_val.value = f"{ss:.2f}"
            self.bs_val.value = f"{bs:.2f}"

            self.sf_val.update()
            self.bm_val.update()
            self.ss_val.update()
            self.bs_val.update()
        except Exception:
            pass
