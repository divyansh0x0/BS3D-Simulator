from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Import Beam classes and types
from core.Beam import Beam, RectangularBeam, CircularBeam, IBeam, BeamType, LoadType, LoadFunction

class StateManager:
    beam_type: Optional[BeamType]
    beam_length: float
    dimensions: Dict[str, float]
    supports: List[Dict[str, Any]]
    loads: List[Dict[str, Any]]
    
    reaction_left: float
    reaction_right: float
    sfd_points: List[Tuple[float, float]]
    bmd_points: List[Tuple[float, float]]

    def __init__(self) -> None:
        self.beam_type = None
        self.beam_length = 10.0
        self.dimensions = {}
        self.supports = [
            {"type": "Pin", "position": 0.0},
            {"type": "Roller", "position": 10.0},
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
        if self.beam_type == "Rectangular":
            h = self.dimensions.get("Height (mm)", 100.0) / 1000.0
            w = self.dimensions.get("Width (mm)", 100.0) / 1000.0
            beam = RectangularBeam(height=h, width=w, length=self.beam_length)
        elif self.beam_type == "Circular":
            d = self.dimensions.get("Diameter (mm)", 100.0) / 1000.0
            beam = CircularBeam(diameter=d, length=self.beam_length)
        elif self.beam_type == "I-Beam":
            hw = self.dimensions.get("Height (mm)", 100.0) / 1000.0
            fw = self.dimensions.get("Flange Width (mm)", 100.0) / 1000.0
            ft_thick = self.dimensions.get("Flange Thickness (mm)", 10.0) / 1000.0
            wt = self.dimensions.get("Web Thickness (mm)", 10.0) / 1000.0
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
            if ld["type"] == "Point":
                mag = ld.get("Load Magnitude (kN)", 0.0)
                pos = ld.get("Load Position (m)", 0.0)
                beam.set_point_load(load=mag, x=pos)
            elif ld["type"] == "UDL":
                mag = ld.get("Load Intensity (kN/m)", 0.0)
                start = ld.get("Start Position (m)", 0.0)
                end = ld.get("End Position (m)", 0.0)
                beam.set_load_function(start, end, lambda x, m=mag: m)
            elif ld["type"] == "UVL":
                start_mag = ld.get("Start Intensity (kN/m)", 0.0)
                end_mag = ld.get("End Intensity (kN/m)", 0.0)
                start = ld.get("Start Position (m)", 0.0)
                end = ld.get("End Position (m)", 0.0)
                
                def uvl_func(x: float, s: float=start, e: float=end, sm: float=start_mag, em: float=end_mag) -> float:
                    if e == s:
                        return sm
                    return sm + (em - sm) * (x - s) / (e - s)
                
                beam.set_load_function(start, end, uvl_func)

        for sup in self.supports:
            if sup["type"] == "Pin":
                beam.reaction_left.position = sup["position"]
            elif sup["type"] == "Roller":
                beam.reaction_right.position = sup["position"]

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
