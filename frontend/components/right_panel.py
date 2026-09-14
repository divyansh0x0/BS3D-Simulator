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

        def on_slider_change(e: Any) -> None:
            self.state.cross_section_y_meters = float(e.control.value)
            self.val_text.value = f"{self.state.cross_section_y_meters:.2f}m"
            self.val_text.update()
            if self.on_canvas_redraw:
                self.on_canvas_redraw()

        self.cross_section_y_slider = ft.Slider(
            min=-1.0, max=1.0,
            label="{value}",
            value=self.state.cross_section_y_meters,
            round=3,
            on_change=on_slider_change,
            expand=True
        )

        self.val_text = ft.Text(f"{self.state.cross_section_y_meters * 1000:.2f}mm", color=ft.Colors.PRIMARY,
                                weight=ft.FontWeight.BOLD)

        self.content = ft.Column(
            controls=[
                ft.Text("Y-Axis Section", color=ft.Colors.ON_SURFACE, size=20, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            self.val_text,
                            ft.Container(
                                content=ft.RotatedBox(
                                    quarter_turns=-1,
                                    content=self.cross_section_y_slider
                                ),
                                expand=False
                            )
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        expand=True,
                    ),
                    expand=2  # 66% of the column height
                ),
                ft.Container(expand=1)  # Remaining 33%
            ],
            spacing=5,
            expand=True
        )

    def refresh(self) -> None:
        if self.state._beam:
            h = self.state._beam.get_height() / 2
            self.cross_section_y_slider.min = -h
            self.cross_section_y_slider.max = h
            if self.cross_section_y_slider.value > h:
                self.cross_section_y_slider.value = h
                self.state.cross_section_y_meters = h
            if self.cross_section_y_slider.value < -h:
                self.cross_section_y_slider.value = -h
                self.state.cross_section_y_meters = -h
            self.val_text.value = f"{self.state.cross_section_y_meters * 1000:.2f}mm"

        try:
            self.cross_section_y_slider.update()
            self.val_text.update()
        except RuntimeError:
            pass
