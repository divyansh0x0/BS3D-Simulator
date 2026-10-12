from dataclasses import dataclass
from typing import Optional

from core.integration import simpson_one_third
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
class LoadProfileMap:
    """Class storing one-time processed integration metrics for a continuous load."""
    total_area: float
    centroid: float
    total_moment: float
    is_zero_load: bool


class Load:
    start: float
    end: float
    function: LoadFunction
    step_size: float
    _profile_map: LoadProfileMap

    def __init__(self, start: float, end: float, function: LoadFunction):
        self.start = start
        self.end = end
        self.function = function
        self.step_size = 0.01
        self._profile_map = self._build_profile_map()

    def _build_profile_map(self) -> LoadProfileMap:
        """One-time processing of continuous load metrics using Simpson 1/3 with error reduction."""
        if self.start >= self.end:
            return LoadProfileMap(
                total_area=0.0,
                centroid=self.start,
                total_moment=0.0,
                is_zero_load=True,
            )

        total_area = simpson_one_third(self.function, self.start, self.end)
        if abs(total_area) < 1e-12:
            centroid = (self.start + self.end) / 2.0
            total_moment = 0.0
            is_zero_load = True
        else:
            num = simpson_one_third(lambda x: x * self.function(x), self.start, self.end)
            centroid = num / total_area
            total_moment = num
            is_zero_load = False

        return LoadProfileMap(
            total_area=total_area,
            centroid=centroid,
            total_moment=total_moment,
            is_zero_load=is_zero_load,
        )

    @property
    def profile_map(self) -> LoadProfileMap:
        return self._profile_map

    def get_area(self, start: Optional[float] = None, end: Optional[float] = None) -> float:
        effective_start = self.start if start is None else max(start, self.start)
        effective_end = self.end if end is None else min(end, self.end)

        if effective_start >= effective_end:
            return 0.0

        # O(1) fast return for full span
        if effective_start == self.start and effective_end == self.end:
            return self._profile_map.total_area

        return simpson_one_third(self.function, effective_start, effective_end)

    def get_avg_value_point(self, start: Optional[float] = None, end: Optional[float] = None) -> float:
        effective_start = self.start if start is None else max(start, self.start)
        effective_end = self.end if end is None else min(end, self.end)

        if effective_start >= effective_end:
            return effective_start

        # O(1) fast return for full span
        if effective_start == self.start and effective_end == self.end:
            return self._profile_map.centroid

        denominator = self.get_area(effective_start, effective_end)
        if abs(denominator) < 1e-12:
            return effective_start

        numerator = simpson_one_third(lambda x: x * self.function(x), effective_start, effective_end)
        return numerator / denominator

    def get_shear_contribution(self, x: float) -> float:
        """Fast shear force contribution of this load up to position x."""
        if x <= self.start:
            return 0.0
        if x >= self.end:
            return self._profile_map.total_area
        return self.get_area(self.start, x)

    def get_moment_contribution(self, x: float) -> float:
        """Fast bending moment contribution of this load up to position x."""
        if x <= self.start:
            return 0.0
        if x >= self.end:
            # (x - centroid) * total_area
            return (x - self._profile_map.centroid) * self._profile_map.total_area

        partial_area = self.get_area(self.start, x)
        if abs(partial_area) < 1e-12:
            return 0.0
        partial_centroid = self.get_avg_value_point(self.start, x)
        return (x - partial_centroid) * partial_area
