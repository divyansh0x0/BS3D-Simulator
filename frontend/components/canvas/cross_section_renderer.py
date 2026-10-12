from typing import Any

import flet as ft
import flet.canvas as cv

from frontend.models import IBeamDimensions, RectangularDimensions


class CrossSectionRenderer:
    @staticmethod
    def render(
        canvas: cv.Canvas,
        state: Any,
        realtime_width: float,
        realtime_height: float,
        section_width_fraction: float,
        section_height_fraction: float,
        spacing: float,
        cross_section_paint: ft.Paint,
    ) -> None:
        center_x = realtime_width * section_width_fraction * (3 / 2)
        section_height = realtime_height * section_height_fraction
        section_width = realtime_width * section_width_fraction
        center_y = section_height / 2
        diameter = min(section_height, section_width) - spacing * 2

        h1 = diameter
        w1 = diameter
        h_px = diameter
        fw_px = diameter

        if state.beam_type == "Circular":
            canvas.shapes.append(
                cv.Circle(
                    x=center_x,
                    y=center_y,
                    radius=diameter / 2,
                    paint=cross_section_paint,
                )
            )
        elif state.beam_type == "Rectangular":
            max_w = section_width - spacing * 2
            max_h = section_height - spacing * 2

            if isinstance(state.beam_dimensions, RectangularDimensions):
                w_mm = max(1.0, state.beam_dimensions.width_mm)
                h_mm = max(1.0, state.beam_dimensions.height_mm)

                # Uniform scaling factor to fit inside max_w x max_h
                scale = min(max_w / w_mm, max_h / h_mm)
                w1 = w_mm * scale
                h1 = h_mm * scale
            else:
                w1 = min(max_w, max_h)
                h1 = w1

            x1 = center_x - w1 / 2
            y1 = center_y - h1 / 2
            canvas.shapes.append(
                cv.Rect(
                    x=x1,
                    y=y1,
                    height=h1,
                    width=w1,
                    paint=cross_section_paint,
                )
            )
        elif state.beam_type == "I-Beam":
            if isinstance(state.beam_dimensions, IBeamDimensions):
                h_mm = max(state.beam_dimensions.height_mm, 1.0)
                fw_mm = state.beam_dimensions.flange_width_mm
                ft_mm = state.beam_dimensions.flange_thickness_mm
                wt_mm = state.beam_dimensions.web_thickness_mm

                scale = (min(section_height, section_width) - spacing * 2) / max(h_mm, fw_mm, 1.0)
                h_px = h_mm * scale
                fw_px = fw_mm * scale
                ft_px = ft_mm * scale
                wt_px = wt_mm * scale

                x0 = center_x - fw_px / 2
                y0 = center_y - h_px / 2
                cx = center_x

                canvas.shapes.append(
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

        if state._beam is not None:
            real_height = state._beam.get_height()
            if real_height > 0:
                if state.beam_type == "Circular":
                    pixel_height = diameter
                    pixel_width = diameter
                elif state.beam_type == "Rectangular":
                    pixel_height = h1
                    pixel_width = w1
                elif state.beam_type == "I-Beam":
                    pixel_height = h_px
                    pixel_width = fw_px
                else:
                    pixel_height = diameter
                    pixel_width = diameter

                y_offset_px = (state.cross_section_y_meters / real_height) * pixel_height
                line_y = center_y

                # neutral axis
                canvas.shapes.append(
                    cv.Line(
                        x1=center_x - pixel_width / 2 - 10,
                        y1=line_y,
                        x2=center_x + pixel_width / 2 + 10,
                        y2=line_y,
                        paint=ft.Paint(
                            stroke_width=2,
                            color=ft.Colors.TERTIARY,
                            style=ft.PaintingStyle.STROKE,
                        ),
                    )
                )
                canvas.shapes.append(
                    cv.Text(
                        value="Neutral Axis",
                        x=center_x,
                        y=line_y - 5,
                        alignment=ft.Alignment.BOTTOM_CENTER,
                        style=ft.TextStyle(size=12, color=ft.Colors.SECONDARY),
                    )
                )
                # line parallel to neutral axis
                canvas.shapes.append(
                    cv.Line(
                        x1=center_x - section_width / 2,
                        y1=line_y - y_offset_px,
                        x2=center_x + section_width / 2,
                        y2=line_y - y_offset_px,
                        paint=ft.Paint(
                            stroke_width=2,
                            color=ft.Colors.SECONDARY,
                            style=ft.PaintingStyle.STROKE,
                        ),
                    )
                )
                canvas.shapes.append(
                    cv.Text(
                        value=f"y={state.cross_section_y_meters * 1000:.2f}mm",
                        x=center_x - section_width / 2 + 10,
                        y=line_y - y_offset_px - 5,
                        alignment=ft.Alignment.BOTTOM_LEFT,
                        style=ft.TextStyle(size=12, color=ft.Colors.SECONDARY),
                    )
                )
