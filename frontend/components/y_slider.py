import flet as ft
from frontend.StateManager import StateManager
from typing import Callable, Any


class YSliderPanel(ft.Container):
    def __init__(self, state: StateManager, on_change: Callable[[], None]):
        super().__init__()
        self.state = state
        self.on_change = on_change

        self.right = 10
        self.top = 0
        self.bottom = 0
        self.alignment = ft.Alignment.CENTER

        def on_slider_change(e: Any) -> None:
            self.state.cross_section_y_meters = float(e.control.value)
            if self.on_change:
                self.on_change()

        self.slider = ft.Slider(
            min=-1.0, max=1.0,
            value=self.state.cross_section_y_meters,
            round=3,
            on_change=on_slider_change,
            expand=True
        )
        self.content = ft.Column(
            controls=[
                # add slider right beside the top right section of canvas containing drawing of cross section of beam
                ft.Container(
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                    border_radius=8,
                    padding=1,
                    border=ft.Border.all(1, ft.Colors.OUTLINE),
                    content=ft.RotatedBox(quarter_turns=-1, content=self.slider),
                    alignment=ft.Alignment.CENTER,
                    expand=1  # Middle 50% slider box
                ),
                ft.Container(expand=1),  # Top 25% spacer

                ft.Container(expand=1),  # Bottom 25% spacer
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            expand=True
        )

    def refresh(self):
        if self.state._beam:
            h = self.state._beam.get_height() / 2
            if h == 0: h = 0.1
            self.slider.min = -h
            self.slider.max = h
            if self.slider.value > h:
                self.slider.value = h
                self.state.cross_section_y_meters = h
            if self.slider.value < -h:
                self.slider.value = -h
                self.state.cross_section_y_meters = -h
        try:
            self.slider.update()
        except RuntimeError:
            pass
