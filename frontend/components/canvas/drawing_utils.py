import math
from typing import Tuple

import flet.canvas as cv


def min_max_y(points: list[Tuple[float, float]]) -> Tuple[float, float]:
    if not points:
        return 0.0, 0.0
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    return min_y, max_y


def min_max_x(points: list[Tuple[float, float]]) -> Tuple[float, float]:
    if not points:
        return 0.0, 0.0
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    return min_x, max_x


def min_max_xy(points: list[Tuple[float, float]]) -> Tuple[float, float, float, float]:
    """Single-pass min/max calculation for x and y points."""
    if not points:
        return 0.0, 0.0, 0.0, 0.0
    p0 = points[0]
    min_x = max_x = p0[0]
    min_y = max_y = p0[1]
    for px, py in points[1:]:
        if px < min_x:
            min_x = px
        elif px > max_x:
            max_x = px
        if py < min_y:
            min_y = py
        elif py > max_y:
            max_y = py
    return min_x, max_x, min_y, max_y


def draw_arrow(canvas: cv.Canvas, x: float, y: float, angle: float = 0, paint=None) -> None:
    h1 = 5
    w1 = 3 * h1
    x1 = x - w1
    y1 = y + h1 / 2
    x2 = x - w1
    y2 = y - h1 / 2

    def transform(__x: float, __y: float, __cx: float, __cy: float, angle: float):
        angle_rad = angle * math.pi / 180
        rx = (__x - __cx) * math.cos(angle_rad) - (__y - __cy) * math.sin(angle_rad) + __cx
        ry = (__x - __cx) * math.sin(angle_rad) + (__y - __cy) * math.cos(angle_rad) + __cy
        return rx, ry

    tx1, ty1 = transform(x1, y1, x, y, angle)
    tx2, ty2 = transform(x2, y2, x, y, angle)

    canvas.shapes.append(
        cv.Line(
            x1=tx1,
            x2=x,
            y1=ty1,
            y2=y,
            paint=paint,
        )
    )

    canvas.shapes.append(
        cv.Line(
            x1=tx2,
            x2=x,
            y1=ty2,
            y2=y,
            paint=paint,
        )
    )
