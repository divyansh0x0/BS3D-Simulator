import flet as ft
import flet.canvas as cv
from frontend.StateManager import StateManager

class BeamCanvas(ft.Container):
    state: StateManager
    canvas_shape_group: cv.Canvas

    def __init__(self, state: StateManager) -> None:
        super().__init__()
        self.state = state
        self.expand = True
        self.padding = 20
        self.canvas_shape_group = cv.Canvas(
            shapes=[],
            expand=True,
        )
        self.content = self.canvas_shape_group

    def redraw(self) -> None:
        self.canvas_shape_group.shapes.clear()
        beam_paint = ft.Paint(stroke_width=6, color="#ffffff")
        # --- DRAW BEAM USING START_X ---

        self.canvas_shape_group.update()
