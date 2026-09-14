from numbers import Number

import flet as ft
import flet.canvas as cv
from flet.controls import border_radius

from frontend.StateManager import StateManager


class BeamCanvas(ft.Container):
    state: StateManager
    canvas_shape_group: cv.Canvas

    def __init__(self, state: StateManager) -> None:
        super().__init__()
        self.state: StateManager = state
        self.expand: bool = True
        self.canvas_shape_group = cv.Canvas(
            shapes=[],
            expand=True,
        )
        self.spacing = 20
        self.content = self.canvas_shape_group
        self.section_width_fraction = 0.5
        self.section_height_fraction = 0.3
        self.on_size_change = self.update_realtime_size

        self.realtime_width = 0
        self.realtime_height = 0
        self.expand = True

    def update_realtime_size(self, e: ft.LayoutSizeChangeEvent) -> None:
        self.realtime_width = float(e.width)
        self.realtime_height = float(e.height)
        print(self.realtime_width, self.realtime_height)
        self.redraw()

    def redraw(self) -> None:
        self.canvas_shape_group.shapes.clear()
        box_paint = ft.Paint(stroke_width=2, color="#aaa", style=ft.PaintingStyle.STROKE)

        # draw BEAM, SFD, BMD separator
        def draw_section_borders():
            xb1 = 0
            wb1 = self.realtime_width * self.section_width_fraction
            yb1 = 0
            hb1 = self.realtime_height * self.section_height_fraction
            xb2 = xb1 + wb1
            yb2 = yb1 + hb1
            for i in range(1, 3):
                self.canvas_shape_group.shapes.append(cv.Line(
                    x1=xb1,
                    y1=yb2 * i,
                    x2=xb2,
                    y2=yb2 * i,
                    paint=box_paint,
                ))
            # draw separator between left and right section
            self.canvas_shape_group.shapes.append(cv.Line(
                x1=xb2,
                y1=yb1,
                x2=xb2,
                y2=self.realtime_height,
                paint=box_paint,
            ))
            # draw separator for bending stress and shear stress
            self.canvas_shape_group.shapes.append(cv.Line(
                x1=xb2,
                y1=self.realtime_height * 0.5,
                x2=self.realtime_width,
                y2=self.realtime_height * 0.5,
                paint=box_paint,
            ))

        draw_section_borders()
        self.canvas_shape_group.update()
