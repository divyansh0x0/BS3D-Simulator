import flet as ft
from frontend.components.canvas_view import BeamCanvas
from frontend.components.left_panel import LeftPanel
from frontend.components.load_panel import LoadPanel
from frontend.StateManager import StateManager


def app(page: ft.Page) -> None:
    page.title = "BS3D - Beam Structural Analysis"
    page.padding = 0
    page.bgcolor = "#0B0F19"

    # --- APPLICATION STATE ---
    state: StateManager = StateManager()

    # Initialize Components
    beam_canvas: BeamCanvas = BeamCanvas(state)

    def on_slider_change(e):
        state.cross_section_x = float(e.control.value)
        beam_canvas.redraw()

    cross_section_slider = ft.Slider(
        min=0, max=max(0.1, state.beam_length),
        value=state.cross_section_x,
        label="Cross Section X: {value}m",
        on_change=on_slider_change,
        expand=True,
    )
    
    slider_row = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text("Cross Section Position (m):", color="#F8FAFC"),
                cross_section_slider
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor="#0F172A",
        padding=10,
    )

    def refresh_slider():
        cross_section_slider.max = max(0.1, state.beam_length)
        if cross_section_slider.value > state.beam_length:
            cross_section_slider.value = state.beam_length
            state.cross_section_x = state.beam_length
        try:
            cross_section_slider.update()
        except RuntimeError:
            pass

    def on_state_change() -> None:
        beam_canvas.redraw()
        refresh_slider()

    def on_load_confirmed() -> None:
        left_panel.refresh_load_list()
        on_state_change()

    load_panel: LoadPanel = LoadPanel(state, on_load_confirmed)

    async def on_load_type_change(selected_load: str) -> None:
        await load_panel.change_load(selected_load)

    left_panel: LeftPanel = LeftPanel(
        state=state,
        on_canvas_redraw=on_state_change,
        on_load_type_change=on_load_type_change,
    )

    center_viewport = ft.Column(
        controls=[
            ft.Stack(
                controls=[
                    beam_canvas,
                    load_panel,
                ],
                expand=True,
            ),
            slider_row
        ],
        expand=3,
        spacing=0
    )

    page.add(
        ft.Row(
            controls=[
                left_panel,
                center_viewport,
            ],
            expand=True,
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    )


