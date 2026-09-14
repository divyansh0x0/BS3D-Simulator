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
    material_type: ft.Dropdown
    load_type: ft.Dropdown
    beam_length_input: ft.TextField
    solve_button: ft.Button

    def __init__(self, state: StateManager, on_canvas_redraw: Callable[[], None], on_load_type_change: Callable[[str], Coroutine[Any, Any, None]]) -> None:
        super().__init__()
        self.state = state
        self.on_canvas_redraw = on_canvas_redraw
        self.on_load_type_change = on_load_type_change
        
        self.expand = 1
        self.bgcolor = "#0F172A"
        self.padding = 15

        self.dimension_content = ft.Column(
            spacing=10,
            controls=[
                ft.Text("Rectangular Beam Dimensions", size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                ft.TextField(label="Width (mm)", value="100.0", height=40, color="#F8FAFC", on_change=self.update_rect_width),
                ft.TextField(label="Height (mm)", value="100.0", height=40, color="#F8FAFC", on_change=self.update_rect_height),
            ]
        )
        self.dimensions_container = ft.Container(
            content=self.dimension_content, opacity=1, animate_opacity=150,
            expand=True
        )

        self.load_list_view = ft.Column(spacing=5)

        self.beam_type = ft.Dropdown(
            label="Select Beam Type",
            value="Rectangular",
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
            expand=True
        )

        self.load_type = ft.Dropdown(
            label="Select Load Type",
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
            on_select=self.change_load_handler,expand=True
        )

        
        
        self.beam_length_input = ft.TextField(
            label="Beam Length (m)",
            value="10.0",
            height=40,
            color="#F8FAFC",
            on_change=self.update_beam_length,expand=True
        )

        self.solve_button = ft.Button(
            "Calculate SFD & BMD",
            on_click=self.on_solve_click,
            bgcolor="#22C55E",
            color="#FFFFFF",
            height=45,expand=True
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
        self.refresh_load_list(do_update=False)
    def on_solve_click(self, e: Any) -> None:
        self.state.solve()
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    async def change_material(self, e: Any) -> None:
        from frontend.StateManager import MaterialType
        selected = e.control.value if e.control.value else None
        if selected == "Steel":
            self.state.material_type = MaterialType.STEEL
        elif selected == "Aluminum":
            self.state.material_type = MaterialType.ALUMINUM
        elif selected == "Concrete":
            self.state.material_type = MaterialType.CONCRETE
        elif selected == "Wood":
            self.state.material_type = MaterialType.WOOD

    def _parse_float(self, val: str) -> float:
        try: return float(val)
        except ValueError: return 0.0

    def update_rect_width(self, e: Any) -> None:
        from frontend.StateManager import RectangularDimensions
        if isinstance(self.state.beam_dimensions, RectangularDimensions):
            self.state.beam_dimensions.width_mm = self._parse_float(e.control.value)
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    def update_rect_height(self, e: Any) -> None:
        from frontend.StateManager import RectangularDimensions
        if isinstance(self.state.beam_dimensions, RectangularDimensions):
            self.state.beam_dimensions.height_mm = self._parse_float(e.control.value)
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    def update_circ_diameter(self, e: Any) -> None:
        from frontend.StateManager import CircularDimensions
        if isinstance(self.state.beam_dimensions, CircularDimensions):
            self.state.beam_dimensions.diameter_mm = self._parse_float(e.control.value)
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    def update_ibeam_height(self, e: Any) -> None:
        from frontend.StateManager import IBeamDimensions
        if isinstance(self.state.beam_dimensions, IBeamDimensions):
            self.state.beam_dimensions.height_mm = self._parse_float(e.control.value)
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    def update_ibeam_flange_width(self, e: Any) -> None:
        from frontend.StateManager import IBeamDimensions
        if isinstance(self.state.beam_dimensions, IBeamDimensions):
            self.state.beam_dimensions.flange_width_mm = self._parse_float(e.control.value)
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    def update_ibeam_flange_thickness(self, e: Any) -> None:
        from frontend.StateManager import IBeamDimensions
        if isinstance(self.state.beam_dimensions, IBeamDimensions):
            self.state.beam_dimensions.flange_thickness_mm = self._parse_float(e.control.value)
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    def update_ibeam_web_thickness(self, e: Any) -> None:
        from frontend.StateManager import IBeamDimensions
        if isinstance(self.state.beam_dimensions, IBeamDimensions):
            self.state.beam_dimensions.web_thickness_mm = self._parse_float(e.control.value)
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    async def change_dimensions(self, e: Any) -> None:
        from typing import cast
        from core.Beam import BeamType
        from frontend.StateManager import RectangularDimensions, CircularDimensions, IBeamDimensions
        selected_beam = cast(BeamType, e.control.value) if e.control.value else None
        self.state.beam_type = selected_beam

        self.dimensions_container.opacity = 0
        self.dimensions_container.update()
        self.dimension_content.controls.clear()

        if selected_beam == "I-Beam":
            self.state.beam_dimensions = IBeamDimensions()
            self.dimension_content.controls.extend(
                [
                    ft.Text("I-Beam Dimensions", size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                    ft.TextField(label="Height (mm)", height=40, color="#F8FAFC", on_change=self.update_ibeam_height),
                    ft.TextField(label="Flange Width (mm)", height=40, color="#F8FAFC", on_change=self.update_ibeam_flange_width),
                    ft.TextField(label="Flange Thickness (mm)", height=40, color="#F8FAFC", on_change=self.update_ibeam_flange_thickness),
                    ft.TextField(label="Web Thickness (mm)", height=40, color="#F8FAFC", on_change=self.update_ibeam_web_thickness),
                ]
            )
        elif selected_beam == "Rectangular":
            self.state.beam_dimensions = RectangularDimensions()
            self.dimension_content.controls.extend(
                [
                    ft.Text("Rectangular Beam Dimensions", size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                    ft.TextField(label="Width (mm)", height=40, color="#F8FAFC", on_change=self.update_rect_width),
                    ft.TextField(label="Height (mm)", height=40, color="#F8FAFC", on_change=self.update_rect_height),
                ]
            )
        elif selected_beam == "Circular":
            self.state.beam_dimensions = CircularDimensions()
            self.dimension_content.controls.extend(
                [
                    ft.Text("Circular Beam Dimensions", size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                    ft.TextField(label="Diameter (mm)", height=40, color="#F8FAFC", on_change=self.update_circ_diameter),
                ]
            )
        self.dimensions_container.opacity = 1
        self.dimensions_container.update()
        if self.on_canvas_redraw:
            self.on_canvas_redraw()
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
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    async def change_load_handler(self, e: Any) -> None:
        selected_load: str = str(e.control.value) if e.control.value else ""
        if self.on_load_type_change:
            await self.on_load_type_change(selected_load)

    def remove_load(self, index: int) -> None:
        self.state.loads.pop(index)
        self.refresh_load_list()
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    def refresh_load_list(self, do_update: bool = True) -> None:
        self.load_list_view.controls.clear()
        for idx, ld in enumerate(self.state.loads):
            load_type_name: str = str(getattr(ld, 'load_type', 'Unknown'))
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
        if do_update:
            self.load_list_view.update()
        if self.on_canvas_redraw and do_update:
            self.on_canvas_redraw()
