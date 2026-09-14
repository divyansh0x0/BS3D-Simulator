import flet as ft
import asyncio
from typing import Callable, Optional, Any, Dict
from frontend.StateManager import StateManager

class LoadPanel(ft.Container):
    state: StateManager
    on_load_confirmed: Callable[[], None]
    load_content: ft.Column
    current_load_type: Optional[str]

    def __init__(self, state: StateManager, on_load_confirmed: Callable[[], None]) -> None:
        super().__init__()
        self.state = state
        self.on_load_confirmed = on_load_confirmed
        
        self.load_content = ft.Column(spacing=10)
        self.content = self.load_content
        self.border = ft.Border.all(1, ft.Colors.OUTLINE)
        self.border_radius = 10
        self.padding = 12
        self.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
        self.opacity = 0
        self.animate_opacity = 150
        self.bottom = 100
        self.left = 20
        self.current_load_type = None

    async def change_load(self, selected_load: str) -> None:
        self.current_load_type = selected_load
        self.opacity = 0
        self.update()
        await asyncio.sleep(0.15)
        self.load_content.controls.clear()

        if selected_load == "Point":
            self.load_content.controls.extend(
                [
                    ft.Text("Point Load Parameters", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
                    ft.TextField(label="Load Magnitude (kN)", height=40, color=ft.Colors.ON_SURFACE, keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="Load Position (m)", height=40, color=ft.Colors.ON_SURFACE, keyboard_type=ft.KeyboardType.NUMBER),
                ]
            )
        elif selected_load == "UDL":
            self.load_content.controls.extend(
                [
                    ft.Text("UDL Parameters", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
                    ft.TextField(label="Load Intensity (kN/m)", height=40, color=ft.Colors.ON_SURFACE, keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="Start Position (m)", height=40, color=ft.Colors.ON_SURFACE, keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="End Position (m)", height=40, color=ft.Colors.ON_SURFACE, keyboard_type=ft.KeyboardType.NUMBER),
                ]
            )
        elif selected_load == "UVL":
            self.load_content.controls.extend(
                [
                    ft.Text("UVL Parameters", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE),
                    ft.TextField(label="Start Intensity (kN/m)", height=40, color=ft.Colors.ON_SURFACE, keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="End Intensity (kN/m)", height=40, color=ft.Colors.ON_SURFACE, keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="Start Position (m)", height=40, color=ft.Colors.ON_SURFACE, keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="End Position (m)", height=40, color=ft.Colors.ON_SURFACE, keyboard_type=ft.KeyboardType.NUMBER),
                ]
            )

        if selected_load:
            self.load_content.controls.append(
                ft.Button(
                    "Confirm Load",
                    on_click=self.confirm_load,
                    bgcolor=ft.Colors.PRIMARY,
                    color=ft.Colors.ON_PRIMARY,
                )
            )

        self.opacity = 1
        self.update()

    async def confirm_load(self, e: Any) -> None:
        from frontend.StateManager import PointLoadState, UDLLoadState, UVLLoadState
        
        has_error = False

        def parse_val(control: ft.TextField) -> float:
            nonlocal has_error
            control.error_text = None
            if not control.value:
                control.error_text = "Required"
                has_error = True
                return 0.0
            try:
                return float(control.value)
            except ValueError:
                control.error_text = "Invalid number"
                has_error = True
                return 0.0

        def validate_pos(control: ft.TextField, pos: float) -> bool:
            nonlocal has_error
            if control.error_text is not None:
                return False
            if pos < 0 or pos > self.state.beam_length:
                control.error_text = f"Range: 0 - {self.state.beam_length}"
                has_error = True
                return False
            return True

        load_obj = None

        if self.current_load_type == "Point":
            mag = pos = 0.0
            pos_ctrl = None
            for control in self.load_content.controls:
                if isinstance(control, ft.TextField):
                    val = parse_val(control)
                    if "Magnitude" in control.label: mag = val
                    elif "Position" in control.label: 
                        pos = val
                        pos_ctrl = control
            if pos_ctrl: validate_pos(pos_ctrl, pos)
            
            if not has_error:
                load_obj = PointLoadState(magnitude_kn=mag, position_m=pos)

        elif self.current_load_type == "UDL":
            intensity = start_pos = end_pos = 0.0
            start_ctrl = end_ctrl = None
            for control in self.load_content.controls:
                if isinstance(control, ft.TextField):
                    val = parse_val(control)
                    if "Intensity" in control.label: intensity = val
                    elif "Start Position" in control.label: 
                        start_pos = val
                        start_ctrl = control
                    elif "End Position" in control.label: 
                        end_pos = val
                        end_ctrl = control
            
            s_ok = validate_pos(start_ctrl, start_pos) if start_ctrl else False
            e_ok = validate_pos(end_ctrl, end_pos) if end_ctrl else False
            
            if s_ok and e_ok and start_pos >= end_pos:
                end_ctrl.error_text = "Must be > Start"
                has_error = True

            if not has_error:
                load_obj = UDLLoadState(intensity_kn_m=intensity, start_position_m=start_pos, end_position_m=end_pos)

        elif self.current_load_type == "UVL":
            start_int = end_int = start_pos = end_pos = 0.0
            start_ctrl = end_ctrl = None
            for control in self.load_content.controls:
                if isinstance(control, ft.TextField):
                    val = parse_val(control)
                    if "Start Intensity" in control.label: start_int = val
                    elif "End Intensity" in control.label: end_int = val
                    elif "Start Position" in control.label: 
                        start_pos = val
                        start_ctrl = control
                    elif "End Position" in control.label: 
                        end_pos = val
                        end_ctrl = control
                        
            s_ok = validate_pos(start_ctrl, start_pos) if start_ctrl else False
            e_ok = validate_pos(end_ctrl, end_pos) if end_ctrl else False
            
            if s_ok and e_ok and start_pos >= end_pos:
                end_ctrl.error_text = "Must be > Start"
                has_error = True

            if not has_error:
                load_obj = UVLLoadState(start_intensity_kn_m=start_int, end_intensity_kn_m=end_int, start_position_m=start_pos, end_position_m=end_pos)
        else:
            has_error = True

        if has_error:
            self.update()
            return

        if load_obj:
            self.state.loads.append(load_obj)
        
        if self.on_load_confirmed:
            self.on_load_confirmed()

        # Visual feedback flash
        self.border = ft.Border.all(2, ft.Colors.TERTIARY)
        self.update()
        await asyncio.sleep(0.15)

        self.opacity = 0
        self.border = ft.Border.all(1, ft.Colors.OUTLINE)
        self.update()
