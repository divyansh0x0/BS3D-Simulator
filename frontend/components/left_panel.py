import flet as ft
import asyncio
from typing import Callable, Coroutine, Any, Dict
from frontend.StateManager import StateManager

class LeftPanel(ft.Container):
    state: StateManager
    on_canvas_redraw: Callable[[], None]
    on_load_type_change: Callable[[str], Coroutine[Any, Any, None]]
    dimension_content: ft.Column
    dimensions_container: ft.Container
    load_list_view: ft.Column
    beam_type: ft.Dropdown
    load_type: ft.Dropdown
    beam_length_input: ft.TextField
    solve_button: ft.Button

    def __init__(self, state: StateManager, on_canvas_redraw: Callable[[], None], on_load_type_change: Callable[[str], Coroutine[Any, Any, None]]) -> None:
        super().__init__()
        self.state = state
        self.on_canvas_redraw = on_canvas_redraw
        self.on_load_type_change = on_load_type_change
        
        self.width = 260
        self.bgcolor = "#0F172A"
        self.padding = 15

        self.dimension_content = ft.Column(spacing=10)
        self.dimensions_container = ft.Container(
            content=self.dimension_content, opacity=0, animate_opacity=150
        )

        self.load_list_view = ft.Column(spacing=5)

        self.beam_type = ft.Dropdown(
            label="Select Beam Type",
            width=210,
            options=[
                ft.dropdown.Option("Rectangular"),
                ft.dropdown.Option("Circular"),
                ft.dropdown.Option("I-Beam"),
            ],
            bgcolor="#0F172A",
            border_color="#334155",
            focused_border_color="#2563EB",
            border_radius=8,
            text_style=ft.TextStyle(color="#F8FAFC"),
            on_select=self.change_dimensions,
        )

        self.load_type = ft.Dropdown(
            label="Select Load Type",
            width=210,
            options=[
                ft.dropdown.Option("Point"),
                ft.dropdown.Option("UDL"),
                ft.dropdown.Option("UVL"),
            ],
            bgcolor="#0F172A",
            border_color="#334155",
            focused_border_color="#2563EB",
            border_radius=8,
            text_style=ft.TextStyle(color="#F8FAFC"),
            on_select=self.change_load_handler,
        )

        
        
        self.beam_length_input = ft.TextField(
            label="Beam Length (m)",
            value="10.0",
            width=210,
            height=40,
            color="#F8FAFC",
            on_change=self.update_beam_length,
        )

        self.solve_button = ft.Button(
            "Calculate SFD & BMD",
            on_click=self.on_solve_click,
            bgcolor="#22C55E",
            color="#FFFFFF",
            width=210,
            height=45,
        )

        self.content = ft.Column(
            controls=[
                ft.Text("Beam Controls", color="#F8FAFC", size=20, weight=ft.FontWeight.BOLD),
                self.beam_length_input,
                ft.Text("Beam Section", color="#94A3B8", size=12),
                self.beam_type,
                self.dimensions_container,
                ft.Text("Load Setup", color="#94A3B8", size=12),
                self.load_type,
                ft.Text("Active Loads", color="#94A3B8", size=12),
                self.load_list_view,
                self.solve_button,
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        )

    def on_solve_click(self, e: Any) -> None:
        self.state.solve()
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    def update_dimension(self, e: Any) -> None:
        try:
            if e.control.value:
                val = float(e.control.value)
                self.state.dimensions[e.control.label] = val
        except ValueError:
            pass

    async def change_dimensions(self, e: Any) -> None:
        from typing import cast
        from core.Beam import BeamType
        selected_beam = cast(BeamType, e.control.value) if e.control.value else None
        self.state.beam_type = selected_beam
        self.state.dimensions.clear()

        self.dimensions_container.opacity = 0
        self.dimensions_container.update()
        await asyncio.sleep(0.15)
        self.dimension_content.controls.clear()

        if selected_beam == "I-Beam":
            self.dimension_content.controls.extend(
                [
                    ft.Text("I-Beam Dimensions", size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                    ft.TextField(label="Height (mm)", width=210, height=40, color="#F8FAFC", on_change=self.update_dimension),
                    ft.TextField(label="Flange Width (mm)", width=210, height=40, color="#F8FAFC", on_change=self.update_dimension),
                    ft.TextField(label="Flange Thickness (mm)", width=210, height=40, color="#F8FAFC", on_change=self.update_dimension),
                    ft.TextField(label="Web Thickness (mm)", width=210, height=40, color="#F8FAFC", on_change=self.update_dimension),
                ]
            )
        elif selected_beam == "Rectangular":
            self.dimension_content.controls.extend(
                [
                    ft.Text("Rectangular Beam Dimensions", size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                    ft.TextField(label="Width (mm)", width=210, height=40, color="#F8FAFC", on_change=self.update_dimension),
                    ft.TextField(label="Height (mm)", width=210, height=40, color="#F8FAFC", on_change=self.update_dimension),
                ]
            )
        elif selected_beam == "Circular":
            self.dimension_content.controls.extend(
                [
                    ft.Text("Circular Beam Dimensions", size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                    ft.TextField(label="Diameter (mm)", width=210, height=40, color="#F8FAFC", on_change=self.update_dimension),
                ]
            )
        self.dimensions_container.opacity = 1
        self.dimensions_container.update()

    async def update_beam_length(self, e: Any) -> None:
        val: str = str(e.control.value).strip() if e.control.value else ""
        try:
            if val:
                self.state.beam_length = float(val)
                # Update roller support position
                for sup in self.state.supports:
                    if sup.get("type") == "Roller":
                        sup["position"] = self.state.beam_length
                if self.on_canvas_redraw:
                    self.on_canvas_redraw()
        except ValueError:
            pass

    async def change_load_handler(self, e: Any) -> None:
        selected_load: str = str(e.control.value) if e.control.value else ""
        if self.on_load_type_change:
            await self.on_load_type_change(selected_load)

    def remove_load(self, index: int) -> None:
        self.state.loads.pop(index)
        self.refresh_load_list()
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    def refresh_load_list(self) -> None:
        self.load_list_view.controls.clear()
        for idx, ld in enumerate(self.state.loads):
            load_type_name: str = str(ld.get('type', 'Unknown'))
            self.load_list_view.controls.append(
                ft.Container(
                    bgcolor="#1E293B",
                    padding=8,
                    border_radius=6,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(f"{load_type_name}", size=12, color="#F8FAFC"),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINED,
                                icon_size=16,
                                icon_color="#EF4444",
                                on_click=lambda e, i=idx: self.remove_load(i),
                            ),
                        ],
                    ),
                )
            )
        self.load_list_view.update()
