from dataclasses import dataclass
from typing import Literal, Callable, TypeAlias, override
import numpy as np

# 1. Custom Type Aliases
BeamType = Literal["Rectangular", "Circular", "I-Beam"]
LoadType = Literal["Point", "UDL", "UVL"]

ArrayPair: TypeAlias = tuple[np.ndarray, np.ndarray]


@dataclass
class Load:
    type: LoadType
    magnitude: float| int
    position: float | int

PhysicsSolver = Callable[[list[Load]], ArrayPair]
LoadFunction = Callable[[float], float]