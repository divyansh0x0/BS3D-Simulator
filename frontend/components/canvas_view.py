from numbers import Number
from turtledemo.chaos import h

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
        self.section_height_fraction = 1 / 3
        self.right_section_height_fraction = 0.5
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
        axis_paint = ft.Paint(stroke_width=2, color="#34b1eb", style=ft.PaintingStyle.STROKE)
        beam_paint = ft.Paint(stroke_width=2, color="#999", style=ft.PaintingStyle.FILL)
        cross_section_paint = ft.Paint(stroke_width=2, color="#456675", style=ft.PaintingStyle.STROKE)

        def draw_section_borders():
            xb1 = 0
            wb1 = self.realtime_width * self.section_width_fraction
            yb1 = 0
            hb1 = self.realtime_height * self.section_height_fraction
            xb2 = xb1 + wb1
            yb2 = yb1 + hb1
            for i in range(1, 3):
                # draw BEAM, SFD, BMD separator
                self.canvas_shape_group.shapes.append(cv.Line(
                    x1=xb1,
                    y1=yb2 * i,
                    x2=xb2,
                    y2=yb2 * i,
                    paint=box_paint,
                ))
                # draw separator for bending stress and shear stress

                self.canvas_shape_group.shapes.append(cv.Line(
                    x1=xb2,
                    y1=yb2 * i,
                    x2=self.realtime_width,
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

        def draw_beam():
            x1 = self.spacing
            w = self.section_width_fraction * self.realtime_width - 2 * self.spacing
            h = 50
            y1 = (self.realtime_height * self.section_height_fraction - h) / 2

            self.canvas_shape_group.shapes.append(cv.Rect(
                x=x1,
                y=y1,
                width=w,
                height=h,
                border_radius=5,
                paint=beam_paint
            ))
            self.canvas_shape_group.shapes.append(cv.Rect(
                x=x1,
                y=y1,
                width=w,
                height=h,
                border_radius=5,
                paint=box_paint
            ))

        def draw_beam_cross_section():
            center_x = self.realtime_width * self.section_width_fraction * (3 / 2)
            section_height = self.realtime_height * self.section_height_fraction
            section_width = self.realtime_width * self.section_width_fraction
            center_y = section_height / 2
            diameter = min(section_height, section_width) - self.spacing * 2
            if self.state.beam_type == "Circular":
                self.canvas_shape_group.shapes.append(cv.Circle(
                    x=center_x,
                    y=center_y,
                    radius=diameter / 2,
                    paint=cross_section_paint
                ))
            elif self.state.beam_type == "Rectangular":
                h1 = section_height - self.spacing * 2
                w1 = section_width - self.spacing * 2
                from frontend.StateManager import RectangularDimensions
                if isinstance(self.state.beam_dimensions, RectangularDimensions):
                    aspect = self.state.beam_dimensions.width_mm / max(1.0, self.state.beam_dimensions.height_mm)
                    if aspect > 1:
                        h1 /= aspect
                    else:
                        w1 *= aspect
                
                x1 = center_x - w1/2
                y1 = center_y - h1/2
                self.canvas_shape_group.shapes.append(cv.Rect(
                    x=x1,
                    y=y1,
                    height=h1,
                    width=w1,
                    paint=cross_section_paint
                ))
            elif self.state.beam_type == "I-Beam":
                from frontend.StateManager import IBeamDimensions
                if isinstance(self.state.beam_dimensions, IBeamDimensions):
                    h_mm = max(self.state.beam_dimensions.height_mm, 1.0)
                    fw_mm = self.state.beam_dimensions.flange_width_mm
                    ft_mm = self.state.beam_dimensions.flange_thickness_mm
                    wt_mm = self.state.beam_dimensions.web_thickness_mm

                    scale = (min(section_height, section_width) - self.spacing * 2) / max(h_mm, fw_mm, 1.0)
                    h_px = h_mm * scale
                    fw_px = fw_mm * scale
                    ft_px = ft_mm * scale
                    wt_px = wt_mm * scale

                    x0 = center_x - fw_px / 2
                    y0 = center_y - h_px / 2
                    cx = center_x

                    self.canvas_shape_group.shapes.append(
                        cv.Path(
                            [
                                cv.Path.MoveTo(x0, y0),
                                cv.Path.LineTo(x0 + fw_px, y0),
                                cv.Path.LineTo(x0 + fw_px, y0 + ft_px),
                                cv.Path.LineTo(cx + wt_px / 2, y0 + ft_px),
                                cv.Path.LineTo(cx + wt_px / 2, y0 + h_px - ft_px),
                                cv.Path.LineTo(x0 + fw_px, y0 + h_px - ft_px),
                                cv.Path.LineTo(x0 + fw_px, y0 + h_px),
                                cv.Path.LineTo(x0, y0 + h_px),
                                cv.Path.LineTo(x0, y0 + h_px - ft_px),
                                cv.Path.LineTo(cx - wt_px / 2, y0 + h_px - ft_px),
                                cv.Path.LineTo(cx - wt_px / 2, y0 + ft_px),
                                cv.Path.LineTo(x0, y0 + ft_px),
                                cv.Path.Close(),
                            ],
                            paint=cross_section_paint,
                        )
                    )

        def draw_graph(x: float, y: float, w: float, h: float, axis_paint, has_negatives_y=False,
                       has_negative_x=False) -> None:
            origin_x = x
            origin_y = y + h
            abscissa_y1 = origin_y
            abscissa_y2 = origin_y - h
            ordinate_x1 = origin_x
            ordinate_x2 = origin_x + w

            if has_negative_x:
                origin_x = x + w / 2
                ordinate_x1 = origin_x - w / 2
                ordinate_x2 = origin_x + w / 2

            if has_negatives_y:
                origin_y = y + h / 2
                abscissa_y1 = origin_y - h / 2
                abscissa_y2 = origin_y + h / 2

            self.canvas_shape_group.shapes.append(cv.Line(
                x1=origin_x,
                y1=abscissa_y1,
                x2=origin_x,
                y2=abscissa_y2,
                paint=axis_paint,
            ))
            self.canvas_shape_group.shapes.append(cv.Line(
                x1=ordinate_x1,
                y1=origin_y,
                x2=ordinate_x2,
                y2=origin_y,
                paint=axis_paint,
            ))

        draw_beam()
        draw_beam_cross_section()

        for i in range(1, 3):
            x = self.spacing
            h = self.realtime_height * self.section_height_fraction - self.spacing * 2
            y = self.realtime_height * self.section_height_fraction * i + self.spacing
            w = self.realtime_width * self.section_width_fraction - self.spacing * 2
            draw_graph(x, y, w,
                       h, axis_paint, False, False)
        for i in range(1, 3):
            x = self.realtime_width * self.section_width_fraction + self.spacing
            h = self.realtime_height * self.section_height_fraction - self.spacing * 2
            y = self.realtime_height * self.section_height_fraction * i + self.spacing
            w = self.realtime_width * self.section_width_fraction - self.spacing * 2
            draw_graph(x, y, w,
                       h, axis_paint, True, True)
        draw_section_borders()
        self.canvas_shape_group.update()
