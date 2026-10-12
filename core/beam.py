from dataclasses import dataclass
from typing import Optional

from core.loads import Load, PointLoad, ReactionForce
from core.types import BeamType, LoadFunction


@dataclass(slots=True)
class BeamEquilibriumState:
    """Class storing one-time processed equilibrium state for a beam."""
    total_load: float
    reaction_left_magnitude: float
    reaction_left_position: float
    reaction_right_magnitude: float
    reaction_right_position: float


class Beam:
    type: BeamType
    continuous_loads: list[Load]
    point_loads: list[PointLoad]
    total_load: float
    reaction_left: ReactionForce
    reaction_right: ReactionForce
    _equilibrium_state: Optional[BeamEquilibriumState]

    def __init__(self, beam_type: BeamType, beam_length: float):
        self.type = beam_type
        self.continuous_loads = []
        self.point_loads = []
        self.total_load = 0.0
        self.reaction_left = ReactionForce(0.0, 0.0)
        self.reaction_right = ReactionForce(0.0, beam_length)
        self._equilibrium_state = None

    def get_second_moment_of_area(self) -> float:
        pass

    def get_first_moment_of_area(self, y: float) -> float:
        pass

    def set_load_function(self, start: float, end: float, function: LoadFunction) -> None:
        self.continuous_loads.append(Load(start, end, function))
        self._equilibrium_state = None

    def set_point_load(self, load: float, x: float) -> None:
        self.point_loads.append(PointLoad(magnitude=load, position=x))
        self._equilibrium_state = None

    def update_loads(self) -> None:
        sum_moments = 0.0
        sum_load = 0.0

        for load in self.continuous_loads:
            # Uses O(1) precomputed metrics from LoadProfileMap
            area = load.profile_map.total_area
            sum_load += area
            sum_moments += load.profile_map.total_moment

        for p_load in self.point_loads:
            sum_load += p_load.magnitude
            sum_moments += p_load.magnitude * p_load.position

        pos_diff = self.reaction_left.position - self.reaction_right.position
        if abs(pos_diff) > 1e-12:
            self.reaction_left.magnitude = (
                sum_moments - self.reaction_right.position * sum_load
            ) / pos_diff
        else:
            self.reaction_left.magnitude = sum_load / 2.0

        self.reaction_right.magnitude = sum_load - self.reaction_left.magnitude
        self.total_load = sum_load

        self._equilibrium_state = BeamEquilibriumState(
            total_load=self.total_load,
            reaction_left_magnitude=self.reaction_left.magnitude,
            reaction_left_position=self.reaction_left.position,
            reaction_right_magnitude=self.reaction_right.magnitude,
            reaction_right_position=self.reaction_right.position,
        )

    def get_shear_force(self, x: float) -> float:
        sum_left = 0.0
        for load in self.continuous_loads:
            if load.start > x:
                continue
            sum_left += load.get_shear_contribution(x)

        for p_load in self.point_loads:
            if p_load.position > x:
                continue
            sum_left += p_load.magnitude

        if x < self.reaction_right.position:
            return self.reaction_left.magnitude - sum_left
        else:
            return self.reaction_left.magnitude + self.reaction_right.magnitude - sum_left

    def get_bending_moment(self, x: float) -> float:
        sum_moments = 0.0
        for load in self.continuous_loads:
            if load.start > x:
                continue
            sum_moments += load.get_moment_contribution(x)

        for p_load in self.point_loads:
            if p_load.position > x:
                continue
            sum_moments += (x - p_load.position) * p_load.magnitude

        reaction_moment_left = self.reaction_left.magnitude * (x - self.reaction_left.position)
        if x < self.reaction_right.position:
            return reaction_moment_left - sum_moments
        else:
            reaction_moment_right = self.reaction_right.magnitude * (x - self.reaction_right.position)
            return reaction_moment_left + reaction_moment_right - sum_moments

    def get_width(self, y: float) -> float:
        pass

    def get_height(self) -> float:
        pass
