import math
from typing import Any

import flet as ft
import flet.canvas as cv
from flet.controls import alignment

from frontend.components.canvas.drawing_utils import draw_arrow
from frontend.models import PointLoadState, UDLLoadState, UVLLoadState


class LoadRenderer:
    @staticmethod
    def render(
        canvas: cv.Canvas,
        state: Any,
        spacing: float,
        rendered_beam_length: float,
        beam_h: float,
        realtime_height: float,
        section_height_fraction: float,
    ) -> None:
        max_load = 0.001
        for l in state.loads:
            if isinstance(l, PointLoadState):
                max_load = max(max_load, abs(l.magnitude_kn))
            elif isinstance(l, UDLLoadState):
                max_load = max(max_load, abs(l.intensity_kn_m))
            elif isinstance(l, UVLLoadState):
                max_load = max(max_load, abs(l.start_intensity_kn_m), abs(l.end_intensity_kn_m))

        # Maximum available pixel height for the tallest load arrow
        max_px_h = (realtime_height * section_height_fraction - beam_h) / 2 - 25
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

        def draw_point_load(
            value_kN: float,
            pos_meters: float,
            write_text: bool = True,
            color=ft.Colors.ERROR,
            is_reaction: bool = False,
        ) -> None:
            if value_kN == 0.0 or state.beam_length <= 0:
                return

            x = spacing + (pos_meters / state.beam_length) * rendered_beam_length

            if is_reaction:
                # Reactions get a fixed visual height that doesn't scale with load magnitudes
                h = (max_px_h * 0.75) * math.copysign(1, value_kN)
            else:
                h = get_px_h(value_kN)

            # Beam top/bottom y-coordinates
            beam_top = (realtime_height * section_height_fraction - beam_h) / 2
            beam_bottom = beam_top + beam_h

            fraction = pos_meters / max(state.beam_length, 0.01)
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
            canvas.shapes.append(cv.Line(x1=x, y1=y1, x2=x, y2=y2, paint=local_paint))

            # Only draw the arrowhead if the shaft is longer than the arrowhead itself (15px)
            if abs(h) >= 15 or is_reaction:
                draw_arrow(canvas, x, y2, arrow_angle, local_paint)

            if write_text:
                canvas.shapes.append(
                    cv.Text(
                        x=x,
                        y=text_y,
                        value=f"{abs(value_kN):.2f}kN",
                        alignment=align,
                        style=ft.TextStyle(color=color, size=12),
                    )
                )

        def draw_uvl(val_start: float, val_end: float, pos_start: float, pos_end: float) -> None:
            if (val_start == 0.0 and val_end == 0.0) or state.beam_length <= 0:
                return

            x1 = spacing + (pos_start / state.beam_length) * rendered_beam_length
            x2 = spacing + (pos_end / state.beam_length) * rendered_beam_length
            w = max(1.0, x2 - x1)

            h_start = get_px_h(val_start)
            h_end = get_px_h(val_end)

            beam_top = (realtime_height * section_height_fraction - beam_h) / 2
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
            fill_paint = ft.Paint(
                color=ft.Colors.with_opacity(0.2, ft.Colors.ERROR),
                style=ft.PaintingStyle.FILL,
            )
            canvas.shapes.append(
                cv.Path(
                    [
                        cv.Path.MoveTo(x1, y1_base),
                        cv.Path.LineTo(x1, y1_top),
                        cv.Path.LineTo(x2, y2_top),
                        cv.Path.LineTo(x2, y2_base),
                        cv.Path.Close(),
                    ],
                    paint=fill_paint,
                )
            )

            # Draw boundary lines and text
            outline_paint = ft.Paint(
                stroke_width=1,
                color=ft.Colors.ERROR,
                style=ft.PaintingStyle.STROKE,
            )
            canvas.shapes.append(
                cv.Path(
                    [
                        cv.Path.MoveTo(x1, y1_base),
                        cv.Path.LineTo(x1, y1_top),
                        cv.Path.LineTo(x2, y2_top),
                        cv.Path.LineTo(x2, y2_base),
                        cv.Path.Close(),
                    ],
                    paint=outline_paint,
                )
            )

            # Draw a few arrows inside to show direction
            arrow_spacing = 30
            num_arrows = int(w / arrow_spacing)
            for i in range(num_arrows + 1):
                fraction = i / max(1, num_arrows)
                val = val_start + (val_end - val_start) * fraction
                pos = pos_start + (pos_end - pos_start) * fraction

                # Don't draw internal arrows if the height is smaller than the arrowhead (15px)
                if abs(get_px_h(val)) > 15:
                    draw_point_load(
                        val,
                        pos,
                        False,
                        color=ft.Colors.with_opacity(0.5, ft.Colors.ERROR),
                    )

            if val_start != 0:
                fraction_start = pos_start / max(state.beam_length, 0.01)
                align_start = get_text_align(dominant_val > 0, fraction_start)
                canvas.shapes.append(
                    cv.Text(
                        x=x1,
                        y=y1_top + y_text_offset,
                        value=f"{abs(val_start):.2f}kN/m",
                        alignment=align_start,
                        style=ft.TextStyle(color=ft.Colors.ERROR, size=12),
                    )
                )
            if val_end != 0 and abs(val_start - val_end) > 0.001:
                fraction_end = pos_end / max(state.beam_length, 0.01)
                align_end = get_text_align(dominant_val > 0, fraction_end)
                canvas.shapes.append(
                    cv.Text(
                        x=x2,
                        y=y2_top + y_text_offset,
                        value=f"{abs(val_end):.2f}kN/m",
                        alignment=align_end,
                        style=ft.TextStyle(color=ft.Colors.ERROR, size=12),
                    )
                )

        loads = list(state.loads)
        for l in loads:
            if isinstance(l, PointLoadState):
                draw_point_load(l.magnitude_kn, l.position_m)
            elif isinstance(l, UDLLoadState):
                draw_uvl(l.intensity_kn_m, l.intensity_kn_m, l.start_position_m, l.end_position_m)
            elif isinstance(l, UVLLoadState):
                draw_uvl(l.start_intensity_kn_m, l.end_intensity_kn_m, l.start_position_m, l.end_position_m)

        # Draw reactions if they exist
        if hasattr(state, "reaction_left_pos"):
            draw_point_load(
                -state.reaction_left,
                state.reaction_left_pos,
                color=ft.Colors.TERTIARY,
                is_reaction=True,
            )
            draw_point_load(
                -state.reaction_right,
                state.reaction_right_pos,
                color=ft.Colors.TERTIARY,
                is_reaction=True,
            )
