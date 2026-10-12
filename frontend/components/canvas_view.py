from typing import Tuple

import flet as ft
import flet.canvas as cv

from frontend.components.canvas.beam_renderer import BeamRenderer
from frontend.components.canvas.cross_section_renderer import CrossSectionRenderer
from frontend.components.canvas.drawing_utils import min_max_x, min_max_y
from frontend.components.canvas.graph_renderer import GraphRenderer
from frontend.components.canvas.grid_renderer import GridRenderer
from frontend.components.canvas.load_renderer import LoadRenderer
from frontend.StateManager import StateManager

__all__ = ["CanvasView", "min_max_x", "min_max_y"]


class CanvasView(ft.Container):
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

        self.canvas_container = ft.Container(
            content=self.canvas_shape_group,
            expand=True,
            on_size_change=self.update_realtime_size,
        )

        self.spacing = 40
        self.content = ft.Column(
            controls=[
                self.canvas_container,
            ],
            expand=True,
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
        self.redraw()

    def get_rendered_beam_length(self) -> float:
        return self.realtime_width * self.section_width_fraction - self.spacing * 2

    def get_beam_height(self) -> float:
        return 10.0

    def redraw(self) -> None:
        self.canvas_shape_group.shapes.clear()

        box_paint = ft.Paint(stroke_width=2, color=ft.Colors.OUTLINE, style=ft.PaintingStyle.STROKE)
        axis_paint = ft.Paint(stroke_width=2, color=ft.Colors.PRIMARY, style=ft.PaintingStyle.STROKE)
        cross_section_paint = ft.Paint(stroke_width=2, color=ft.Colors.SECONDARY, style=ft.PaintingStyle.STROKE)
        graph_paint = ft.Paint(color=ft.Colors.SECONDARY_CONTAINER, style=ft.PaintingStyle.FILL)

        # 1. Render physical beam
        BeamRenderer.render(
            canvas=self.canvas_shape_group,
            spacing=self.spacing,
            rendered_beam_length=self.get_rendered_beam_length(),
            beam_height=self.get_beam_height(),
            realtime_height=self.realtime_height,
            section_height_fraction=self.section_height_fraction,
            graph_paint=graph_paint,
        )

        # 2. Render loads & reactions
        LoadRenderer.render(
            canvas=self.canvas_shape_group,
            state=self.state,
            spacing=self.spacing,
            rendered_beam_length=self.get_rendered_beam_length(),
            beam_h=self.get_beam_height(),
            realtime_height=self.realtime_height,
            section_height_fraction=self.section_height_fraction,
        )

        # 3. Render beam cross-section profile
        CrossSectionRenderer.render(
            canvas=self.canvas_shape_group,
            state=self.state,
            realtime_width=self.realtime_width,
            realtime_height=self.realtime_height,
            section_width_fraction=self.section_width_fraction,
            section_height_fraction=self.section_height_fraction,
            spacing=self.spacing,
            cross_section_paint=cross_section_paint,
        )

        # 4. Render SFD and BMD graphs
        w = self.realtime_width * self.section_width_fraction - self.spacing * 2
        num_points = max(10, int(w))
        iterators = (self.state.generate_sfd_points(num_points), self.state.generate_bmd_points(num_points))
        bm_y = self.state.get_bending_moment(self.state.cross_section_x)
        sf_y = self.state.get_shear_force(self.state.cross_section_x)
        sfd_bmd_marked_points = ((self.state.cross_section_x, sf_y), (self.state.cross_section_x, bm_y))

        for i in range(1, 3):
            x = self.spacing
            h = self.realtime_height * self.section_height_fraction - self.spacing * 2
            y = self.realtime_height * self.section_height_fraction * i + self.spacing
            w = self.realtime_width * self.section_width_fraction - self.spacing * 2

            y_lbl = "kN" if i == 1 else "kN·m"
            GraphRenderer.render_axes(
                canvas=self.canvas_shape_group,
                x=x,
                y=y,
                graph_width=w,
                graph_height=h,
                paint=axis_paint,
                graph_paint=graph_paint,
                beam_length=self.state.beam_length,
                spacing=self.spacing,
                has_negatives_y=True,
                has_negative_x=False,
                point_iterator=iterators[i - 1],
                marker_point=sfd_bmd_marked_points[i - 1],
                x_label="m",
                y_label=y_lbl,
                graph_name="SFD" if i == 1 else "BMD",
            )

        # 5. Render Shear Stress and Bending Stress graphs
        stress_iterators = (
            self.state.generate_shear_stress_points(num_points),
            self.state.generate_bending_stress_points(num_points),
        )
        y_mm = self.state.cross_section_y_meters * 1000.0
        bending_stress_and_shear_stress_marked_points = (
            (self.state.get_shear_stress(self.state.cross_section_y_meters), y_mm),
            (self.state.get_bending_stress(self.state.cross_section_y_meters), y_mm),
        )

        for i in range(1, 3):
            x = self.realtime_width * self.section_width_fraction + self.spacing
            h = self.realtime_height * self.section_height_fraction - self.spacing * 2
            y = self.realtime_height * self.section_height_fraction * i + self.spacing
            w = self.realtime_width * self.section_width_fraction - self.spacing * 2

            y_lbl = "mm"
            x_lbl = "MPa"
            fixed_max = self.state.max_shear_stress if i == 1 else self.state.max_bending_stress
            GraphRenderer.render_axes(
                canvas=self.canvas_shape_group,
                x=x,
                y=y,
                graph_width=w,
                graph_height=h,
                paint=axis_paint,
                graph_paint=graph_paint,
                beam_length=self.state.beam_length,
                spacing=self.spacing,
                has_negatives_y=True,
                has_negative_x=True,
                point_iterator=stress_iterators[i - 1],
                marker_point=bending_stress_and_shear_stress_marked_points[i - 1],
                x_label=x_lbl,
                y_label=y_lbl,
                graph_name="Shear Stress" if i == 1 else "Bending Stress",
                fixed_max_x=fixed_max,
            )

        # 6. Render Slider cross-section indicator line
        GridRenderer.render_slider_indicator(
            canvas=self.canvas_shape_group,
            cross_section_x=self.state.cross_section_x,
            beam_length=self.state.beam_length,
            spacing=self.spacing,
            realtime_width=self.realtime_width,
            realtime_height=self.realtime_height,
            section_width_fraction=self.section_width_fraction,
        )

        # 7. Render section border separators
        GridRenderer.render_section_borders(
            canvas=self.canvas_shape_group,
            realtime_width=self.realtime_width,
            realtime_height=self.realtime_height,
            section_width_fraction=self.section_width_fraction,
            section_height_fraction=self.section_height_fraction,
            box_paint=box_paint,
        )

        self.canvas_shape_group.update()
