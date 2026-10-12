from collections.abc import Iterator
from dataclasses import dataclass
from typing import List, Tuple

import flet as ft
import flet.canvas as cv

from frontend.components.canvas.drawing_utils import draw_arrow, min_max_xy


@dataclass(slots=True)
class GraphCoordinateSystem:
    origin_x: float
    origin_y: float
    abscissa_y1: float
    abscissa_y2: float
    ordinate_x1: float
    ordinate_x2: float
    x_ratio: float
    y_ratio: float
    max_abs_x: float
    max_abs_y: float
    has_negative_x: bool
    has_negatives_y: bool
    beam_length: float


class GraphRenderer:
    @staticmethod
    def compute_coordinate_system(
        x: float,
        y: float,
        graph_width: float,
        graph_height: float,
        beam_length: float,
        has_negatives_y: bool = False,
        has_negative_x: bool = False,
        points: List[Tuple[float, float]] | None = None,
        fixed_max_x: float | None = None,
        fixed_max_y: float | None = None,
    ) -> GraphCoordinateSystem:
        origin_x = x
        origin_y = y + graph_height
        abscissa_y1 = origin_y
        abscissa_y2 = origin_y - graph_height
        ordinate_x1 = origin_x
        ordinate_x2 = origin_x + graph_width

        if has_negative_x:
            origin_x = x + graph_width / 2.0
            ordinate_x1 = origin_x - graph_width / 2.0
            ordinate_x2 = origin_x + graph_width / 2.0

        if has_negatives_y:
            origin_y = y + graph_height / 2.0
            abscissa_y2 = origin_y - graph_height / 2.0
            abscissa_y1 = origin_y + graph_height / 2.0

        if fixed_max_y is not None:
            max_abs_y = fixed_max_y * 1.1
        elif points:
            _, _, min_y, max_y = min_max_xy(points)
            max_abs_y = max(abs(min_y), abs(max_y)) * 1.1
        else:
            max_abs_y = 1.0

        if max_abs_y == 0.0:
            max_abs_y = 1.0

        if has_negatives_y:
            y_ratio = (abscissa_y2 - abscissa_y1) / (2.0 * max_abs_y)
        else:
            y_ratio = (abscissa_y2 - abscissa_y1) / max_abs_y

        if has_negative_x:
            if fixed_max_x is not None:
                max_abs_x = fixed_max_x * 1.1
            elif points:
                min_x, max_x, _, _ = min_max_xy(points)
                max_abs_x = max(abs(min_x), abs(max_x)) * 1.1
            else:
                max_abs_x = 1.0
            if max_abs_x == 0.0:
                max_abs_x = 1.0
            x_ratio = (ordinate_x2 - ordinate_x1) / (2.0 * max_abs_x)
        else:
            max_abs_x = max(beam_length, 0.001)
            x_ratio = (ordinate_x2 - ordinate_x1) / max_abs_x

        return GraphCoordinateSystem(
            origin_x=origin_x,
            origin_y=origin_y,
            abscissa_y1=abscissa_y1,
            abscissa_y2=abscissa_y2,
            ordinate_x1=ordinate_x1,
            ordinate_x2=ordinate_x2,
            x_ratio=x_ratio,
            y_ratio=y_ratio,
            max_abs_x=max_abs_x,
            max_abs_y=max_abs_y,
            has_negative_x=has_negative_x,
            has_negatives_y=has_negatives_y,
            beam_length=beam_length,
        )

    @staticmethod
    def draw_curve(
        canvas: cv.Canvas,
        coord_sys: GraphCoordinateSystem,
        points: List[Tuple[float, float]],
        graph_fill_paint: ft.Paint,
        graph_stroke_paint: ft.Paint,
    ) -> None:
        if not points:
            return
        l = []
        if coord_sys.has_negative_x:
            l.append(cv.Path.MoveTo(coord_sys.origin_x, coord_sys.origin_y + points[0][1] * coord_sys.y_ratio))
        else:
            l.append(cv.Path.MoveTo(coord_sys.origin_x, coord_sys.origin_y))

        for gx, gy in points:
            scaled_x = coord_sys.origin_x + gx * coord_sys.x_ratio
            scaled_y = coord_sys.origin_y + gy * coord_sys.y_ratio
            l.append(cv.Path.LineTo(scaled_x, scaled_y))

        if coord_sys.has_negative_x:
            l.append(cv.Path.LineTo(coord_sys.origin_x, coord_sys.origin_y + points[-1][1] * coord_sys.y_ratio))
        else:
            l.append(cv.Path.LineTo(coord_sys.origin_x + coord_sys.beam_length * coord_sys.x_ratio, coord_sys.origin_y))

        l.append(cv.Path.Close())
        canvas.shapes.append(cv.Path(l, graph_fill_paint))
        canvas.shapes.append(cv.Path(l, graph_stroke_paint))

    @staticmethod
    def render_static_axes(
        canvas: cv.Canvas,
        coord_sys: GraphCoordinateSystem,
        paint: ft.Paint,
        top_y: float,
        spacing: float,
        x_label: str = "",
        y_label: str = "",
        graph_name: str = "",
    ) -> None:
        # y-axis
        canvas.shapes.append(
            cv.Line(
                x1=coord_sys.origin_x,
                y1=coord_sys.abscissa_y1,
                x2=coord_sys.origin_x,
                y2=coord_sys.abscissa_y2,
                paint=paint,
            )
        )
        # x-axis
        canvas.shapes.append(
            cv.Line(
                x1=coord_sys.ordinate_x1,
                y1=coord_sys.origin_y,
                x2=coord_sys.ordinate_x2,
                y2=coord_sys.origin_y,
                paint=paint,
            )
        )
        draw_arrow(canvas, coord_sys.ordinate_x2, coord_sys.origin_y, paint=paint)
        draw_arrow(canvas, coord_sys.origin_x, coord_sys.abscissa_y2, -90, paint=paint)

        # Axes Label at Top Left
        canvas.shapes.append(
            cv.Text(
                x=coord_sys.ordinate_x2 - 40,
                y=top_y - spacing + 5,
                value=f"x-axis: {x_label}\ny-axis: {y_label}",
                alignment=ft.alignment.Alignment.TOP_LEFT,
                style=ft.TextStyle(color=ft.Colors.TERTIARY, size=12),
            )
        )

        # Ticks for Y-axis
        text_style = ft.TextStyle(color=ft.Colors.ON_SURFACE_VARIANT, size=10)
        num_y_ticks = int((coord_sys.ordinate_x2 - coord_sys.ordinate_x1) / 100)
        for i in range(1, num_y_ticks + 1):
            val = coord_sys.max_abs_y * (i / num_y_ticks)
            tick_y = coord_sys.origin_y + val * coord_sys.y_ratio
            canvas.shapes.append(
                cv.Line(x1=coord_sys.origin_x - 3, y1=tick_y, x2=coord_sys.origin_x + 3, y2=tick_y, paint=paint)
            )
            canvas.shapes.append(
                cv.Text(
                    x=coord_sys.origin_x - 5,
                    y=tick_y,
                    value=f"{val:.1f}",
                    alignment=ft.alignment.Alignment.CENTER_RIGHT,
                    style=text_style,
                )
            )

            if coord_sys.has_negatives_y:
                tick_y_neg = coord_sys.origin_y - val * coord_sys.y_ratio
                canvas.shapes.append(
                    cv.Line(x1=coord_sys.origin_x - 3, y1=tick_y_neg, x2=coord_sys.origin_x + 3, y2=tick_y_neg, paint=paint)
                )
                canvas.shapes.append(
                    cv.Text(
                        x=coord_sys.origin_x - 5,
                        y=tick_y_neg,
                        value=f"{-val:.1f}",
                        alignment=ft.alignment.Alignment.CENTER_RIGHT,
                        style=text_style,
                    )
                )

        # Ticks for X-axis
        num_x_ticks = int((coord_sys.ordinate_x2 - coord_sys.ordinate_x1) / 100)
        for i in range(1, num_x_ticks + 1):
            val = coord_sys.max_abs_x * (i / num_x_ticks)
            tick_x = coord_sys.origin_x + val * coord_sys.x_ratio
            canvas.shapes.append(
                cv.Line(x1=tick_x, y1=coord_sys.origin_y - 3, x2=tick_x, y2=coord_sys.origin_y + 3, paint=paint)
            )
            canvas.shapes.append(
                cv.Text(
                    x=tick_x,
                    y=coord_sys.origin_y + 15,
                    value=f"{val:.1f}",
                    alignment=ft.alignment.Alignment.TOP_CENTER,
                    style=text_style,
                )
            )

            if coord_sys.has_negative_x:
                tick_x_neg = coord_sys.origin_x - val * coord_sys.x_ratio
                canvas.shapes.append(
                    cv.Line(x1=tick_x_neg, y1=coord_sys.origin_y - 3, x2=tick_x_neg, y2=coord_sys.origin_y + 3, paint=paint)
                )
                canvas.shapes.append(
                    cv.Text(
                        x=tick_x_neg,
                        y=coord_sys.origin_y + 15,
                        value=f"{-val:.1f}",
                        alignment=ft.alignment.Alignment.TOP_CENTER,
                        style=text_style,
                    )
                )

        if graph_name:
            canvas.shapes.append(
                cv.Text(
                    x=coord_sys.ordinate_x1 - spacing / 2.0,
                    y=top_y - 12,
                    value=graph_name,
                    alignment=ft.Alignment.BOTTOM_LEFT,
                    style=ft.TextStyle(size=16, color=ft.Colors.ON_SURFACE),
                )
            )

    @staticmethod
    def render_dynamic_marker(
        canvas: cv.Canvas,
        coord_sys: GraphCoordinateSystem,
        marker_point: Tuple[float, float] | None,
        marker_paint: ft.Paint,
    ) -> None:
        if not marker_point:
            return

        canvas.shapes.append(
            cv.Circle(
                x=coord_sys.origin_x + marker_point[0] * coord_sys.x_ratio,
                y=coord_sys.origin_y + marker_point[1] * coord_sys.y_ratio,
                radius=4,
                paint=marker_paint,
            )
        )
        canvas.shapes.append(
            cv.Circle(
                x=coord_sys.origin_x + marker_point[0] * coord_sys.x_ratio,
                y=coord_sys.origin_y,
                radius=4,
                paint=marker_paint,
            )
        )

        mx = coord_sys.origin_x + marker_point[0] * coord_sys.x_ratio + 5
        my = coord_sys.origin_y + marker_point[1] * coord_sys.y_ratio - 12
        text_style = ft.TextStyle(size=13, color=ft.Colors.TERTIARY)
        canvas.shapes.append(
            cv.Text(
                value=f"{marker_point[0]:.2f}",
                x=mx,
                y=coord_sys.origin_y + 12,
                alignment=ft.alignment.Alignment.CENTER_LEFT,
                style=text_style,
            )
        )
        canvas.shapes.append(
            cv.Text(
                value=f"{marker_point[1]:.2f}",
                x=mx,
                y=my,
                alignment=ft.alignment.Alignment.CENTER_LEFT,
                style=text_style,
            )
        )

    @classmethod
    def render_dynamic_curve_and_marker(
        cls,
        canvas: cv.Canvas,
        coord_sys: GraphCoordinateSystem,
        point_iterator: Iterator[Tuple[float, float]] | None,
        marker_point: Tuple[float, float] | None,
        graph_fill_paint: ft.Paint,
        graph_stroke_paint: ft.Paint,
        marker_paint: ft.Paint,
    ) -> None:
        points = list(point_iterator) if point_iterator else []
        cls.draw_curve(canvas, coord_sys, points, graph_fill_paint, graph_stroke_paint)
        cls.render_dynamic_marker(canvas, coord_sys, marker_point, marker_paint)

    @classmethod
    def render_static_graph(
        cls,
        canvas: cv.Canvas,
        x: float,
        y: float,
        graph_width: float,
        graph_height: float,
        paint: ft.Paint,
        graph_paint: ft.Paint,
        graph_stroke_paint: ft.Paint,
        beam_length: float,
        spacing: float,
        has_negatives_y: bool = False,
        has_negative_x: bool = False,
        point_iterator: Iterator[Tuple[float, float]] | None = None,
        x_label: str = "",
        y_label: str = "",
        graph_name: str = "",
        fixed_max_x: float | None = None,
        fixed_max_y: float | None = None,
    ) -> GraphCoordinateSystem:
        points = list(point_iterator) if point_iterator else []
        coord_sys = cls.compute_coordinate_system(
            x=x,
            y=y,
            graph_width=graph_width,
            graph_height=graph_height,
            beam_length=beam_length,
            has_negatives_y=has_negatives_y,
            has_negative_x=has_negative_x,
            points=points,
            fixed_max_x=fixed_max_x,
            fixed_max_y=fixed_max_y,
        )
        cls.draw_curve(canvas, coord_sys, points, graph_paint, graph_stroke_paint)
        cls.render_static_axes(
            canvas=canvas,
            coord_sys=coord_sys,
            paint=paint,
            top_y=y,
            spacing=spacing,
            x_label=x_label,
            y_label=y_label,
            graph_name=graph_name,
        )
        return coord_sys

    @classmethod
    def render_static_axes_only(
        cls,
        canvas: cv.Canvas,
        x: float,
        y: float,
        graph_width: float,
        graph_height: float,
        paint: ft.Paint,
        beam_length: float,
        spacing: float,
        has_negatives_y: bool = False,
        has_negative_x: bool = False,
        x_label: str = "",
        y_label: str = "",
        graph_name: str = "",
        fixed_max_x: float | None = None,
        fixed_max_y: float | None = None,
    ) -> GraphCoordinateSystem:
        coord_sys = cls.compute_coordinate_system(
            x=x,
            y=y,
            graph_width=graph_width,
            graph_height=graph_height,
            beam_length=beam_length,
            has_negatives_y=has_negatives_y,
            has_negative_x=has_negative_x,
            points=None,
            fixed_max_x=fixed_max_x,
            fixed_max_y=fixed_max_y,
        )
        cls.render_static_axes(
            canvas=canvas,
            coord_sys=coord_sys,
            paint=paint,
            top_y=y,
            spacing=spacing,
            x_label=x_label,
            y_label=y_label,
            graph_name=graph_name,
        )
        return coord_sys

    @classmethod
    def render_axes(
        cls,
        canvas: cv.Canvas,
        x: float,
        y: float,
        graph_width: float,
        graph_height: float,
        paint: ft.Paint,
        graph_paint: ft.Paint,
        beam_length: float,
        spacing: float,
        has_negatives_y: bool = False,
        has_negative_x: bool = False,
        point_iterator: Iterator[Tuple[float, float]] | None = None,
        marker_point: Tuple[float, float] | None = None,
        x_label: str = "",
        y_label: str = "",
        graph_name: str = "",
        fixed_max_x: float | None = None,
    ) -> None:
        graph_stroke_paint = ft.Paint(
            stroke_width=2,
            color=ft.Colors.PRIMARY,
            style=ft.PaintingStyle.STROKE,
        )
        marker_paint = ft.Paint(color=ft.Colors.PRIMARY)
        coord_sys = cls.render_static_graph(
            canvas=canvas,
            x=x,
            y=y,
            graph_width=graph_width,
            graph_height=graph_height,
            paint=paint,
            graph_paint=graph_paint,
            graph_stroke_paint=graph_stroke_paint,
            beam_length=beam_length,
            spacing=spacing,
            has_negatives_y=has_negatives_y,
            has_negative_x=has_negative_x,
            point_iterator=point_iterator,
            x_label=x_label,
            y_label=y_label,
            graph_name=graph_name,
            fixed_max_x=fixed_max_x,
        )
        cls.render_dynamic_marker(
            canvas=canvas,
            coord_sys=coord_sys,
            marker_point=marker_point,
            marker_paint=marker_paint,
        )
