from typing import Callable, Literal

BeamType = Literal["Rectangular", "Circular", "IBeam"]
LoadType = Literal["Point", "UDL", "UVL"]

LoadFunction = Callable[[float], float]
