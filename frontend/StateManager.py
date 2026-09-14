from typing import Any, List, Optional, Tuple, Union
from dataclasses import dataclass
import numpy as np

from core.Beam import Beam, RectangularBeam, CircularBeam, IBeam, BeamType, LoadType, LoadFunction

# --- Dimension State Classes ---
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

# --- Support State Classes ---
@dataclass
class SupportState:
    support_type: str  # e.g., "Pin", "Roller"
    position: float

# --- Load State Classes ---
@dataclass
class LoadState:
    load_type: LoadType

@dataclass
class PointLoadState(LoadState):
    magnitude_kn: float = 0.0
    position_m: float = 0.0
    
    def __init__(self, magnitude_kn: float = 0.0, position_m: float = 0.0):
        super().__init__("Point")
        self.magnitude_kn = magnitude_kn
        self.position_m = position_m

@dataclass
class UDLLoadState(LoadState):
    intensity_kn_m: float = 0.0
    start_position_m: float = 0.0
    end_position_m: float = 0.0

    def __init__(self, intensity_kn_m: float = 0.0, start_position_m: float = 0.0, end_position_m: float = 0.0):
        super().__init__("UDL")
        self.intensity_kn_m = intensity_kn_m
        self.start_position_m = start_position_m
        self.end_position_m = end_position_m

@dataclass
class UVLLoadState(LoadState):
    start_intensity_kn_m: float = 0.0
    end_intensity_kn_m: float = 0.0
    start_position_m: float = 0.0
    end_position_m: float = 0.0

    def __init__(self, start_intensity_kn_m: float = 0.0, end_intensity_kn_m: float = 0.0, start_position_m: float = 0.0, end_position_m: float = 0.0):
        super().__init__("UVL")
        self.start_intensity_kn_m = start_intensity_kn_m
        self.end_intensity_kn_m = end_intensity_kn_m
        self.start_position_m = start_position_m
        self.end_position_m = end_position_m


class StateManager:
    beam_type: Optional[BeamType]
    beam_length: float
    beam_dimensions: Optional[BeamDimensions]
    supports: List[SupportState]
    loads: List[LoadState]
    
    reaction_left: float
    reaction_right: float
    sfd_points: List[Tuple[float, float]]
    bmd_points: List[Tuple[float, float]]

    def __init__(self) -> None:
        self.beam_type = None
        self.beam_length = 10.0
        self.beam_dimensions = None
        self.supports = [
            SupportState("Pin", 0.0),
            SupportState("Roller", 10.0),
        ]
        self.loads = []
        
        self.reaction_left = 0.0
        self.reaction_right = 0.0
        self.sfd_points = []
        self.bmd_points = []

    def solve(self) -> None:
        """
        Reads the UI state and interfaces with core.Beam.
        This decouples the frontend from Beam.py.
        """
        if not self.beam_type or self.beam_length <= 0:
            return

        beam: Beam
        if self.beam_type == "Rectangular" and isinstance(self.beam_dimensions, RectangularDimensions):
            h = self.beam_dimensions.height_mm / 1000.0
            w = self.beam_dimensions.width_mm / 1000.0
            beam = RectangularBeam(height=h, width=w, length=self.beam_length)
        elif self.beam_type == "Circular" and isinstance(self.beam_dimensions, CircularDimensions):
            d = self.beam_dimensions.diameter_mm / 1000.0
            beam = CircularBeam(diameter=d, length=self.beam_length)
        elif self.beam_type == "I-Beam" and isinstance(self.beam_dimensions, IBeamDimensions):
            hw = self.beam_dimensions.height_mm / 1000.0
            fw = self.beam_dimensions.flange_width_mm / 1000.0
            ft_thick = self.beam_dimensions.flange_thickness_mm / 1000.0
            wt = self.beam_dimensions.web_thickness_mm / 1000.0
            beam = IBeam(
                flange_width=fw, 
                flange_height=ft_thick, 
                web_width=wt, 
                web_height=max(0.001, hw - 2 * ft_thick), 
                length=self.beam_length
            )
        else:
            beam = Beam(self.beam_type, self.beam_length)

        for ld in self.loads:
            if isinstance(ld, PointLoadState):
                beam.set_point_load(load=ld.magnitude_kn, x=ld.position_m)
            elif isinstance(ld, UDLLoadState):
                mag = ld.intensity_kn_m
                start = ld.start_position_m
                end = ld.end_position_m
                beam.set_load_function(start, end, lambda x, m=mag: m)
            elif isinstance(ld, UVLLoadState):
                start_mag = ld.start_intensity_kn_m
                end_mag = ld.end_intensity_kn_m
                start = ld.start_position_m
                end = ld.end_position_m
                
                def uvl_func(x: float, s: float=start, e: float=end, sm: float=start_mag, em: float=end_mag) -> float:
                    if e == s:
                        return sm
                    return sm + (em - sm) * (x - s) / (e - s)
                
                beam.set_load_function(start, end, uvl_func)

        for sup in self.supports:
            if sup.support_type == "Pin":
                beam.reaction_left.position = sup.position
            elif sup.support_type == "Roller":
                beam.reaction_right.position = sup.position

        beam.update_loads()
        self.reaction_left = beam.reaction_left.magnitude
        self.reaction_right = beam.reaction_right.magnitude

        self.sfd_points = []
        self.bmd_points = []
        num_points = 100
        if self.beam_length > 0:
            dx = self.beam_length / num_points
            for i in range(num_points + 1):
                x = i * dx
                sf = beam.get_shear_force(x)
                bm = beam.get_bending_moment(x)
                self.sfd_points.append((x, sf))
                self.bmd_points.append((x, bm))
