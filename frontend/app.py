import flet as ft
from frontend.components.canvas_view import CanvasView
from frontend.components.left_panel import LeftPanel
from frontend.components.load_panel import LoadPanel
from frontend.StateManager import StateManager


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

    current_val_text = ft.Text(f"{state.cross_section_x:.2f}m", color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD, width=60)

    def on_slider_change(e):
        state.cross_section_x = float(e.control.value)
        beam_canvas.redraw()

    def on_slider_move(e):
        val = float(e.control.value)
        current_val_text.value = f"{val:.2f}m"
        current_val_text.update()
        beam_canvas.update_vertical_line(val)

    cross_section_slider = ft.Slider(
        min=0, max=max(0,state.beam_length),
        value=state.cross_section_x,
        label="{value}m",
        round=2,
        divisions=1000,
        on_change=on_slider_move,
        on_change_end=on_slider_change,
        expand=True,
    )
    
    min_label = ft.Text("0.00m", color=ft.Colors.ON_SURFACE_VARIANT, size=12)
    max_label = ft.Text(f"{max(0.1, state.beam_length):.2f}m", color=ft.Colors.ON_SURFACE_VARIANT, size=12)

    slider_row = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text("Cross Section Position:", color=ft.Colors.PRIMARY ),
                current_val_text,
                min_label,
                cross_section_slider,
                max_label
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        padding=10,
    )

    def refresh_slider():
        cross_section_slider.max = max(0.1, state.beam_length)
        if cross_section_slider.value > state.beam_length:
            cross_section_slider.value = state.beam_length
            state.cross_section_x = state.beam_length
        current_val_text.value = f"{state.cross_section_x:.2f}m"
        max_label.value = f"{max(0.1, state.beam_length):.2f}m"
        try:
            cross_section_slider.update()
            current_val_text.update()
            max_label.update()
        except RuntimeError:
            pass

    def on_state_change() -> None:
        state.solve()
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
                    ft.FloatingActionButton(
                        icon=ft.Icons.PLAY_ARROW,

                        on_click=lambda e: on_state_change(),
                        bgcolor=ft.Colors.TERTIARY,
                        foreground_color=ft.Colors.ON_TERTIARY,
                        top=20,
                        right=20,
                    ),
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


