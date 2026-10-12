from collections.abc import Iterator
from dataclasses import dataclass
from typing import List, Optional, Tuple

from core.Beam import Beam, CircularBeam, IBeam, RectangularBeam, BeamType
from frontend.models import (
    BeamDimensions,
    CircularDimensions,
    IBeamDimensions,
    LoadState,
    MaterialType,
    PointLoadState,
    RectangularDimensions,
    SupportState,
    UDLLoadState,
    UVLLoadState,
)


@dataclass(slots=True)
class AnalysisConfig:
    """Configurable numerical parameters minimizing hardcoded constants."""
    default_resolution: int = 200
    stress_resolution: int = 100
    scan_steps: int = 50
    min_stress_floor: float = 1e-9
    default_stress_scale: float = 1.0


@dataclass(slots=True)
class DiagramDataMap:
    """Class storing one-time processed SFD, BMD, and global stress metrics."""
    resolution: int
    sfd_points: list[Tuple[float, float]]
    bmd_points: list[Tuple[float, float]]
    max_m_abs: float
    max_v_abs: float
    max_v_x: float
    max_bending_stress: float
    max_shear_stress: float


class StateManager:
    beam_type: BeamType
    material_type: Optional[MaterialType]
    beam_length: float
    beam_dimensions: Optional[BeamDimensions]
    supports: List[SupportState]
    loads: List[LoadState]

    reaction_left: float
    reaction_left_pos: float
    reaction_right: float
    reaction_right_pos: float
    _beam: Optional[Beam]
    _diagram_map: Optional[DiagramDataMap]
    config: AnalysisConfig

    def __init__(self) -> None:
        self.config = AnalysisConfig()
        self.max_shear_stress = self.config.default_stress_scale
        self.max_bending_stress = self.config.default_stress_scale
        self.beam_type: BeamType = "Rectangular"
        self.material_type = MaterialType.STEEL
        self.beam_length = 10.0
        self.beam_dimensions = RectangularDimensions()
        self.supports = [
            SupportState("Pin", 0.0),
            SupportState("Roller", 10.0),
        ]
        self.loads = [
            PointLoadState(magnitude_kn=10.0, position_m=5.0)
        ]

        self.reaction_left = 0.0
        self.reaction_left_pos = 0.0
        self.reaction_right = 0.0
        self.reaction_right_pos = 10.0
        self._beam = None
        self._diagram_map = None
        self.cross_section_x = 5.0
        self.cross_section_y_meters = 0.0

    def solve(self) -> None:
        """Reads UI state, solves equilibrium, and caches one-time processed diagrams."""
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
                length=self.beam_length,
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

                def uvl_func(
                    x: float,
                    s: float = start,
                    e: float = end,
                    sm: float = start_mag,
                    em: float = end_mag,
                ) -> float:
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
        self.reaction_left_pos = beam.reaction_left.position
        self.reaction_right = beam.reaction_right.magnitude
        self.reaction_right_pos = beam.reaction_right.position
        self._beam = beam

        # Precompute and cache one-time processed SFD & BMD points
        n_pts = self.config.default_resolution
        dx = self.beam_length / n_pts
        sfd_points: list[Tuple[float, float]] = []
        bmd_points: list[Tuple[float, float]] = []

        max_m_abs = 0.0
        max_v_abs = 0.0
        max_v_x = 0.0

        for i in range(n_pts + 1):
            x = i * dx
            v = beam.get_shear_force(x)
            m = beam.get_bending_moment(x)
            sfd_points.append((x, v))
            bmd_points.append((x, m))

            v_abs = abs(v)
            m_abs = abs(m)
            if v_abs > max_v_abs:
                max_v_abs = v_abs
                max_v_x = x
            if m_abs > max_m_abs:
                max_m_abs = m_abs

        # Calculate global max stresses
        self.max_bending_stress = self.config.default_stress_scale
        self.max_shear_stress = self.config.default_stress_scale

        I = beam.get_second_moment_of_area()
        if I > 0:
            y_max = beam.get_height() / 2.0
            self.max_bending_stress = max(
                self.config.min_stress_floor,
                ((max_m_abs * y_max) / I) / 1000.0,
            )

            original_x = self.cross_section_x
            self.cross_section_x = max_v_x

            stresses = [stress for stress, _ in self.generate_shear_stress_points(self.config.scan_steps)]
            if len(stresses) > 0:
                self.max_shear_stress = max(
                    self.config.min_stress_floor,
                    float(max(abs(s) for s in stresses)),
                )

            self.cross_section_x = original_x

        self._diagram_map = DiagramDataMap(
            resolution=n_pts,
            sfd_points=sfd_points,
            bmd_points=bmd_points,
            max_m_abs=max_m_abs,
            max_v_abs=max_v_abs,
            max_v_x=max_v_x,
            max_bending_stress=self.max_bending_stress,
            max_shear_stress=self.max_shear_stress,
        )

    def generate_sfd_points(self, num_points: int = 100) -> Iterator[Tuple[float, float]]:
        if not self._beam or self.beam_length <= 0:
            return

        # If cached diagram points are available, stream directly from cache
        if self._diagram_map is not None:
            yield from self._diagram_map.sfd_points
            return

        dx = self.beam_length / num_points
        for i in range(num_points + 1):
            x = i * dx
            yield x, self._beam.get_shear_force(x)

    def generate_bmd_points(self, num_points: int = 100) -> Iterator[Tuple[float, float]]:
        if not self._beam or self.beam_length <= 0:
            return

        # If cached diagram points are available, stream directly from cache
        if self._diagram_map is not None:
            yield from self._diagram_map.bmd_points
            return

        dx = self.beam_length / num_points
        for i in range(num_points + 1):
            x = i * dx
            yield x, self._beam.get_bending_moment(x)

    def generate_bending_stress_points(self, num_points: int = 100) -> Iterator[Tuple[float, float]]:
        if not self._beam or self.beam_length <= 0:
            return

        target_x = min(max(0.0, self.cross_section_x), self.beam_length)
        M = self._beam.get_bending_moment(target_x)
        I = self._beam.get_second_moment_of_area()
        if I == 0:
            return

        h = self._beam.get_height()
        y_step = h / num_points
        y_start = -h / 2.0
        scale = M / (I * 1000.0)

        for i in range(num_points):
            y = y_start + i * y_step
            yield y * scale, y * 1000.0

    def generate_shear_stress_points(self, num_points: int = 100) -> Iterator[Tuple[float, float]]:
        if not self._beam or self.beam_length <= 0:
            return

        target_x = min(max(0.0, self.cross_section_x), self.beam_length)
        V = self._beam.get_shear_force(target_x)
        I = self._beam.get_second_moment_of_area()
        h = self._beam.get_height()
        y_step = h / num_points
        y_start = -h / 2.0

        for i in range(num_points):
            y = y_start + i * y_step
            Q = self._beam.get_first_moment_of_area(y)
            b = self._beam.get_width(y)
            if b == 0.0 or I == 0.0:
                stress_mpa = 0.0
            else:
                stress_kpa = (V * Q) / (I * b)
                stress_mpa = float(stress_kpa) / 1000.0
            yield stress_mpa, y * 1000.0

    def get_shear_force(self, cross_section_x: float) -> float:
        if self._beam is not None:
            return self._beam.get_shear_force(cross_section_x)
        return 0.0

    def get_bending_moment(self, cross_section_x: float) -> float:
        if self._beam is not None:
            return self._beam.get_bending_moment(cross_section_x)
        return 0.0

    def get_shear_stress(self, cross_section_y: float) -> float:
        if self._beam is None:
            return 0.0
        V = self._beam.get_shear_force(self.cross_section_x)
        I = self._beam.get_second_moment_of_area()
        y = cross_section_y
        Q = self._beam.get_first_moment_of_area(y)
        b = self._beam.get_width(y)
        if b == 0.0 or I == 0.0:
            return 0.0
        stress_kpa = (V * Q) / (I * b)
        return float(stress_kpa) / 1000.0

    def get_bending_stress(self, cross_section_y: float) -> float:
        if self._beam is None:
            return 0.0
        M = self._beam.get_bending_moment(self.cross_section_x)
        I = self._beam.get_second_moment_of_area()
        if I == 0:
            return 0.0
        stress_kpa = (M * float(cross_section_y)) / I
        return stress_kpa / 1000.0
