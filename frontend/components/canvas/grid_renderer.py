import flet as ft
import flet.canvas as cv


class GridRenderer:
    @staticmethod
    def render_section_borders(
        canvas: cv.Canvas,
        realtime_width: float,
        realtime_height: float,
        section_width_fraction: float,
        section_height_fraction: float,
        box_paint: ft.Paint,
    ) -> None:
        xb1 = 0
        wb1 = realtime_width * section_width_fraction
        yb1 = 0
        hb1 = realtime_height * section_height_fraction
        xb2 = xb1 + wb1
        yb2 = yb1 + hb1
        for i in range(1, 3):
            # draw BEAM, SFD, BMD separator
            canvas.shapes.append(
                cv.Line(
                    x1=xb1,
                    y1=yb2 * i,
                    x2=xb2,
                    y2=yb2 * i,
                    paint=box_paint,
                )
            )
            # draw separator for bending stress and shear stress
            canvas.shapes.append(
                cv.Line(
                    x1=xb2,
                    y1=yb2 * i,
                    x2=realtime_width,
                    y2=yb2 * i,
                    paint=box_paint,
                )
            )
        # draw separator between left and right section
        canvas.shapes.append(
            cv.Line(
                x1=xb2,
                y1=yb1,
                x2=xb2,
                y2=realtime_height,
                paint=box_paint,
            )
        )

    @staticmethod
    def render_slider_indicator(
        canvas: cv.Canvas,
        cross_section_x: float,
        beam_length: float,
        spacing: float,
        realtime_width: float,
        realtime_height: float,
        section_width_fraction: float,
        slider_paint: ft.Paint | None = None,
    ) -> None:
        if beam_length <= 0:
            return

        w_beam = realtime_width * section_width_fraction - spacing * 2
        slider_pixel_x = spacing + (cross_section_x / beam_length) * w_beam

        line_paint = slider_paint or ft.Paint(
            stroke_width=2,
            color=ft.Colors.PRIMARY,
            style=ft.PaintingStyle.STROKE,
        )
        slider_line_shape = cv.Line(
            x1=slider_pixel_x,
            y1=0,
            x2=slider_pixel_x,
            y2=realtime_height,
            paint=line_paint,
        )
        slider_text_shape = cv.Text(
            x=slider_pixel_x + 5,
            y=10,
            value=f"x = {cross_section_x:.2f}m",
            style=ft.TextStyle(
                color=ft.Colors.PRIMARY,
                size=12,
                weight=ft.FontWeight.BOLD,
            ),
        )

        canvas.shapes.append(slider_line_shape)
        canvas.shapes.append(slider_text_shape)
