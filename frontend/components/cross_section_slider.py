from typing import Any, Callable

import flet as ft

from frontend.StateManager import StateManager


class CrossSectionSlider(ft.Container):
    def __init__(self, state: StateManager, on_change: Callable[[], None]) -> None:
        super().__init__()
        self.state = state
        self.on_change = on_change

        self.current_val_text = ft.Text(
            f"{self.state.cross_section_x:.2f}m",
            color=ft.Colors.PRIMARY,
            weight=ft.FontWeight.BOLD,
            width=60,
        )

        def on_slider_change(e: Any) -> None:
            self.state.cross_section_x = float(e.control.value)
            if self.on_change:
                self.on_change()

        def on_slider_move(e: Any) -> None:
            val = float(e.control.value)
            self.current_val_text.value = f"{val:.2f}m"
            self.current_val_text.update()

        self.slider = ft.Slider(
            min=0,
            max=max(0, self.state.beam_length),
            value=self.state.cross_section_x,
            label="{value}m",
            round=2,
            divisions=1000,
            on_change=on_slider_move,
            on_change_end=on_slider_change,
            expand=True,
        )

        self.min_label = ft.Text("0.00m", color=ft.Colors.ON_SURFACE_VARIANT, size=12)
        self.max_label = ft.Text(
            f"{max(0.1, self.state.beam_length):.2f}m",
            color=ft.Colors.ON_SURFACE_VARIANT,
            size=12,
        )

        self.content = ft.Row(
            controls=[
                ft.Text("Cross Section Position:", color=ft.Colors.PRIMARY),
                self.current_val_text,
                self.min_label,
                self.slider,
                self.max_label,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self.bgcolor = ft.Colors.SURFACE_CONTAINER
        self.padding = 10

    def refresh(self) -> None:
        self.slider.max = max(0.1, self.state.beam_length)
        if self.slider.value > self.state.beam_length:
            self.slider.value = self.state.beam_length
            self.state.cross_section_x = self.state.beam_length
        self.current_val_text.value = f"{self.state.cross_section_x:.2f}m"
        self.max_label.value = f"{max(0.1, self.state.beam_length):.2f}m"
        try:
            self.slider.update()
            self.current_val_text.update()
            self.max_label.update()
        except RuntimeError:
            pass
