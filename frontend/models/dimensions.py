from dataclasses import dataclass


@dataclass
class BeamDimensions:
    pass


@dataclass
class RectangularDimensions(BeamDimensions):
    width_mm: float = 100.0
    height_mm: float = 100.0


@dataclass
class CircularDimensions(BeamDimensions):
    diameter_mm: float = 100.0


@dataclass
class IBeamDimensions(BeamDimensions):
    height_mm: float = 100.0
    flange_width_mm: float = 100.0
    flange_thickness_mm: float = 10.0
    web_thickness_mm: float = 10.0
