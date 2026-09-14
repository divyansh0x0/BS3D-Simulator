import math
from collections.abc import Iterator
from itertools import tee
from numbers import Number
from turtledemo.chaos import h
from typing import Tuple

import flet as ft
import flet.canvas as cv
from flet import TextAlign
from flet.controls import border_radius, alignment

from frontend.StateManager import StateManager, PointLoadState, UDLLoadState, UVLLoadState


def min_max_y(points: list[Tuple[float, float]]) -> Tuple[float, float]:
    if not points:
        return 0.0, 0.0
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    return min_y, max_y
def min_max_x(points: list[Tuple[float, float]]) -> Tuple[float, float]:
    if not points:
        return 0.0, 0.0
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    return min_x, max_x

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

        def on_slider_change(e):
            self.state.cross_section_x = float(e.control.value)
            self.redraw()

        self.cross_section_slider = ft.Slider(
            min=0, max=max(0.1, self.state.beam_length),
            value=self.state.cross_section_x,
            label="Cross Section X: {value}m",
            on_change=on_slider_change,
            expand=True,
        )
        self.slider_row = ft.Row(
            controls=[
                ft.Text("Cross Section Position (m):"),
                self.cross_section_slider
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.canvas_container = ft.Container(
            content=self.canvas_shape_group,
            expand=True,
            on_size_change=self.update_realtime_size
        )

        self.spacing = 20
        self.content = ft.Column(
            controls=[
                self.canvas_container,
                self.slider_row
            ],
            expand=True
        )
        self.section_width_fraction = 0.5
        self.section_height_fraction = 1 / 3
        self.right_section_height_fraction = 0.5

        self.realtime_width = 0
        self.realtime_height = 0
        self.expand = True

    def update_realtime_size(self, e: ft.LayoutSizeChangeEvent) -> None:
        self.realtime_width = float(e.width)
        self.realtime_height = float(e.height)
        print(self.realtime_width, self.realtime_height)
        self.redraw()

    def get_rendered_beam_length(self) -> float:
        return self.realtime_width * self.section_width_fraction - self.spacing * 2

    def get_beam_height(self) -> float:
        return 50.0

    def redraw(self) -> None:
        self.canvas_shape_group.shapes.clear()

        # Sync slider with beam length changes
        self.cross_section_slider.max = max(0.1, self.state.beam_length)
        if self.cross_section_slider.value > self.state.beam_length:
            self.cross_section_slider.value = self.state.beam_length
            self.state.cross_section_x = self.state.beam_length
        try:
            self.slider_row.update()
        except RuntimeError:
            pass  # Control might not be added to page yet

        box_paint = ft.Paint(stroke_width=2, color="#aaa", style=ft.PaintingStyle.STROKE)
        axis_paint = ft.Paint(stroke_width=2, color="#34b1eb", style=ft.PaintingStyle.STROKE)
        beam_paint = ft.Paint(stroke_width=2, color="#999", style=ft.PaintingStyle.FILL)
        cross_section_paint = ft.Paint(stroke_width=2, color="#456675", style=ft.PaintingStyle.STROKE)
        graph_paint = ft.Paint(color="#304e5c", style=ft.PaintingStyle.FILL)
        load_paint = ft.Paint(stroke_width=3, color="#80FF0000", style=ft.PaintingStyle.FILL)

        def draw_arrow(x: float, y: float, angle: float = 0, paint=axis_paint) -> None:
            h1 = 5
            w1 = 3 * h1
            x1 = x - w1
            y1 = y + h1 / 2
            x2 = x - w1
            y2 = y - h1 / 2

            def transform(__x: float, __y: float, __cx: float, __cy: float, angle: float):
                angle_rad = angle * math.pi / 180
                rx = (__x - __cx) * math.cos(angle_rad) - (__y - __cy) * math.sin(angle_rad) + __cx
                ry = (__x - __cx) * math.sin(angle_rad) + (__y - __cy) * math.cos(angle_rad) + __cy
                return rx, ry

            tx1, ty1 = transform(x1, y1, x, y, angle)
            tx2, ty2 = transform(x2, y2, x, y, angle)

            self.canvas_shape_group.shapes.append(cv.Line(
                x1=tx1,
                x2=x,
                y1=ty1,
                y2=y,
                paint=paint
            ))

            self.canvas_shape_group.shapes.append(cv.Line(
                x1=tx2,
                x2=x,
                y1=ty2,
                y2=y,
                paint=paint
            ))

        def draw_loads():
            from frontend.StateManager import PointLoadState, UDLLoadState

            # Find the absolute maximum load for scaling
            max_load = 0.001
            for l in self.state.loads:
                if isinstance(l, PointLoadState):
                    max_load = max(max_load, abs(l.magnitude_kn))
                elif isinstance(l, UDLLoadState):
                    max_load = max(max_load, abs(l.intensity_kn_m))
                elif hasattr(l, 'start_intensity_kn_m'):
                    max_load = max(max_load, abs(l.start_intensity_kn_m), abs(l.end_intensity_kn_m))

            # Maximum available pixel height for the tallest load arrow
            beam_h = self.get_beam_height()
            max_px_h = (self.realtime_height * self.section_height_fraction - beam_h) / 2 - 25
            if max_px_h < 10:
                max_px_h = 10

            def get_px_h(value: float) -> float:
                return (abs(value) / max_load) * max_px_h * math.copysign(1, value)

            def get_text_align(is_downward: bool, pos_fraction: float):
                if is_downward:
                    if pos_fraction <= 0.01:
                        return alignment.Alignment.BOTTOM_LEFT
                    elif pos_fraction >= 0.99:
                        return alignment.Alignment.BOTTOM_RIGHT
                    else:
                        return alignment.Alignment.BOTTOM_CENTER
                else:
                    if pos_fraction <= 0.01:
                        return alignment.Alignment.TOP_LEFT
                    elif pos_fraction >= 0.99:
                        return alignment.Alignment.TOP_RIGHT
                    else:
                        return alignment.Alignment.TOP_CENTER

            def draw_point_load(value_kN: float, pos_meters: float, write_text=True, color="#EF4444",
                                is_reaction=False):
                if value_kN == 0.0 or self.state.beam_length <= 0: return

                x = self.spacing + (pos_meters / self.state.beam_length) * self.get_rendered_beam_length()

                if is_reaction:
                    # Reactions get a fixed visual height that doesn't scale with load magnitudes
                    h = (max_px_h * 0.75) * math.copysign(1, value_kN)
                else:
                    h = get_px_h(value_kN)

                # Beam top/bottom y-coordinates
                beam_top = (self.realtime_height * self.section_height_fraction - beam_h) / 2
                beam_bottom = beam_top + beam_h

                fraction = pos_meters / max(self.state.beam_length, 0.01)
                align = get_text_align(h > 0, fraction)

                if h > 0:
                    y2 = beam_top
                    y1 = y2 - h
                    arrow_angle = 90
                    text_y = y1 - 2
                else:
                    y2 = beam_bottom
                    y1 = y2 - h
                    arrow_angle = -90
                    text_y = y1 + 2

                local_paint = ft.Paint(stroke_width=2, color=color, style=ft.PaintingStyle.STROKE)
                self.canvas_shape_group.shapes.append(cv.Line(x1=x, y1=y1, x2=x, y2=y2, paint=local_paint))

                # Only draw the arrowhead if the shaft is longer than the arrowhead itself (15px)
                if abs(h) >= 15 or is_reaction:
                    draw_arrow(x, y2, arrow_angle, local_paint)

                if write_text:
                    self.canvas_shape_group.shapes.append(cv.Text(
                        x=x, y=text_y, value=f"{abs(value_kN):.2f}kN",
                        alignment=align,
                        style=ft.TextStyle(color=color, size=12)
                    ))

            def draw_uvl(val_start: float, val_end: float, pos_start: float, pos_end: float):
                if (val_start == 0.0 and val_end == 0.0) or self.state.beam_length <= 0: return

                x1 = self.spacing + (pos_start / self.state.beam_length) * self.get_rendered_beam_length()
                x2 = self.spacing + (pos_end / self.state.beam_length) * self.get_rendered_beam_length()
                w = max(1.0, x2 - x1)

                h_start = get_px_h(val_start)
                h_end = get_px_h(val_end)

                beam_top = (self.realtime_height * self.section_height_fraction - beam_h) / 2
                beam_bottom = beam_top + beam_h

                # Determine sign assumption (assuming a UVL doesn't cross the beam)
                dominant_val = val_start if abs(val_start) >= abs(val_end) else val_end

                if dominant_val > 0:
                    y1_base = beam_top
                    y2_base = beam_top
                    y1_top = beam_top - max(0, h_start)
                    y2_top = beam_top - max(0, h_end)
                    y_text_offset = -2
                else:
                    y1_base = beam_bottom
                    y2_base = beam_bottom
                    y1_top = beam_bottom - min(0, h_start)
                    y2_top = beam_bottom - min(0, h_end)
                    y_text_offset = 2

                # Transparent background
                fill_paint = ft.Paint(color="#44EF4444", style=ft.PaintingStyle.FILL)
                self.canvas_shape_group.shapes.append(cv.Path(
                    [
                        cv.Path.MoveTo(x1, y1_base),
                        cv.Path.LineTo(x1, y1_top),
                        cv.Path.LineTo(x2, y2_top),
                        cv.Path.LineTo(x2, y2_base),
                        cv.Path.Close()
                    ], paint=fill_paint
                ))

                # Draw boundary lines and text
                outline_paint = ft.Paint(stroke_width=1, color="#EF4444", style=ft.PaintingStyle.STROKE)
                self.canvas_shape_group.shapes.append(cv.Path(
                    [
                        cv.Path.MoveTo(x1, y1_base),
                        cv.Path.LineTo(x1, y1_top),
                        cv.Path.LineTo(x2, y2_top),
                        cv.Path.LineTo(x2, y2_base),
                        cv.Path.Close()
                    ], paint=outline_paint
                ))

                # Draw a few arrows inside to show direction
                arrow_spacing = 30
                num_arrows = int(w / arrow_spacing)
                for i in range(num_arrows + 1):
                    fraction = i / max(1, num_arrows)
                    val = val_start + (val_end - val_start) * fraction
                    pos = pos_start + (pos_end - pos_start) * fraction

                    # Don't draw internal arrows if the height is smaller than the arrowhead (15px)
                    if abs(get_px_h(val)) > 15:
                        draw_point_load(val, pos, False, color="#88EF4444")

                if val_start != 0:
                    fraction_start = pos_start / max(self.state.beam_length, 0.01)
                    align_start = get_text_align(dominant_val > 0, fraction_start)
                    self.canvas_shape_group.shapes.append(cv.Text(
                        x=x1, y=y1_top + y_text_offset, value=f"{abs(val_start):.2f}kN/m",
                        alignment=align_start,
                        style=ft.TextStyle(color="#EF4444", size=12)
                    ))
                if val_end != 0 and abs(val_start - val_end) > 0.001:
                    fraction_end = pos_end / max(self.state.beam_length, 0.01)
                    align_end = get_text_align(dominant_val > 0, fraction_end)
                    self.canvas_shape_group.shapes.append(cv.Text(
                        x=x2, y=y2_top + y_text_offset, value=f"{abs(val_end):.2f}kN/m",
                        alignment=align_end,
                        style=ft.TextStyle(color="#EF4444", size=12)
                    ))

            loads = list(self.state.loads)
            for l in loads:
                if isinstance(l, PointLoadState):
                    draw_point_load(l.magnitude_kn, l.position_m)
                elif isinstance(l, UDLLoadState):
                    draw_uvl(l.intensity_kn_m, l.intensity_kn_m, l.start_position_m, l.end_position_m)
                elif isinstance(l, UVLLoadState):
                    draw_uvl(l.start_intensity_kn_m, l.end_intensity_kn_m, l.start_position_m, l.end_position_m)

            # Draw reactions if they exist
            if hasattr(self.state, 'reaction_left_pos'):
                draw_point_load(-self.state.reaction_left, self.state.reaction_left_pos, color="#22C55E",
                                is_reaction=True)
                draw_point_load(-self.state.reaction_right, self.state.reaction_right_pos, color="#22C55E",
                                is_reaction=True)

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
            w = self.get_rendered_beam_length()
            h = self.get_beam_height()
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
                max_w = section_width - self.spacing * 2
                max_h = section_height - self.spacing * 2

                from frontend.StateManager import RectangularDimensions
                if isinstance(self.state.beam_dimensions, RectangularDimensions):
                    w_mm = max(1.0, self.state.beam_dimensions.width_mm)
                    h_mm = max(1.0, self.state.beam_dimensions.height_mm)

                    # Uniform scaling factor to fit inside max_w x max_h
                    scale = min(max_w / w_mm, max_h / h_mm)
                    w1 = w_mm * scale
                    h1 = h_mm * scale
                else:
                    w1 = min(max_w, max_h)
                    h1 = w1

                x1 = center_x - w1 / 2
                y1 = center_y - h1 / 2
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

        def draw_graph_axes(x: float, y: float, graph_width: float, graph_height: float, paint,
                            has_negatives_y: bool = False,
                            has_negative_x=False, point_iterator: Iterator[Tuple[float, float]] | None = None) -> None:
            origin_x = x
            origin_y = y + graph_height
            abscissa_y1 = origin_y
            abscissa_y2 = origin_y - graph_height
            ordinate_x1 = origin_x
            ordinate_x2 = origin_x + graph_width

            def draw_graph():
                if not point_iterator:
                    return

                points = list(point_iterator)
                if not points:
                    return

                min_y, max_y = min_max_y(points)
                l = []

                # Avoid division by zero if all values are zero
                graph_spacing = 0.001
                max_abs_y = max(abs(min_y) + graph_spacing, abs(max_y) + graph_spacing)
                if max_abs_y == 0:
                    max_abs_y = 1.0

                if has_negatives_y:
                    y_ratio = (abscissa_y2 - abscissa_y1) / (2 * max_abs_y)
                else:
                    y_ratio = (abscissa_y2 - abscissa_y1) / max_abs_y
                    
                min_x, max_x =  min_max_x(points)
                max_abs_x = max(abs(min_x) + graph_spacing, abs(max_x) + graph_spacing)

                if has_negative_x:
                    x_ratio = (ordinate_x2 - ordinate_x1) / (2 * max_abs_x)
                else:
                    x_ratio = (ordinate_x2 - ordinate_x1) / max_abs_x


                l.append(cv.Path.MoveTo(origin_x, origin_y))
                for gx, gy in points:
                    scaled_x = origin_x + gx * x_ratio
                    scaled_y = origin_y + gy * y_ratio
                    l.append(cv.Path.LineTo(scaled_x, scaled_y))

                print(points)
                l.append(cv.Path.LineTo(origin_x + self.state.beam_length * x_ratio, origin_y))
                l.append(cv.Path.Close())

                self.canvas_shape_group.shapes.append(cv.Path(l, graph_paint))

                # Draw the stroke (the actual line)
                graph_stroke_paint = ft.Paint(stroke_width=2, color="#5bc0de", style=ft.PaintingStyle.STROKE)
                self.canvas_shape_group.shapes.append(cv.Path(l, graph_stroke_paint))

            if has_negative_x:
                origin_x = x + graph_width / 2
                ordinate_x1 = origin_x - graph_width / 2
                ordinate_x2 = origin_x + graph_width / 2

            if has_negatives_y:
                origin_y = y + graph_height / 2
                abscissa_y2 = origin_y - graph_height / 2
                abscissa_y1 = origin_y + graph_height / 2

            # draw graph first so that axes lay above it
            draw_graph()
            # y-axis
            self.canvas_shape_group.shapes.append(cv.Line(
                x1=origin_x,
                y1=abscissa_y1,
                x2=origin_x,
                y2=abscissa_y2,
                paint=paint,
            ))
            # x-axis
            self.canvas_shape_group.shapes.append(cv.Line(
                x1=ordinate_x1,
                y1=origin_y,
                x2=ordinate_x2,
                y2=origin_y,
                paint=paint,
            ))
            draw_arrow(ordinate_x2, origin_y)
            draw_arrow(origin_x, abscissa_y2, -90)

        draw_beam()
        draw_loads()
        draw_beam_cross_section()

        for i in range(1, 3):
            x = self.spacing
            h = self.realtime_height * self.section_height_fraction - self.spacing * 2
            y = self.realtime_height * self.section_height_fraction * i + self.spacing
            w = self.realtime_width * self.section_width_fraction - self.spacing * 2

            # Scale number of points based on the pixel width of the graphing axis
            num_points = max(10, int(w))
            if i == 1:
                iterator = self.state.generate_sfd_points(num_points)
            else:
                iterator = self.state.generate_bmd_points(num_points)

            draw_graph_axes(x, y, w,
                            h, axis_paint, True, False, iterator)
        for i in range(1, 3):
            x = self.realtime_width * self.section_width_fraction + self.spacing
            h = self.realtime_height * self.section_height_fraction - self.spacing * 2
            y = self.realtime_height * self.section_height_fraction * i + self.spacing
            w = self.realtime_width * self.section_width_fraction - self.spacing * 2

            num_points = max(10, int(w))
            if i == 1:
                iterator = self.state.generate_shear_stress_points(num_points)
                global_max_x = getattr(self.state, 'max_shear_stress', None)
            else:
                iterator = self.state.generate_bending_stress_points(num_points)
                global_max_x = getattr(self.state, 'max_bending_stress', None)

            draw_graph_axes(x, y, w,
                            h, axis_paint, True, True, iterator)
        draw_section_borders()
        self.canvas_shape_group.update()
