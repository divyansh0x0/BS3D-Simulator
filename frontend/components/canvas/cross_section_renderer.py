from dataclasses import dataclass
from typing import Any

import flet as ft
import flet.canvas as cv

from frontend.models import IBeamDimensions, RectangularDimensions


@dataclass(slots=True)
class CrossSectionGeometryMetrics:
    """Dimensions of rendered beam cross section in screen pixels."""
    center_x: float
    center_y: float
    pixel_width: float
    pixel_height: float
    section_width: float
    real_height: float


class CrossSectionRenderer:
    @classmethod
    def render_static_profile(
        cls,
        canvas: cv.Canvas,
        state: Any,
        realtime_width: float,
        realtime_height: float,
        section_width_fraction: float,
        section_height_fraction: float,
        spacing: float,
        cross_section_paint: ft.Paint,
        neutral_axis_paint: ft.Paint,
    ) -> CrossSectionGeometryMetrics:
        center_x = realtime_width * section_width_fraction * (3.0 / 2.0)
        section_height = realtime_height * section_height_fraction
        section_width = realtime_width * section_width_fraction
        center_y = section_height / 2.0
        diameter = min(section_height, section_width) - spacing * 2.0

        h1 = diameter
        w1 = diameter
        h_px = diameter
        fw_px = diameter

        if state.beam_type == "Circular":
            canvas.shapes.append(
                cv.Circle(
                    x=center_x,
                    y=center_y,
                    radius=diameter / 2.0,
                    paint=cross_section_paint,
                )
            )
        elif state.beam_type == "Rectangular":
            max_w = section_width - spacing * 2.0
            max_h = section_height - spacing * 2.0

            if isinstance(state.beam_dimensions, RectangularDimensions):
                w_mm = max(1.0, state.beam_dimensions.width_mm)
                h_mm = max(1.0, state.beam_dimensions.height_mm)
                scale = min(max_w / w_mm, max_h / h_mm)
                w1 = w_mm * scale
                h1 = h_mm * scale
            else:
                w1 = min(max_w, max_h)
                h1 = w1

            x1 = center_x - w1 / 2.0
            y1 = center_y - h1 / 2.0
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

                scale = (min(section_height, section_width) - spacing * 2.0) / max(h_mm, fw_mm, 1.0)
                h_px = h_mm * scale
                fw_px = fw_mm * scale
                ft_px = ft_mm * scale
                wt_px = wt_mm * scale

                x0 = center_x - fw_px / 2.0
                y0 = center_y - h_px / 2.0
                cx = center_x

                canvas.shapes.append(
                    cv.Path(
                        [
                            cv.Path.MoveTo(x0, y0),
                            cv.Path.LineTo(x0 + fw_px, y0),
                            cv.Path.LineTo(x0 + fw_px, y0 + ft_px),
                            cv.Path.LineTo(cx + wt_px / 2.0, y0 + ft_px),
                            cv.Path.LineTo(cx + wt_px / 2.0, y0 + h_px - ft_px),
                            cv.Path.LineTo(x0 + fw_px, y0 + h_px - ft_px),
                            cv.Path.LineTo(x0 + fw_px, y0 + h_px),
                            cv.Path.LineTo(x0, y0 + h_px),
                            cv.Path.LineTo(x0, y0 + h_px - ft_px),
                            cv.Path.LineTo(cx - wt_px / 2.0, y0 + h_px - ft_px),
                            cv.Path.LineTo(cx - wt_px / 2.0, y0 + ft_px),
                            cv.Path.LineTo(x0, y0 + ft_px),
                            cv.Path.Close(),
                        ],
                        paint=cross_section_paint,
                    )
                )

        real_height = state._beam.get_height() if state._beam is not None else 1.0
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

        # Fixed Neutral axis line
        canvas.shapes.append(
            cv.Line(
                x1=center_x - pixel_width / 2.0 - 10.0,
                y1=center_y,
                x2=center_x + pixel_width / 2.0 + 10.0,
                y2=center_y,
                paint=neutral_axis_paint,
            )
        )
        canvas.shapes.append(
            cv.Text(
                value="Neutral Axis",
                x=center_x,
                y=center_y - 5.0,
                alignment=ft.Alignment.BOTTOM_CENTER,
                style=ft.TextStyle(size=12, color=ft.Colors.SECONDARY),
            )
        )

        return CrossSectionGeometryMetrics(
            center_x=center_x,
            center_y=center_y,
            pixel_width=pixel_width,
            pixel_height=pixel_height,
            section_width=section_width,
            real_height=real_height,
        )

    @classmethod
    def render_dynamic_depth_indicator(
        cls,
        canvas: cv.Canvas,
        state: Any,
        metrics: CrossSectionGeometryMetrics,
        depth_line_paint: ft.Paint,
    ) -> None:
        """Fast dynamic rendering of the y depth indicator line and coordinate label."""
        if metrics.real_height <= 0.0:
            return

        y_offset_px = (state.cross_section_y_meters / metrics.real_height) * metrics.pixel_height
        target_y = metrics.center_y - y_offset_px

        canvas.shapes.append(
            cv.Line(
                x1=metrics.center_x - metrics.section_width / 2.0,
                y1=target_y,
                x2=metrics.center_x + metrics.section_width / 2.0,
                y2=target_y,
                paint=depth_line_paint,
            )
        )
        canvas.shapes.append(
            cv.Text(
                value=f"y={state.cross_section_y_meters * 1000.0:.2f}mm",
                x=metrics.center_x - metrics.section_width / 2.0 + 10.0,
                y=target_y - 5.0,
                alignment=ft.Alignment.BOTTOM_LEFT,
                style=ft.TextStyle(size=12, color=ft.Colors.SECONDARY),
            )
        )

    @classmethod
    def render(
        cls,
        canvas: cv.Canvas,
        state: Any,
        realtime_width: float,
        realtime_height: float,
        section_width_fraction: float,
        section_height_fraction: float,
        spacing: float,
        cross_section_paint: ft.Paint,
    ) -> None:
        """Backward-compatible all-in-one render method."""
        neutral_paint = ft.Paint(
            stroke_width=2,
            color=ft.Colors.TERTIARY,
            style=ft.PaintingStyle.STROKE,
        )
        depth_paint = ft.Paint(
            stroke_width=2,
            color=ft.Colors.SECONDARY,
            style=ft.PaintingStyle.STROKE,
        )
        metrics = cls.render_static_profile(
            canvas,
            state,
            realtime_width,
            realtime_height,
            section_width_fraction,
            section_height_fraction,
            spacing,
            cross_section_paint,
            neutral_paint,
        )
        cls.render_dynamic_depth_indicator(canvas, state, metrics, depth_paint)
