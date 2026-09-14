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

    def __init__(self, state: StateManager, on_canvas_redraw: Callable[[], None], on_load_type_change: Callable[[str], Coroutine[Any, Any, None]]) -> None:
        super().__init__()
        self.state = state
        self.on_canvas_redraw = on_canvas_redraw
        self.on_load_type_change = on_load_type_change
        
        self.expand = 1
        self.bgcolor = ft.Colors.SURFACE_CONTAINER
        self.padding = 15

        self.dimension_content = ft.Column(
            spacing=10,
            controls=[
                ft.Text("Rectangular Beam Dimensions", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
                ft.TextField(label="Width (mm)", value=str(self.state.beam_dimensions.width_mm) if hasattr(self.state.beam_dimensions, 'width_mm') else "100.0", height=40, color=ft.Colors.ON_SURFACE, on_change=self.update_rect_width),
                ft.TextField(label="Height (mm)", value=str(self.state.beam_dimensions.height_mm) if hasattr(self.state.beam_dimensions, 'height_mm') else "100.0", height=40, color=ft.Colors.ON_SURFACE, on_change=self.update_rect_height),
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
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_color=ft.Colors.OUTLINE,
            focused_border_color=ft.Colors.PRIMARY,
            border_radius=8,
            text_style=ft.TextStyle(color=ft.Colors.ON_SURFACE),
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
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_color=ft.Colors.OUTLINE,
            focused_border_color=ft.Colors.PRIMARY,
            border_radius=8,
            text_style=ft.TextStyle(color=ft.Colors.ON_SURFACE),
            on_select=self.change_load_handler,expand=True
        )

        
        
        self.beam_length_input = ft.TextField(
            label="Beam Length (m)",
            value="10.0",
            height=40,
            color=ft.Colors.ON_SURFACE,
            on_change=self.update_beam_length,expand=True
        )

        self.content = ft.Column(
            controls=[
                ft.Text("Beam Controls", color=ft.Colors.ON_SURFACE, size=20, weight=ft.FontWeight.BOLD),
                self.beam_length_input,
                ft.Text("Beam Section", color=ft.Colors.ON_SURFACE_VARIANT, size=12),
                self.beam_type,
                self.dimensions_container,
                ft.Text("Load Setup", color=ft.Colors.ON_SURFACE_VARIANT, size=12),
                self.load_type,
                ft.Text("Active Loads", color=ft.Colors.ON_SURFACE_VARIANT, size=12),
                self.load_list_view,
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        )
        self.refresh_load_list(do_update=False)

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

    def _parse_float(self, control: ft.TextField) -> float:
        val = str(control.value).strip() if control.value else ""
        control.error_text = None
        if not val:
            control.error_text = "Required"
            control.update()
            return 0.0
        try:
            parsed = float(val)
            if parsed <= 0:
                control.error_text = "Must be > 0"
                control.update()
                return 0.0
            control.update()
            return parsed
        except ValueError:
            control.error_text = "Invalid"
            control.update()
            return 0.0

    def update_rect_width(self, e: Any) -> None:
        from frontend.StateManager import RectangularDimensions
        if isinstance(self.state.beam_dimensions, RectangularDimensions):
            val = self._parse_float(e.control)
            if val > 0: self.state.beam_dimensions.width_mm = val
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    def update_rect_height(self, e: Any) -> None:
        from frontend.StateManager import RectangularDimensions
        if isinstance(self.state.beam_dimensions, RectangularDimensions):
            val = self._parse_float(e.control)
            if val > 0: self.state.beam_dimensions.height_mm = val
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    def update_circ_diameter(self, e: Any) -> None:
        from frontend.StateManager import CircularDimensions
        if isinstance(self.state.beam_dimensions, CircularDimensions):
            val = self._parse_float(e.control)
            if val > 0: self.state.beam_dimensions.diameter_mm = val
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    def update_ibeam_height(self, e: Any) -> None:
        from frontend.StateManager import IBeamDimensions
        if isinstance(self.state.beam_dimensions, IBeamDimensions):
            val = self._parse_float(e.control)
            if val > 0: self.state.beam_dimensions.height_mm = val
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    def update_ibeam_flange_width(self, e: Any) -> None:
        from frontend.StateManager import IBeamDimensions
        if isinstance(self.state.beam_dimensions, IBeamDimensions):
            val = self._parse_float(e.control)
            if val > 0: self.state.beam_dimensions.flange_width_mm = val
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    def update_ibeam_flange_thickness(self, e: Any) -> None:
        from frontend.StateManager import IBeamDimensions
        if isinstance(self.state.beam_dimensions, IBeamDimensions):
            val = self._parse_float(e.control)
            if val > 0: self.state.beam_dimensions.flange_thickness_mm = val
        if self.on_canvas_redraw:
            self.on_canvas_redraw()

    def update_ibeam_web_thickness(self, e: Any) -> None:
        from frontend.StateManager import IBeamDimensions
        if isinstance(self.state.beam_dimensions, IBeamDimensions):
            val = self._parse_float(e.control)
            if val > 0: self.state.beam_dimensions.web_thickness_mm = val
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
            if not isinstance(self.state.beam_dimensions, IBeamDimensions):
                self.state.beam_dimensions = IBeamDimensions()
            d = self.state.beam_dimensions
            self.dimension_content.controls.extend(
                [
                    ft.Text("I-Beam Dimensions", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
                    ft.TextField(label="Height (mm)", value=str(d.height_mm), height=40, color=ft.Colors.ON_SURFACE, on_change=self.update_ibeam_height),
                    ft.TextField(label="Flange Width (mm)", value=str(d.flange_width_mm), height=40, color=ft.Colors.ON_SURFACE, on_change=self.update_ibeam_flange_width),
                    ft.TextField(label="Flange Thickness (mm)", value=str(d.flange_thickness_mm), height=40, color=ft.Colors.ON_SURFACE, on_change=self.update_ibeam_flange_thickness),
                    ft.TextField(label="Web Thickness (mm)", value=str(d.web_thickness_mm), height=40, color=ft.Colors.ON_SURFACE, on_change=self.update_ibeam_web_thickness),
                ]
            )
        elif selected_beam == "Rectangular":
            if not isinstance(self.state.beam_dimensions, RectangularDimensions):
                self.state.beam_dimensions = RectangularDimensions()
            d = self.state.beam_dimensions
            self.dimension_content.controls.extend(
                [
                    ft.Text("Rectangular Beam Dimensions", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
                    ft.TextField(label="Width (mm)", value=str(d.width_mm), height=40, color=ft.Colors.ON_SURFACE, on_change=self.update_rect_width),
                    ft.TextField(label="Height (mm)", value=str(d.height_mm), height=40, color=ft.Colors.ON_SURFACE, on_change=self.update_rect_height),
                ]
            )
        elif selected_beam == "Circular":
            if not isinstance(self.state.beam_dimensions, CircularDimensions):
                self.state.beam_dimensions = CircularDimensions()
            d = self.state.beam_dimensions
            self.dimension_content.controls.extend(
                [
                    ft.Text("Circular Beam Dimensions", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
                    ft.TextField(label="Diameter (mm)", value=str(d.diameter_mm), height=40, color=ft.Colors.ON_SURFACE, on_change=self.update_circ_diameter),
                ]
            )
        self.dimensions_container.opacity = 1
        self.dimensions_container.update()
        if self.on_canvas_redraw:
            self.on_canvas_redraw()
    async def update_beam_length(self, e: Any) -> None:
        val: str = str(e.control.value).strip() if e.control.value else ""
        e.control.error_text = None
        if not val:
            e.control.error_text = "Required"
            e.control.update()
            return
            
        try:
            length = float(val)
            if length <= 0:
                e.control.error_text = "Must be > 0"
                e.control.update()
                return
                
            self.state.beam_length = length
            # Update roller support position
            for sup in self.state.supports:
                if sup.support_type == "Roller":
                    sup.position = self.state.beam_length
            if self.on_canvas_redraw:
                self.on_canvas_redraw()
            e.control.update()
        except ValueError:
            e.control.error_text = "Invalid number"
            e.control.update()

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
        from frontend.StateManager import PointLoadState, UDLLoadState, UVLLoadState
        
        self.load_list_view.controls.clear()
        for idx, ld in enumerate(self.state.loads):
            load_type_name: str = str(ld.load_type) if ld.load_type else "Unknown"
            
            if isinstance(ld, PointLoadState):
                details = f"{ld.magnitude_kn}kN @ {ld.position_m}m"
            elif isinstance(ld, UDLLoadState):
                details = f"{ld.intensity_kn_m}kN/m from {ld.start_position_m}m to {ld.end_position_m}m"
            elif isinstance(ld, UVLLoadState):
                details = f"{ld.start_intensity_kn_m} to {ld.end_intensity_kn_m}kN/m from {ld.start_position_m}m to {ld.end_position_m}m"
            else:
                details = "Unknown parameters"

            self.load_list_view.controls.append(
                ft.Container(
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                    padding=8,
                    border_radius=6,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(f"{load_type_name} Load", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
                                    ft.Text(details, size=11, color=ft.Colors.ON_SURFACE_VARIANT),
                                ]
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINED,
                                icon_size=16,
                                icon_color=ft.Colors.ERROR,
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
