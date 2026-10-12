import flet as ft
from frontend.StateManager import StateManager
from frontend.components.canvas_view import CanvasView
from frontend.components.cross_section_slider import CrossSectionSlider
from frontend.components.left_panel import LeftPanel
from frontend.components.load_panel import LoadPanel
from frontend.components.right_panel import RightPanel
from frontend.components.y_slider import YSliderPanel


def app(page: ft.Page) -> None:
    page.title = "BS3D - Beam Structural Analysis"
    page.padding = 0
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
    )
    page.theme_mode = ft.ThemeMode.DARK

    # --- APPLICATION STATE ---
    state: StateManager = StateManager()

    # Initialize Components
    beam_canvas: CanvasView = CanvasView(state)
    cross_section_slider: CrossSectionSlider = CrossSectionSlider(
        state=state,
        on_change=beam_canvas.redraw,
    )

    def on_state_change() -> None:
        state.solve()
        beam_canvas.redraw()
        cross_section_slider.refresh()
        right_panel.refresh()
        y_slider_panel.refresh()

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

    y_slider_panel = YSliderPanel(state=state, on_change=on_state_change)

    center_viewport = ft.Column(
        controls=[
            ft.Stack(
                controls=[
                    beam_canvas,
                    load_panel,
                    y_slider_panel,
                    ft.FloatingActionButton(
                        icon=ft.Icons.PLAY_ARROW,
                        on_click=lambda e: on_state_change(),
                        bgcolor=ft.Colors.TERTIARY,
                        foreground_color=ft.Colors.ON_TERTIARY,
                        bottom=20,
                        right=20,
                    ),
                ],
                expand=True,
            ),
            cross_section_slider,
        ],
        expand=3,
        spacing=0,
    )

    right_panel = RightPanel(state=state, on_canvas_redraw=on_state_change)

    page.add(
        ft.Row(
            controls=[
                left_panel,
                center_viewport,
                right_panel,
            ],
            expand=True,
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    )

    # Solve and render the initial default state on load
    on_state_change()
