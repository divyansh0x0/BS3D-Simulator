from dataclasses import dataclass
from typing import Callable, Literal

BeamType = Literal["Rectangular", "Circular", "IBeam"]
LoadType = Literal["Point", "UDL", "UVL"]

LoadFunction = Callable[[float], float]


@dataclass(slots=True)
class Point2D:
    x: float
    y: float
