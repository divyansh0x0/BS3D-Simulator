import flet as ft
import flet.canvas as cv
from frontend.StateManager import StateManager

class BeamCanvas(ft.Container):
    state: StateManager
    canvas_shape_group: cv.Canvas

    def __init__(self, state: StateManager) -> None:
        super().__init__()
        self.state = state
        self.expand = True
        self.padding = 20
        self.canvas_shape_group = cv.Canvas(
            shapes=[],
            expand=True,
        )
        self.content = self.canvas_shape_group

    def redraw(self) -> None:
        self.canvas_shape_group.shapes.clear()

        c_width: int = 750

        # --- 1. ADJUST X-POSITION & LENGTH ---
        start_x: float = 30.0  # <--- SHIFT X-POSITION: Increase to move beam RIGHT, decrease to move LEFT
        draw_width: float = 400.0  # <--- BEAM VISUAL LENGTH: Set exact pixel width of the beam on screen

        beam_len: float = self.state.beam_length if self.state.beam_length > 0 else 1.0
        scale_x: float = draw_width / beam_len

        # --- 2. Y-COORDINATES & GAPS ---
        y_beam: float = 50.0  # Top section: Physical Beam
        y_sfd: float = 240.0  # Middle section: SFD baseline
        y_bmd: float = 480.0  # Bottom section: BMD baseline

        # --- DRAW BEAM USING START_X ---
        self.canvas_shape_group.shapes.append(
            cv.Line(
                start_x,  # Start point X
                y_beam,
                start_x + draw_width,  # End point X
                y_beam,
                paint=ft.Paint(stroke_width=6, color="#38BDF8"),
            )
        )

        # --- DRAW SUPPORTS USING START_X ---
        for sup in self.state.supports:
            sx: float = start_x + (sup["position"] * scale_x)
            self.canvas_shape_group.shapes.append(
                cv.Path(
                    [
                        cv.Path.MoveTo(sx, y_beam),
                        cv.Path.LineTo(sx - 8, y_beam + 12),
                        cv.Path.LineTo(sx + 8, y_beam + 12),
                        cv.Path.Close(),
                    ],
                    paint=ft.Paint(color="#E2E8F0", style=ft.PaintingStyle.FILL),
                )
            )

        # --- DRAW POINT LOADS USING START_X ---
        for ld in self.state.loads:
            if ld["type"] == "Point":
                raw_pos = ld.get("Load Position (m)", 0.0)
                try:
                    pos: float = float(raw_pos) if raw_pos != "" else 0.0
                except (ValueError, TypeError):
                    pos = 0.0

                px: float = start_x + (pos * scale_x)
                self.canvas_shape_group.shapes.append(
                    cv.Line(
                        px,
                        y_beam - 30,
                        px,
                        y_beam - 2,
                        paint=ft.Paint(stroke_width=2.5, color="#EF4444"),
                    )
                )

        # --- DRAW GRAPH BASELINES USING START_X ---
        # SFD Reference Baseline
        self.canvas_shape_group.shapes.append(
            cv.Line(
                start_x,
                y_sfd,
                start_x + draw_width,
                y_sfd,
                paint=ft.Paint(
                    stroke_width=1, color="#64748B", stroke_dash_pattern=[4, 4]
                ),
            )
        )

        # BMD Reference Baseline
        self.canvas_shape_group.shapes.append(
            cv.Line(
                start_x,
                y_bmd,
                start_x + draw_width,
                y_bmd,
                paint=ft.Paint(
                    stroke_width=1, color="#64748B", stroke_dash_pattern=[4, 4]
                ),
            )
        )

        self.canvas_shape_group.update()
