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

    def on_load_confirmed() -> None:
        left_panel.refresh_load_list()
        beam_canvas.redraw()

    load_panel: LoadPanel = LoadPanel(state, on_load_confirmed)

    async def on_load_type_change(selected_load: str) -> None:
        await load_panel.change_load(selected_load)

    left_panel: LeftPanel = LeftPanel(
        state=state,
        on_canvas_redraw=beam_canvas.redraw,
        on_load_type_change=on_load_type_change,
    )

    center_viewport: ft.Stack = ft.Stack(
        controls=[
            beam_canvas,
            load_panel,
        ],
        expand=3,
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

    beam_canvas.redraw()


