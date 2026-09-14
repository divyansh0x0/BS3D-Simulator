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
        self.bgcolor = "#0F172A"
        self.padding = 15

        def on_slider_change(e: Any) -> None:
            self.state.cross_section_x = float(e.control.value)
            if self.on_canvas_redraw:
                self.on_canvas_redraw()

        self.cross_section_slider = ft.Slider(
            min=0, max=max(0.1, self.state.beam_length),
            value=self.state.cross_section_x,
            label="Cross Section X: {value}m",
            on_change=on_slider_change,
        )

        self.content = ft.Column(
            controls=[
                ft.Text("Analysis Tools", color="#F8FAFC", size=20, weight=ft.FontWeight.BOLD),
                ft.Text("Cross Section Position (m)", color="#94A3B8", size=12),
                self.cross_section_slider
            ],
            spacing=12,
        )

    def refresh(self) -> None:
        self.cross_section_slider.max = max(0.1, self.state.beam_length)
        if self.cross_section_slider.value > self.state.beam_length:
            self.cross_section_slider.value = self.state.beam_length
            self.state.cross_section_x = self.state.beam_length
        try:
            self.cross_section_slider.update()
        except RuntimeError:
            pass
