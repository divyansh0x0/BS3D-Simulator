from collections.abc import Iterator
from dataclasses import dataclass
from typing import List, Optional, Tuple

from core.beam import Beam
from core.sections import CircularBeam, IBeam, RectangularBeam
from core.types import BeamType
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
    cross_section_cache_capacity: int = 500
    depth_cache_capacity: int = 1000


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


@dataclass(slots=True)
class CrossSectionStressMap:
    """Class storing precomputed stress graphs and forces for a specific x coordinate."""
    x_meters: float
    shear_force: float
    bending_moment: float
    shear_stress_points: list[Tuple[float, float]]
    bending_stress_points: list[Tuple[float, float]]


class CrossSectionStressCache:
    """Map-based cache storing one-time processed stress distribution graphs for position x."""
    _cache: dict[float, CrossSectionStressMap]
    max_capacity: int

    def __init__(self, max_capacity: int = 500) -> None:
        self._cache = {}
        self.max_capacity = max_capacity

    def get(self, x: float) -> Optional[CrossSectionStressMap]:
        key = round(x, 2)
        return self._cache.get(key)

    def put(self, x: float, data: CrossSectionStressMap) -> None:
        if len(self._cache) >= self.max_capacity:
            first_key = next(iter(self._cache))
            del self._cache[first_key]
        key = round(x, 2)
        self._cache[key] = data

    def clear(self) -> None:
        self._cache.clear()


@dataclass(slots=True)
class DepthStressEvaluation:
    """Class storing point stress values at specific (x, y) coordinates."""
    x_meters: float
    y_meters: float
    shear_stress_mpa: float
    bending_stress_mpa: float


class DepthStressCache:
    """Map-based cache storing point stress evaluations for coordinates (x, y)."""
    _cache: dict[Tuple[float, float], DepthStressEvaluation]
    max_capacity: int

    def __init__(self, max_capacity: int = 1000) -> None:
        self._cache = {}
        self.max_capacity = max_capacity

    def get(self, x: float, y: float) -> Optional[DepthStressEvaluation]:
        key = (round(x, 2), round(y, 4))
        return self._cache.get(key)

    def put(self, x: float, y: float, data: DepthStressEvaluation) -> None:
        if len(self._cache) >= self.max_capacity:
            first_key = next(iter(self._cache))
            del self._cache[first_key]
        key = (round(x, 2), round(y, 4))
        self._cache[key] = data

    def clear(self) -> None:
        self._cache.clear()


@dataclass(slots=True)
class UnitStressProfilePoint:
    """Normalized geometric profile factor across cross-section depth y."""
    unit_bending_factor: float  # y / I
    unit_shear_factor: float    # Q(y) / (I * b(y))
    y_mm: float


@dataclass(slots=True)
class SectionUnitStressMap:
    """One-time processed geometric stress profile for the beam cross section."""
    points: list[UnitStressProfilePoint]


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
    _cross_section_cache: CrossSectionStressCache
    _depth_stress_cache: DepthStressCache
    _unit_stress_map: Optional[SectionUnitStressMap]
    config: AnalysisConfig

    def __init__(self) -> None:
        self.config = AnalysisConfig()
        self.max_shear_stress = self.config.default_stress_scale
        self.max_bending_stress = self.config.default_stress_scale
        self.beam_type = "Rectangular"
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
        self._cross_section_cache = CrossSectionStressCache(self.config.cross_section_cache_capacity)
        self._depth_stress_cache = DepthStressCache(self.config.depth_cache_capacity)
        self._unit_stress_map = None
        self.cross_section_x = 5.0
        self.cross_section_y_meters = 0.0

    def _build_unit_stress_map(self) -> Optional[SectionUnitStressMap]:
        """Precomputes geometric stress profile across depth y for O(1) graph scaling."""
        if not self._beam:
            return None

        I = self._beam.get_second_moment_of_area()
        h = self._beam.get_height()
        if I <= 0 or h <= 0:
            return None

        n_pts = self.config.stress_resolution
        y_step = h / n_pts
        y_start = -h / 2.0
        pts: list[UnitStressProfilePoint] = []

        for i in range(n_pts):
            y = y_start + i * y_step
            Q = self._beam.get_first_moment_of_area(y)
            b = self._beam.get_width(y)

            unit_bending = y / I
            unit_shear = (Q / (I * b)) if (b > 0.0 and I > 0.0) else 0.0
            pts.append(
                UnitStressProfilePoint(
                    unit_bending_factor=unit_bending,
                    unit_shear_factor=unit_shear,
                    y_mm=y * 1000.0,
                )
            )

        return SectionUnitStressMap(points=pts)

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

        # Invalidate cross-section specific caches on new solve
        self._cross_section_cache.clear()
        self._depth_stress_cache.clear()
        self._unit_stress_map = self._build_unit_stress_map()

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

    def _get_or_compute_stress_graphs(self, target_x: float) -> Optional[CrossSectionStressMap]:
        """Retrieves cached stress distribution graphs or computes and stores them."""
        if not self._beam:
            return None

        cached = self._cross_section_cache.get(target_x)
        if cached is not None:
            return cached

        V = self._beam.get_shear_force(target_x)
        M = self._beam.get_bending_moment(target_x)

        if self._unit_stress_map is not None:
            b_pts = [
                ((pt.unit_bending_factor * M) / 1000.0, pt.y_mm)
                for pt in self._unit_stress_map.points
            ]
            s_pts = [
                ((pt.unit_shear_factor * V) / 1000.0, pt.y_mm)
                for pt in self._unit_stress_map.points
            ]
        else:
            I = self._beam.get_second_moment_of_area()
            h = self._beam.get_height()
            n_pts = self.config.stress_resolution
            y_step = h / n_pts
            y_start = -h / 2.0
            b_pts = []
            s_pts = []
            for i in range(n_pts):
                y = y_start + i * y_step
                y_mm = y * 1000.0
                Q = self._beam.get_first_moment_of_area(y)
                b = self._beam.get_width(y)

                b_stress = (M * float(y)) / (I * 1000.0) if I > 0 else 0.0
                s_stress = ((V * Q) / (I * b * 1000.0)) if (b > 0 and I > 0) else 0.0
                b_pts.append((b_stress, y_mm))
                s_pts.append((s_stress, y_mm))

        computed = CrossSectionStressMap(
            x_meters=target_x,
            shear_force=V,
            bending_moment=M,
            shear_stress_points=s_pts,
            bending_stress_points=b_pts,
        )
        self._cross_section_cache.put(target_x, computed)
        return computed

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
        stress_map = self._get_or_compute_stress_graphs(target_x)
        if stress_map is not None:
            yield from stress_map.bending_stress_points

    def generate_shear_stress_points(self, num_points: int = 100) -> Iterator[Tuple[float, float]]:
        if not self._beam or self.beam_length <= 0:
            return

        target_x = min(max(0.0, self.cross_section_x), self.beam_length)
        stress_map = self._get_or_compute_stress_graphs(target_x)
        if stress_map is not None:
            yield from stress_map.shear_stress_points

    def get_shear_force(self, cross_section_x: float) -> float:
        if self._beam is None:
            return 0.0

        cached = self._cross_section_cache.get(cross_section_x)
        if cached is not None:
            return cached.shear_force

        return self._beam.get_shear_force(cross_section_x)

    def get_bending_moment(self, cross_section_x: float) -> float:
        if self._beam is None:
            return 0.0

        cached = self._cross_section_cache.get(cross_section_x)
        if cached is not None:
            return cached.bending_moment

        return self._beam.get_bending_moment(cross_section_x)

    def get_shear_stress(self, cross_section_y: float) -> float:
        if self._beam is None:
            return 0.0

        target_x = min(max(0.0, self.cross_section_x), self.beam_length)
        cached = self._depth_stress_cache.get(target_x, cross_section_y)
        if cached is not None:
            return cached.shear_stress_mpa

        V = self.get_shear_force(target_x)
        M = self.get_bending_moment(target_x)
        I = self._beam.get_second_moment_of_area()
        y = cross_section_y
        Q = self._beam.get_first_moment_of_area(y)
        b = self._beam.get_width(y)

        s_mpa = float((V * Q) / (I * b)) / 1000.0 if (b > 0.0 and I > 0.0) else 0.0
        b_mpa = (M * float(y)) / (I * 1000.0) if I > 0.0 else 0.0

        eval_data = DepthStressEvaluation(
            x_meters=target_x,
            y_meters=cross_section_y,
            shear_stress_mpa=s_mpa,
            bending_stress_mpa=b_mpa,
        )
        self._depth_stress_cache.put(target_x, cross_section_y, eval_data)
        return s_mpa

    def get_bending_stress(self, cross_section_y: float) -> float:
        if self._beam is None:
            return 0.0

        target_x = min(max(0.0, self.cross_section_x), self.beam_length)
        cached = self._depth_stress_cache.get(target_x, cross_section_y)
        if cached is not None:
            return cached.bending_stress_mpa

        # get_shear_stress calculates and caches both shear and bending stresses for (target_x, cross_section_y)
        self.get_shear_stress(cross_section_y)
        cached = self._depth_stress_cache.get(target_x, cross_section_y)
        return cached.bending_stress_mpa if cached else 0.0
