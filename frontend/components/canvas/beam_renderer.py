import flet as ft
import flet.canvas as cv


class BeamRenderer:
    @staticmethod
    def render(
        canvas: cv.Canvas,
        spacing: float,
        rendered_beam_length: float,
        beam_height: float,
        realtime_height: float,
        section_height_fraction: float,
        graph_paint: ft.Paint,
    ) -> None:
        x1 = spacing
        w = rendered_beam_length
        h = beam_height
        y1 = (realtime_height * section_height_fraction - h) / 2

        canvas.shapes.append(
            cv.Rect(
                x=x1,
                y=y1,
                width=w,
                height=h,
                border_radius=5,
                paint=graph_paint,
            )
        )
        canvas.shapes.append(
            cv.Rect(
                x=x1,
                y=y1,
                width=w,
                height=h,
                border_radius=5,
                paint=ft.Paint(
                    stroke_width=2,
                    color=ft.Colors.PRIMARY,
                    style=ft.PaintingStyle.STROKE,
                ),
            )
        )
