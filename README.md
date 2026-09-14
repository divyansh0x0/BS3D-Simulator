# BS3D-Simulator

A simply supported beam simulator that computes and visualises the Shear Force Diagram (SFD), Bending Moment Diagram (BMD), shear stress distribution, and bending stress distribution across the cross-section for three beam profiles: Rectangular, Circular, and I-Beam.

## Preview

<img width="1920" height="984" alt="image" src="https://github.com/user-attachments/assets/44c27203-97cc-4f77-8605-73f78a7bb970" />
<img width="1920" height="984" alt="image" src="https://github.com/user-attachments/assets/400441fe-6bf2-432b-ac22-bd8dfe31ac10" />

----
## Architecture

The project is split into two decoupled modules. No module imports from another except where the interface is explicit.

### Core

Contains the beam model and the physics solver. Defines `Beam`, `RectangularBeam`, `CircularBeam`, and `IBeam` classes. Each class implements:

- `get_second_moment_of_area()` — second moment of area $I$ about the neutral axis
- `get_first_moment_of_area(y)` — first moment of area $Q$ at depth $y$
- `get_shear_force(x)` — shear force $V$ at position $x$ along the span
- `get_bending_moment(x)` — bending moment $M$ at position $x$

Distributed loads (UDL and UVL) are integrated numerically using Simpson's 3/8 rule. The beam is assumed to be simply supported and the reactions are resolved from moment equilibrium.

### Frontend

Built with [Flet](https://flet.dev/). All diagrams (SFD, BMD, stress distributions, beam cross-section) are rendered using Flet's custom canvas drawing API. The `StateManager` class holds all input state (beam type, dimensions, supports, applied loads) and exposes generator methods that yield point pairs consumed by the canvas layer. Stress distributions are evaluated at a user-selected cross-section position.

## Supported Load Types

| Load Type | Description |
|---|---|
| Point Load | Concentrated force at a single position along the span |
| UDL | Uniformly Distributed Load — constant intensity over a span segment |
| UVL | Uniformly Varying Load — linearly varying intensity over a span segment |

## Computed Outputs

- Shear Force Diagram (SFD) along the full span
- Bending Moment Diagram (BMD) along the full span
- Bending stress $\sigma = My/I$ distribution across the cross-section height at a selected $x$
- Shear stress $\tau = VQ/Ib$ distribution across the cross-section height at a selected $x$

## Running

```bash
uv run main.py
```

## Building

Flutter must be installed and available on `PATH` before running any build command.

```bash
# Windows
flet build windows

# Linux
flet build linux

# macOS
flet build macos
```

## Dependencies
- [Flet](https://flet.dev/) — UI framework and canvas rendering

