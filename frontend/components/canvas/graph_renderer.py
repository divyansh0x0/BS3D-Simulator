from collections.abc import Iterator
from typing import Tuple

import flet as ft
import flet.canvas as cv

from frontend.components.canvas.drawing_utils import draw_arrow, min_max_x, min_max_y, min_max_xy


class GraphRenderer:
    @staticmethod
    def render_axes(
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
        origin_x = x
        origin_y = y + graph_height
        abscissa_y1 = origin_y
        abscissa_y2 = origin_y - graph_height
        ordinate_x1 = origin_x
        ordinate_x2 = origin_x + graph_width

        if has_negative_x:
            origin_x = x + graph_width / 2
            ordinate_x1 = origin_x - graph_width / 2
            ordinate_x2 = origin_x + graph_width / 2

        if has_negatives_y:
            origin_y = y + graph_height / 2
            abscissa_y2 = origin_y - graph_height / 2
            abscissa_y1 = origin_y + graph_height / 2

        points = []
        if point_iterator:
            points = list(point_iterator)

        if not points:
            min_y, max_y = 0.0, 0.0
            min_x, max_x = 0.0, 0.0
        else:
            min_x, max_x, min_y, max_y = min_max_xy(points)

        max_abs_y = max(abs(min_y), abs(max_y)) * 1.1
        if max_abs_y == 0:
            max_abs_y = 1.0

        if has_negatives_y:
            y_ratio = (abscissa_y2 - abscissa_y1) / (2 * max_abs_y)
        else:
            y_ratio = (abscissa_y2 - abscissa_y1) / max_abs_y

        if has_negative_x:
            if fixed_max_x is not None:
                max_abs_x = fixed_max_x * 1.1
            else:
                max_abs_x = max(abs(min_x), abs(max_x)) * 1.1
            if max_abs_x == 0:
                max_abs_x = 1.0
            x_ratio = (ordinate_x2 - ordinate_x1) / (2 * max_abs_x)
        else:
            max_abs_x = max(beam_length, 0.001)
            x_ratio = (ordinate_x2 - ordinate_x1) / max_abs_x

        def draw_graph():
            if not points:
                return
            l = []

            if has_negative_x:
                l.append(cv.Path.MoveTo(origin_x, origin_y + points[0][1] * y_ratio))
            else:
                l.append(cv.Path.MoveTo(origin_x, origin_y))

            for gx, gy in points:
                scaled_x = origin_x + gx * x_ratio
                scaled_y = origin_y + gy * y_ratio
                l.append(cv.Path.LineTo(scaled_x, scaled_y))

            if has_negative_x:
                l.append(cv.Path.LineTo(origin_x, origin_y + points[-1][1] * y_ratio))
            else:
                l.append(cv.Path.LineTo(origin_x + beam_length * x_ratio, origin_y))

            l.append(cv.Path.Close())

            canvas.shapes.append(cv.Path(l, graph_paint))

            graph_stroke_paint = ft.Paint(
                stroke_width=2,
                color=ft.Colors.PRIMARY,
                style=ft.PaintingStyle.STROKE,
            )
            canvas.shapes.append(cv.Path(l, graph_stroke_paint))

        # draw graph first so that axes lay above it
        draw_graph()

        # y-axis
        canvas.shapes.append(
            cv.Line(
                x1=origin_x,
                y1=abscissa_y1,
                x2=origin_x,
                y2=abscissa_y2,
                paint=paint,
            )
        )
        # x-axis
        canvas.shapes.append(
            cv.Line(
                x1=ordinate_x1,
                y1=origin_y,
                x2=ordinate_x2,
                y2=origin_y,
                paint=paint,
            )
        )
        draw_arrow(canvas, ordinate_x2, origin_y, paint=paint)
        draw_arrow(canvas, origin_x, abscissa_y2, -90, paint=paint)

        # Draw Labels and Ticks

        # Axes Label at Top Left
        canvas.shapes.append(
            cv.Text(
                x=ordinate_x2 - 40,
                y=y - spacing + 5,
                value=f"x-axis: {x_label}\ny-axis: {y_label}",
                alignment=ft.alignment.Alignment.TOP_LEFT,
                style=ft.TextStyle(color=ft.Colors.TERTIARY, size=12),
            )
        )

        # Ticks for Y-axis
        text_style = ft.TextStyle(color=ft.Colors.ON_SURFACE_VARIANT, size=10)
        # 100 pixel wide tick count
        num_y_ticks = int((ordinate_x2 - ordinate_x1) / 100)
        for i in range(1, num_y_ticks + 1):
            val = max_abs_y * (i / num_y_ticks)
            # Positive tick
            tick_y = origin_y + val * y_ratio
            canvas.shapes.append(
                cv.Line(x1=origin_x - 3, y1=tick_y, x2=origin_x + 3, y2=tick_y, paint=paint)
            )
            canvas.shapes.append(
                cv.Text(
                    x=origin_x - 5,
                    y=tick_y,
                    value=f"{val:.1f}",
                    alignment=ft.alignment.Alignment.CENTER_RIGHT,
                    style=text_style,
                )
            )

            if has_negatives_y:
                # Negative tick
                tick_y_neg = origin_y - val * y_ratio
                canvas.shapes.append(
                    cv.Line(x1=origin_x - 3, y1=tick_y_neg, x2=origin_x + 3, y2=tick_y_neg, paint=paint)
                )
                canvas.shapes.append(
                    cv.Text(
                        x=origin_x - 5,
                        y=tick_y_neg,
                        value=f"{-val:.1f}",
                        alignment=ft.alignment.Alignment.CENTER_RIGHT,
                        style=text_style,
                    )
                )

        # Ticks for X-axis
        # 100 pixel wide tick count
        num_x_ticks = int((ordinate_x2 - ordinate_x1) / 100)
        for i in range(1, num_x_ticks + 1):
            val = max_abs_x * (i / num_x_ticks)
            # Positive tick
            tick_x = origin_x + val * x_ratio
            canvas.shapes.append(
                cv.Line(x1=tick_x, y1=origin_y - 3, x2=tick_x, y2=origin_y + 3, paint=paint)
            )
            canvas.shapes.append(
                cv.Text(
                    x=tick_x,
                    y=origin_y + 15,
                    value=f"{val:.1f}",
                    alignment=ft.alignment.Alignment.TOP_CENTER,
                    style=text_style,
                )
            )

            if has_negative_x:
                # Negative tick
                tick_x_neg = origin_x - val * x_ratio
                canvas.shapes.append(
                    cv.Line(x1=tick_x_neg, y1=origin_y - 3, x2=tick_x_neg, y2=origin_y + 3, paint=paint)
                )
                canvas.shapes.append(
                    cv.Text(
                        x=tick_x_neg,
                        y=origin_y + 15,
                        value=f"{-val:.1f}",
                        alignment=ft.alignment.Alignment.TOP_CENTER,
                        style=text_style,
                    )
                )

        if graph_name:
            canvas.shapes.append(
                cv.Text(
                    x=x - spacing / 2,
                    y=y - 12,
                    value=graph_name,
                    alignment=ft.Alignment.BOTTOM_LEFT,
                    style=ft.TextStyle(size=16, color=ft.Colors.ON_SURFACE),
                )
            )

        # marking for current cross section
        if not marker_point:
            return

        point_paint = ft.Paint(color=ft.Colors.PRIMARY)
        canvas.shapes.append(
            cv.Circle(
                x=origin_x + marker_point[0] * x_ratio,
                y=origin_y + marker_point[1] * y_ratio,
                radius=4,
                paint=point_paint,
            )
        )
        canvas.shapes.append(
            cv.Circle(
                x=origin_x + marker_point[0] * x_ratio,
                y=origin_y,
                radius=4,
                paint=point_paint,
            )
        )

        mx = origin_x + marker_point[0] * x_ratio + 5
        my = origin_y + marker_point[1] * y_ratio - 12
        canvas.shapes.append(
            cv.Text(
                value=f"{marker_point[0]:.2f}",
                x=mx,
                y=origin_y + 12,
                alignment=ft.alignment.Alignment.CENTER_LEFT,
                style=ft.TextStyle(size=13, color=ft.Colors.TERTIARY),
            )
        )
        canvas.shapes.append(
            cv.Text(
                value=f"{marker_point[1]:.2f}",
                x=mx,
                y=my,
                alignment=ft.alignment.Alignment.CENTER_LEFT,
                style=ft.TextStyle(size=13, color=ft.Colors.TERTIARY),
            )
        )
