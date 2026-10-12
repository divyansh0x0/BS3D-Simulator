from dataclasses import dataclass

import flet as ft


@dataclass(slots=True)
class CanvasPaintPalette:
    """Pre-allocated Paint instances to eliminate per-frame GC allocations."""
    box_paint: ft.Paint
    axis_paint: ft.Paint
    beam_stroke_paint: ft.Paint
    cross_section_paint: ft.Paint
    graph_fill_paint: ft.Paint
    graph_stroke_paint: ft.Paint
    marker_paint: ft.Paint
    slider_line_paint: ft.Paint
    neutral_axis_paint: ft.Paint
    depth_line_paint: ft.Paint

    @classmethod
    def create_default(cls) -> "CanvasPaintPalette":
        return cls(
            box_paint=ft.Paint(
                stroke_width=2,
                color=ft.Colors.OUTLINE,
                style=ft.PaintingStyle.STROKE,
            ),
            axis_paint=ft.Paint(
                stroke_width=2,
                color=ft.Colors.PRIMARY,
                style=ft.PaintingStyle.STROKE,
            ),
            beam_stroke_paint=ft.Paint(
                stroke_width=2,
                color=ft.Colors.PRIMARY,
                style=ft.PaintingStyle.STROKE,
            ),
            cross_section_paint=ft.Paint(
                stroke_width=2,
                color=ft.Colors.SECONDARY,
                style=ft.PaintingStyle.STROKE,
            ),
            graph_fill_paint=ft.Paint(
                color=ft.Colors.SECONDARY_CONTAINER,
                style=ft.PaintingStyle.FILL,
            ),
            graph_stroke_paint=ft.Paint(
                stroke_width=2,
                color=ft.Colors.PRIMARY,
                style=ft.PaintingStyle.STROKE,
            ),
            marker_paint=ft.Paint(
                color=ft.Colors.PRIMARY,
                style=ft.PaintingStyle.FILL,
            ),
            slider_line_paint=ft.Paint(
                stroke_width=2,
                color=ft.Colors.PRIMARY,
                style=ft.PaintingStyle.STROKE,
            ),
            neutral_axis_paint=ft.Paint(
                stroke_width=2,
                color=ft.Colors.TERTIARY,
                style=ft.PaintingStyle.STROKE,
            ),
            depth_line_paint=ft.Paint(
                stroke_width=2,
                color=ft.Colors.SECONDARY,
                style=ft.PaintingStyle.STROKE,
            ),
        )
