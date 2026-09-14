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
        self.border = ft.Border.all(1, "#334155")
        self.border_radius = 10
        self.padding = 12
        self.width = 230
        self.bgcolor = "#1E293B"
        self.opacity = 0
        self.animate_opacity = 150
        self.top = 20
        self.right = 20
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
                    ft.Text("Point Load Parameters", size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                    ft.TextField(label="Load Magnitude (kN)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="Load Position (m)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                ]
            )
        elif selected_load == "UDL":
            self.load_content.controls.extend(
                [
                    ft.Text("UDL Parameters", size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                    ft.TextField(label="Load Intensity (kN/m)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="Start Position (m)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="End Position (m)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                ]
            )
        elif selected_load == "UVL":
            self.load_content.controls.extend(
                [
                    ft.Text("UVL Parameters", size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                    ft.TextField(label="Start Intensity (kN/m)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="End Intensity (kN/m)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="Start Position (m)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="End Position (m)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                ]
            )

        if selected_load:
            self.load_content.controls.append(
                ft.ElevatedButton(
                    "Confirm Load",
                    on_click=self.confirm_load,
                    bgcolor="#2563EB",
                    color="#FFFFFF",
                    width=200,
                )
            )

        self.opacity = 1
        self.update()

    async def confirm_load(self, e: Any) -> None:
        load_data: Dict[str, Any] = {"type": self.current_load_type}
        for control in self.load_content.controls:
            if isinstance(control, ft.TextField):
                val: str = control.value.strip() if control.value else ""
                label: str = control.label if control.label else "Unknown"
                try:
                    load_data[label] = float(val) if val else 0.0
                except ValueError:
                    load_data[label] = 0.0

        self.state.loads.append(load_data)
        
        if self.on_load_confirmed:
            self.on_load_confirmed()

        # Visual feedback flash
        self.border = ft.Border.all(2, "#22C55E")
        self.update()
        await asyncio.sleep(0.15)

        self.opacity = 0
        self.border = ft.Border.all(1, "#334155")
        self.update()
