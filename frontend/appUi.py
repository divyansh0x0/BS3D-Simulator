import asyncio
import flet as ft
import flet.canvas as cv


def main(page: ft.Page):
    page.title = "BS3D - Beam Structural Analysis"
    page.padding = 0
    page.bgcolor = "#0B0F19"

    # --- APPLICATION STATE ---
    state = {
        "beam_type": None,
        "beam_length": 10.0,
        "dimensions": {},
        "supports": [
            {"type": "Pin", "position": 0.0},
            {"type": "Roller", "position": 10.0},
        ],
        "loads": [],  # Confirmed load inputs list
    }

    dimension_content = ft.Column(spacing=10)
    dimensions_container = ft.Container(
        content=dimension_content, opacity=0, animate_opacity=150
    )

    load_content = ft.Column(spacing=10)

    # Load panel container overlaid at the top-right
    load_container = ft.Container(
        content=load_content,
        border=ft.Border.all(1, "#334155"),
        border_radius=10,
        padding=12,
        width=230,
        bgcolor="#1E293B",
        opacity=0,
        animate_opacity=150,
        top=20,
        right=20,
    )

    load_list_view = ft.Column(spacing=5)

    # Main vector drawing canvas
    canvas_shape_group = cv.Canvas(
        shapes=[],
        expand=True,
    )

    def redraw_canvas():
        canvas_shape_group.shapes.clear()

        c_width = 750

        # --- 1. ADJUST X-POSITION & LENGTH ---
        start_x = 30  # <--- SHIFT X-POSITION: Increase to move beam RIGHT, decrease to move LEFT
        draw_width = 400  # <--- BEAM VISUAL LENGTH: Set exact pixel width of the beam on screen

        beam_len = state["beam_length"] if state["beam_length"] > 0 else 1.0
        scale_x = draw_width / beam_len

        # --- 2. Y-COORDINATES & GAPS ---
        y_beam = 50  # Top section: Physical Beam
        y_sfd = 240  # Middle section: SFD baseline
        y_bmd = 480  # Bottom section: BMD baseline

        # --- DRAW BEAM USING START_X ---
        canvas_shape_group.shapes.append(
            cv.Line(
                start_x,  # Start point X
                y_beam,
                start_x + draw_width,  # End point X
                y_beam,
                paint=ft.Paint(stroke_width=6, color="#38BDF8"),
            )
        )

        # --- DRAW SUPPORTS USING START_X ---
        for sup in state["supports"]:
            sx = start_x + (sup["position"] * scale_x)
            canvas_shape_group.shapes.append(
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
        for ld in state["loads"]:
            if ld["type"] == "POINT LOAD":
                raw_pos = ld.get("Load Position (m)", 0)
                try:
                    pos = float(raw_pos) if raw_pos != "" else 0.0
                except (ValueError, TypeError):
                    pos = 0.0

                px = start_x + (pos * scale_x)
                canvas_shape_group.shapes.append(
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
        canvas_shape_group.shapes.append(
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
        canvas_shape_group.shapes.append(
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

        canvas_shape_group.update()

        canvas_shape_group.update()

    # --- EVENT HANDLERS ---
    async def change_dimensions(e):
        selected_beam = e.control.value
        state["beam_type"] = selected_beam

        dimensions_container.opacity = 0
        dimensions_container.update()
        await asyncio.sleep(0.15)
        dimension_content.controls.clear()

        if selected_beam == "I-Beam":
            dimension_content.controls.extend(
                [
                    ft.Text("I-Beam Dimensions", size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                    ft.TextField(label="Height (mm)", width=210, height=40, color="#F8FAFC"),
                    ft.TextField(label="Flange Width (mm)", width=210, height=40, color="#F8FAFC"),
                    ft.TextField(label="Flange Thickness (mm)", width=210, height=40, color="#F8FAFC"),
                    ft.TextField(label="Web Thickness (mm)", width=210, height=40, color="#F8FAFC"),
                ]
            )
        elif selected_beam == "Rectangular":
            dimension_content.controls.extend(
                [
                    ft.Text("Rectangular Beam Dimensions", size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                    ft.TextField(label="Width (mm)", width=210, height=40, color="#F8FAFC"),
                    ft.TextField(label="Height (mm)", width=210, height=40, color="#F8FAFC"),
                ]
            )
        elif selected_beam == "Circular":
            dimension_content.controls.extend(
                [
                    ft.Text("Circular Beam Dimensions", size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                    ft.TextField(label="Diameter (mm)", width=210, height=40, color="#F8FAFC"),
                ]
            )
        dimensions_container.opacity = 1
        dimensions_container.update()

    async def update_beam_length(e):
        val = e.control.value.strip() if e.control.value else ""
        try:
            if val:
                state["beam_length"] = float(val)
                # Update roller support position
                for sup in state["supports"]:
                    if sup["type"] == "Roller":
                        sup["position"] = state["beam_length"]
                redraw_canvas()
        except ValueError:
            pass

    async def confirm_load(e):
        load_data = {"type": load_type.value}
        for control in load_content.controls:
            if isinstance(control, ft.TextField):
                val = control.value.strip() if control.value else ""
                try:
                    load_data[control.label] = float(val) if val else 0.0
                except ValueError:
                    load_data[control.label] = 0.0

        state["loads"].append(load_data)
        refresh_load_list()
        redraw_canvas()

        # Visual feedback flash
        load_container.border = ft.Border.all(2, "#22C55E")
        load_container.update()
        await asyncio.sleep(0.15)

        load_container.opacity = 0
        load_container.border = ft.Border.all(1, "#334155")
        load_container.update()

    def remove_load(index):
        state["loads"].pop(index)
        refresh_load_list()
        redraw_canvas()

    def refresh_load_list():
        load_list_view.controls.clear()
        for idx, ld in enumerate(state["loads"]):
            load_list_view.controls.append(
                ft.Container(
                    bgcolor="#1E293B",
                    padding=8,
                    border_radius=6,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(f"{ld['type']}", size=12, color="#F8FAFC"),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINED,
                                icon_size=16,
                                icon_color="#EF4444",
                                on_click=lambda e, i=idx: remove_load(i),
                            ),
                        ],
                    ),
                )
            )
        load_list_view.update()

    async def change_load(e):
        selected_load = e.control.value
        load_container.opacity = 0
        load_container.update()
        await asyncio.sleep(0.15)
        load_content.controls.clear()

        if selected_load == "POINT LOAD":
            load_content.controls.extend(
                [
                    ft.Text("Point Load Parameters", size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                    ft.TextField(label="Load Magnitude (kN)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="Load Position (m)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                ]
            )
        elif selected_load == "UDL":
            load_content.controls.extend(
                [
                    ft.Text("UDL Parameters", size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                    ft.TextField(label="Load Intensity (kN/m)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="Start Position (m)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="End Position (m)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                ]
            )
        elif selected_load == "UVL":
            load_content.controls.extend(
                [
                    ft.Text("UVL Parameters", size=14, weight=ft.FontWeight.BOLD, color="#F8FAFC"),
                    ft.TextField(label="Start Intensity (kN/m)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="End Intensity (kN/m)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="Start Position (m)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                    ft.TextField(label="End Position (m)", width=200, height=40, color="#F8FAFC", keyboard_type=ft.KeyboardType.NUMBER),
                ]
            )

        if selected_load:
            load_content.controls.append(
                ft.ElevatedButton(
                    "Confirm Load",
                    on_click=confirm_load,
                    bgcolor="#2563EB",
                    color="#FFFFFF",
                    width=200,
                )
            )

        load_container.opacity = 1
        load_container.update()

    # --- LEFT CONTROLS ---
    beam_type = ft.Dropdown(
        label="Select Beam Type",
        width=210,
        options=[
            ft.dropdown.Option("Rectangular"),
            ft.dropdown.Option("Circular"),
            ft.dropdown.Option("I-Beam"),
        ],
        bgcolor="#0F172A",
        border_color="#334155",
        focused_border_color="#2563EB",
        border_radius=8,
        text_style=ft.TextStyle(color="#F8FAFC"),
        on_select=change_dimensions,
    )

    load_type = ft.Dropdown(
        label="Select Load Type",
        width=210,
        options=[
            ft.dropdown.Option("POINT LOAD"),
            ft.dropdown.Option("UDL"),
            ft.dropdown.Option("UVL"),
        ],
        bgcolor="#0F172A",
        border_color="#334155",
        focused_border_color="#2563EB",
        border_radius=8,
        text_style=ft.TextStyle(color="#F8FAFC"),
        on_select=change_load,
    )

    beam_length_input = ft.TextField(
        label="Beam Length (m)",
        value="10.0",
        width=210,
        height=40,
        color="#F8FAFC",
        on_change=update_beam_length,
    )

    solve_button = ft.ElevatedButton(
        "Calculate SFD & BMD",
        on_click=lambda e: print("STATE DUMP FOR BACKEND:", state),
        bgcolor="#22C55E",
        color="#FFFFFF",
        width=210,
        height=45,
    )

    left_panel = ft.Container(
        width=260,
        bgcolor="#0F172A",
        padding=15,
        content=ft.Column(
            controls=[
                ft.Text("Beam Controls", color="#F8FAFC", size=20, weight=ft.FontWeight.BOLD),
                beam_length_input,
                ft.Text("Beam Section", color="#94A3B8", size=12),
                beam_type,
                dimensions_container,
                ft.Text("Load Setup", color="#94A3B8", size=12),
                load_type,
                ft.Text("Active Loads", color="#94A3B8", size=12),
                load_list_view,
                solve_button,
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    # Main viewport combining Canvas layer and floating Load inputs
    center_viewport = ft.Stack(
        controls=[
            ft.Container(
                expand=True,
                padding=20,
                content=canvas_shape_group,
            ),
            load_container,
        ],
        expand=True,
    )

    page.add(
        ft.Row(
            controls=[
                left_panel,
                center_viewport,
            ],
            expand=True,
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    )

    redraw_canvas()


ft.app(target=main)