from typing import Tuple

import flet as ft
import flet.canvas as cv

from frontend.components.canvas.beam_renderer import BeamRenderer
from frontend.components.canvas.cross_section_renderer import (
    CrossSectionGeometryMetrics,
    CrossSectionRenderer,
)
from frontend.components.canvas.drawing_utils import min_max_x, min_max_y
from frontend.components.canvas.graph_renderer import GraphCoordinateSystem, GraphRenderer
from frontend.components.canvas.grid_renderer import GridRenderer
from frontend.components.canvas.load_renderer import LoadRenderer
from frontend.components.canvas.palette import CanvasPaintPalette
from frontend.StateManager import StateManager

__all__ = ["CanvasView", "min_max_x", "min_max_y"]


class CanvasView(ft.Container):
    state: StateManager
    palette: CanvasPaintPalette
    static_canvas: cv.Canvas
    dynamic_canvas: cv.Canvas
    canvas_shape_group: cv.Canvas

    def __init__(self, state: StateManager) -> None:
        super().__init__()
        self.state = state
        self.expand = True
        self.palette = CanvasPaintPalette.create_default()

        self.static_canvas = cv.Canvas(
            shapes=[],
            expand=True,
        )
        self.dynamic_canvas = cv.Canvas(
            shapes=[],
            expand=True,
        )
        # Keep canvas_shape_group reference for backward compatibility
        self.canvas_shape_group = self.dynamic_canvas

        self.canvas_stack = ft.Stack(
            controls=[
                self.static_canvas,
                self.dynamic_canvas,
            ],
            expand=True,
        )

        self.canvas_container = ft.Container(
            content=self.canvas_stack,
            expand=True,
            on_size_change=self.update_realtime_size,
        )

        self.spacing = 40.0
        self.content = ft.Column(
            controls=[
                self.canvas_container,
            ],
            expand=True,
        )
        self.section_width_fraction = 0.5
        self.section_height_fraction = 1.0 / 3.0
        self.right_section_height_fraction = 0.5

        self.realtime_width = 0.0
        self.realtime_height = 0.0

        self._cross_section_metrics: CrossSectionGeometryMetrics | None = None
        self._sfd_coord_sys: GraphCoordinateSystem | None = None
        self._bmd_coord_sys: GraphCoordinateSystem | None = None
        self._shear_stress_coord_sys: GraphCoordinateSystem | None = None
        self._bending_stress_coord_sys: GraphCoordinateSystem | None = None

    def update_realtime_size(self, e: ft.LayoutSizeChangeEvent) -> None:
        self.realtime_width = float(e.width)
        self.realtime_height = float(e.height)
        self.redraw()

    def get_rendered_beam_length(self) -> float:
        return self.realtime_width * self.section_width_fraction - self.spacing * 2.0

    def get_beam_height(self) -> float:
        return 10.0

    def redraw_static(self) -> None:
        """Render static beam geometry, supports, loads, section borders, and static graphs."""
        if self.realtime_width <= 0 or self.realtime_height <= 0:
            return

        self.static_canvas.shapes.clear()

        # 1. Render physical beam
        BeamRenderer.render(
            canvas=self.static_canvas,
            spacing=self.spacing,
            rendered_beam_length=self.get_rendered_beam_length(),
            beam_height=self.get_beam_height(),
            realtime_height=self.realtime_height,
            section_height_fraction=self.section_height_fraction,
            graph_paint=self.palette.graph_fill_paint,
        )

        # 2. Render loads & reactions
        LoadRenderer.render(
            canvas=self.static_canvas,
            state=self.state,
            spacing=self.spacing,
            rendered_beam_length=self.get_rendered_beam_length(),
            beam_h=self.get_beam_height(),
            realtime_height=self.realtime_height,
            section_height_fraction=self.section_height_fraction,
        )

        # 3. Render static beam cross-section profile
        self._cross_section_metrics = CrossSectionRenderer.render_static_profile(
            canvas=self.static_canvas,
            state=self.state,
            realtime_width=self.realtime_width,
            realtime_height=self.realtime_height,
            section_width_fraction=self.section_width_fraction,
            section_height_fraction=self.section_height_fraction,
            spacing=self.spacing,
            cross_section_paint=self.palette.cross_section_paint,
            neutral_axis_paint=self.palette.neutral_axis_paint,
        )

        # 4. Render SFD and BMD static graphs
        w = self.realtime_width * self.section_width_fraction - self.spacing * 2.0
        num_points = max(10, int(w))
        sfd_points = self.state.generate_sfd_points(num_points)
        bmd_points = self.state.generate_bmd_points(num_points)

        h = self.realtime_height * self.section_height_fraction - self.spacing * 2.0
        y_sfd = self.realtime_height * self.section_height_fraction * 1.0 + self.spacing
        y_bmd = self.realtime_height * self.section_height_fraction * 2.0 + self.spacing

        self._sfd_coord_sys = GraphRenderer.render_static_graph(
            canvas=self.static_canvas,
            x=self.spacing,
            y=y_sfd,
            graph_width=w,
            graph_height=h,
            paint=self.palette.axis_paint,
            graph_paint=self.palette.graph_fill_paint,
            graph_stroke_paint=self.palette.graph_stroke_paint,
            beam_length=self.state.beam_length,
            spacing=self.spacing,
            has_negatives_y=True,
            has_negative_x=False,
            point_iterator=sfd_points,
            x_label="m",
            y_label="kN",
            graph_name="SFD",
        )

        self._bmd_coord_sys = GraphRenderer.render_static_graph(
            canvas=self.static_canvas,
            x=self.spacing,
            y=y_bmd,
            graph_width=w,
            graph_height=h,
            paint=self.palette.axis_paint,
            graph_paint=self.palette.graph_fill_paint,
            graph_stroke_paint=self.palette.graph_stroke_paint,
            beam_length=self.state.beam_length,
            spacing=self.spacing,
            has_negatives_y=True,
            has_negative_x=False,
            point_iterator=bmd_points,
            x_label="m",
            y_label="kN·m",
            graph_name="BMD",
        )

        # 5. Render Shear Stress and Bending Stress static axes
        x_stress = self.realtime_width * self.section_width_fraction + self.spacing
        beam_half_h_mm = (self.state._beam.get_height() * 1000.0) / 2.0 if self.state._beam is not None else 50.0

        self._shear_stress_coord_sys = GraphRenderer.render_static_axes_only(
            canvas=self.static_canvas,
            x=x_stress,
            y=y_sfd,
            graph_width=w,
            graph_height=h,
            paint=self.palette.axis_paint,
            beam_length=self.state.beam_length,
            spacing=self.spacing,
            has_negatives_y=True,
            has_negative_x=True,
            x_label="MPa",
            y_label="mm",
            graph_name="Shear Stress",
            fixed_max_x=self.state.max_shear_stress,
            fixed_max_y=beam_half_h_mm,
        )

        self._bending_stress_coord_sys = GraphRenderer.render_static_axes_only(
            canvas=self.static_canvas,
            x=x_stress,
            y=y_bmd,
            graph_width=w,
            graph_height=h,
            paint=self.palette.axis_paint,
            beam_length=self.state.beam_length,
            spacing=self.spacing,
            has_negatives_y=True,
            has_negative_x=True,
            x_label="MPa",
            y_label="mm",
            graph_name="Bending Stress",
            fixed_max_x=self.state.max_bending_stress,
            fixed_max_y=beam_half_h_mm,
        )

        # 6. Render section border separators
        GridRenderer.render_section_borders(
            canvas=self.static_canvas,
            realtime_width=self.realtime_width,
            realtime_height=self.realtime_height,
            section_width_fraction=self.section_width_fraction,
            section_height_fraction=self.section_height_fraction,
            box_paint=self.palette.box_paint,
        )

        self.static_canvas.update()

    def redraw_dynamic(self) -> None:
        """Fast dynamic redraw of indicators, sliders, markers, and dynamic stress curves."""
        if self.realtime_width <= 0 or self.realtime_height <= 0:
            return

        if (
            self._sfd_coord_sys is None
            or self._bmd_coord_sys is None
            or self._shear_stress_coord_sys is None
            or self._bending_stress_coord_sys is None
            or self._cross_section_metrics is None
        ):
            self.redraw()
            return

        self.dynamic_canvas.shapes.clear()

        # 1. Dynamic Cross-Section depth indicator
        CrossSectionRenderer.render_dynamic_depth_indicator(
            canvas=self.dynamic_canvas,
            state=self.state,
            metrics=self._cross_section_metrics,
            depth_line_paint=self.palette.depth_line_paint,
        )

        # 2. SFD dynamic marker
        sf_y = self.state.get_shear_force(self.state.cross_section_x)
        GraphRenderer.render_dynamic_marker(
            canvas=self.dynamic_canvas,
            coord_sys=self._sfd_coord_sys,
            marker_point=(self.state.cross_section_x, sf_y),
            marker_paint=self.palette.marker_paint,
        )

        # 3. BMD dynamic marker
        bm_y = self.state.get_bending_moment(self.state.cross_section_x)
        GraphRenderer.render_dynamic_marker(
            canvas=self.dynamic_canvas,
            coord_sys=self._bmd_coord_sys,
            marker_point=(self.state.cross_section_x, bm_y),
            marker_paint=self.palette.marker_paint,
        )

        # 4. Shear Stress dynamic curve and marker
        w = self.realtime_width * self.section_width_fraction - self.spacing * 2.0
        num_points = max(10, int(w))
        y_mm = self.state.cross_section_y_meters * 1000.0

        shear_points = self.state.generate_shear_stress_points(num_points)
        shear_stress_at_y = self.state.get_shear_stress(self.state.cross_section_y_meters)
        GraphRenderer.render_dynamic_curve_and_marker(
            canvas=self.dynamic_canvas,
            coord_sys=self._shear_stress_coord_sys,
            point_iterator=shear_points,
            marker_point=(shear_stress_at_y, y_mm),
            graph_fill_paint=self.palette.graph_fill_paint,
            graph_stroke_paint=self.palette.graph_stroke_paint,
            marker_paint=self.palette.marker_paint,
        )

        # 5. Bending Stress dynamic curve and marker
        bending_points = self.state.generate_bending_stress_points(num_points)
        bending_stress_at_y = self.state.get_bending_stress(self.state.cross_section_y_meters)
        GraphRenderer.render_dynamic_curve_and_marker(
            canvas=self.dynamic_canvas,
            coord_sys=self._bending_stress_coord_sys,
            point_iterator=bending_points,
            marker_point=(bending_stress_at_y, y_mm),
            graph_fill_paint=self.palette.graph_fill_paint,
            graph_stroke_paint=self.palette.graph_stroke_paint,
            marker_paint=self.palette.marker_paint,
        )

        # 6. Slider indicator line across beam & graphs
        GridRenderer.render_slider_indicator(
            canvas=self.dynamic_canvas,
            cross_section_x=self.state.cross_section_x,
            beam_length=self.state.beam_length,
            spacing=self.spacing,
            realtime_width=self.realtime_width,
            realtime_height=self.realtime_height,
            section_width_fraction=self.section_width_fraction,
            slider_paint=self.palette.slider_line_paint,
        )

        self.dynamic_canvas.update()

    def redraw(self) -> None:
        """Full redraw of both static background layer and dynamic foreground layer."""
        self.redraw_static()
        self.redraw_dynamic()
