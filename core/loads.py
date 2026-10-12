import math
from dataclasses import dataclass
from typing import Optional

from core.integration import RombergIntegrator, romberg_integral, simpson_one_third
from core.types import LoadFunction


class ReactionForce:
    magnitude: float
    position: float

    def __init__(self, magnitude: float, position: float):
        self.magnitude = magnitude
        self.position = position


class PointLoad:
    magnitude: float
    position: float

    def __init__(self, magnitude: float, position: float):
        self.magnitude = magnitude
        self.position = position


@dataclass(slots=True)
class CumulativeSamplePoint:
    """Precomputed cumulative integral metrics at a discrete point x."""
    x: float
    cumulative_area: float       # Integral of f(t) from start to x
    cumulative_moment_0: float   # Integral of t * f(t) from start to x


@dataclass(slots=True)
class LoadCumulativeMap:
    """Class storing one-time precomputed cumulative integral profile across [start, end]."""
    start: float
    end: float
    total_area: float
    centroid: float
    total_moment: float
    samples: list[CumulativeSamplePoint]
    step_size: float
    is_zero_load: bool


@dataclass(slots=True)
class PartialLoadContribution:
    """Class storing cached shear force and bending moment contributions for position x."""
    shear: float
    moment: float


class LoadContributionCache:
    """Map-based cache storing evaluated contributions for position x."""
    _cache: dict[float, PartialLoadContribution]
    max_capacity: int

    def __init__(self, max_capacity: int = 500) -> None:
        self._cache = {}
        self.max_capacity = max_capacity

    def get(self, x: float) -> Optional[PartialLoadContribution]:
        key = round(x, 3)
        return self._cache.get(key)

    def put(self, x: float, data: PartialLoadContribution) -> None:
        if len(self._cache) >= self.max_capacity:
            first_key = next(iter(self._cache))
            del self._cache[first_key]
        key = round(x, 3)
        self._cache[key] = data

    def clear(self) -> None:
        self._cache.clear()


class Load:
    """Continuous distributed load with full precomputed cumulative integral caching.

    Entire load integrals for shear force and bending moment are computed once upon initialization,
    completely eliminating repeated numerical integration calls during simulation and slider interaction.
    """
    start: float
    end: float
    function: LoadFunction
    step_size: float
    _cumulative_map: LoadCumulativeMap
    _cache: LoadContributionCache

    SAMPLE_INTERVALS: int = 60

    def __init__(self, start: float, end: float, function: LoadFunction):
        self.start = start
        self.end = end
        self.function = function
        self.step_size = 0.01
        self._cache = LoadContributionCache()
        self._cumulative_map = self._build_cumulative_map()

    def _build_cumulative_map(self) -> LoadCumulativeMap:
        """One-time processing and caching of the entire load integral curve."""
        if self.start >= self.end:
            zero_pt = CumulativeSamplePoint(x=self.start, cumulative_area=0.0, cumulative_moment_0=0.0)
            return LoadCumulativeMap(
                start=self.start,
                end=self.end,
                total_area=0.0,
                centroid=self.start,
                total_moment=0.0,
                samples=[zero_pt],
                step_size=0.0,
                is_zero_load=True,
            )

        n = self.SAMPLE_INTERVALS
        span = self.end - self.start
        dx = span / n

        samples: list[CumulativeSamplePoint] = []
        samples.append(CumulativeSamplePoint(x=self.start, cumulative_area=0.0, cumulative_moment_0=0.0))

        # Build cumulative samples across [start, end]
        running_area = 0.0
        running_moment_0 = 0.0
        moment_func = lambda t: t * self.function(t)

        for i in range(1, n + 1):
            sub_start = self.start + (i - 1) * dx
            sub_end = self.start + i * dx
            d_area = romberg_integral(self.function, sub_start, sub_end, tolerance=0.1)
            d_moment = romberg_integral(moment_func, sub_start, sub_end, tolerance=0.1)
            running_area += d_area
            running_moment_0 += d_moment
            samples.append(
                CumulativeSamplePoint(
                    x=sub_end,
                    cumulative_area=running_area,
                    cumulative_moment_0=running_moment_0,
                )
            )

        total_area = running_area
        total_moment = running_moment_0
        if abs(total_area) < 1e-12:
            centroid = (self.start + self.end) / 2.0
            is_zero_load = True
        else:
            centroid = total_moment / total_area
            is_zero_load = False

        return LoadCumulativeMap(
            start=self.start,
            end=self.end,
            total_area=total_area,
            centroid=centroid,
            total_moment=total_moment,
            samples=samples,
            step_size=dx,
            is_zero_load=is_zero_load,
        )

    @property
    def cumulative_map(self) -> LoadCumulativeMap:
        return self._cumulative_map

    @property
    def profile_map(self) -> LoadCumulativeMap:
        """Backward-compatible property."""
        return self._cumulative_map

    def _interpolate_cumulative(self, x: float) -> tuple[float, float]:
        """O(1) interpolation in the precomputed cumulative integral map."""
        if x <= self.start:
            return 0.0, 0.0
        if x >= self.end:
            return self._cumulative_map.total_area, self._cumulative_map.total_moment

        # Compute index directly via uniform grid
        dx = self._cumulative_map.step_size
        if dx <= 0.0:
            return 0.0, 0.0

        idx = int((x - self.start) / dx)
        idx = max(0, min(idx, len(self._cumulative_map.samples) - 2))

        p0 = self._cumulative_map.samples[idx]
        p1 = self._cumulative_map.samples[idx + 1]

        t = (x - p0.x) / (p1.x - p0.x) if (p1.x > p0.x) else 0.0
        area = p0.cumulative_area + t * (p1.cumulative_area - p0.cumulative_area)
        moment_0 = p0.cumulative_moment_0 + t * (p1.cumulative_moment_0 - p0.cumulative_moment_0)
        return area, moment_0

    def get_area(self, start: Optional[float] = None, end: Optional[float] = None) -> float:
        """Fast area calculation using cumulative integral map differences (zero integration calls)."""
        effective_start = self.start if start is None else max(start, self.start)
        effective_end = self.end if end is None else min(end, self.end)

        if effective_start >= effective_end:
            return 0.0

        if effective_start == self.start and effective_end == self.end:
            return self._cumulative_map.total_area

        area_end, _ = self._interpolate_cumulative(effective_end)
        area_start, _ = self._interpolate_cumulative(effective_start)
        return area_end - area_start

    def get_avg_value_point(self, start: Optional[float] = None, end: Optional[float] = None) -> float:
        """Fast centroid calculation using cumulative integral map differences (zero integration calls)."""
        effective_start = self.start if start is None else max(start, self.start)
        effective_end = self.end if end is None else min(end, self.end)

        if effective_start >= effective_end:
            return effective_start

        if effective_start == self.start and effective_end == self.end:
            return self._cumulative_map.centroid

        area_end, m0_end = self._interpolate_cumulative(effective_end)
        area_start, m0_start = self._interpolate_cumulative(effective_start)

        denom = area_end - area_start
        if abs(denom) < 1e-12:
            return effective_start

        num = m0_end - m0_start
        return num / denom

    def get_shear_contribution(self, x: float) -> float:
        """Instant O(1) shear force contribution from precomputed map and cache."""
        if x <= self.start:
            return 0.0
        if x >= self.end:
            return self._cumulative_map.total_area

        cached = self._cache.get(x)
        if cached is not None:
            return cached.shear

        area, m0 = self._interpolate_cumulative(x)
        moment = x * area - m0
        self._cache.put(x, PartialLoadContribution(shear=area, moment=moment))
        return area

    def get_moment_contribution(self, x: float) -> float:
        """Instant O(1) bending moment contribution from precomputed map and cache."""
        if x <= self.start:
            return 0.0
        if x >= self.end:
            return (x - self._cumulative_map.centroid) * self._cumulative_map.total_area

        cached = self._cache.get(x)
        if cached is not None:
            return cached.moment

        area, m0 = self._interpolate_cumulative(x)
        moment = x * area - m0
        self._cache.put(x, PartialLoadContribution(shear=area, moment=moment))
        return moment
