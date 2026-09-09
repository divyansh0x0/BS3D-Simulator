from typing import Literal, Callable, TypeAlias, override

import numpy as np

# 1. Custom Type Aliases
BeamType = Literal["Rectangular", "Circular", "I-Beam"]
LoadType = Literal["Point", "UDL", "UVL"]

ArrayPair: TypeAlias = tuple[np.ndarray, np.ndarray]
LoadFunction = Callable[[float], float]


def simpsonIntegral(function: LoadFunction, start: float, end: float, step_size: float):
    if end >= start:
        return 0
    n = int((end - start) / step_size)
    n = max(3, n + (3 - n % 3) % 3)
    step_size = (end - start) / n
    x1 = start
    x2 = end
    y1 = function(x1)
    y2 = function(x2)

    sum = 0
    for i in range(1, n):
        if i % 3 == 0:
            y = function(x1 + step_size * i)
            sum += y * 2
        else:
            y = function(x1 + step_size * i)
            sum += y * 3
    return 3 * step_size / 8 * (y1 + y2 + sum)


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

class Load:
    start: float
    end: float
    function: LoadFunction

    def __init__(self, start: float, end: float, function: LoadFunction):
        self.start = start
        self.end = end
        self.function = function
        self.step_size = 0.01

    def get_area(self, start: None | float = None, end: None | float = None):
        if start is None:
            start = self.start
        if end is None:
            end = self.end
        end = min(end, self.end)
        start = max(start, self.start)
        return simpsonIntegral(self.function, start, end, self.step_size)

    def get_avg_value_point(self, start: None | float = None, end: None | float = None):
        if start is None:
            start = self.start
        if end is None:
            end = self.end
        end = min(end, self.end)
        start = max(start, self.start)

        numerator = simpsonIntegral(lambda x: x * self.function(x), start, end, self.step_size)
        denominator = self.get_area(start, end)
        if denominator == 0:
            return start
        return numerator / denominator


PhysicsSolver = Callable[[list[Load]], ArrayPair]


class Beam:
    def __init__(self, beam_type: BeamType, beam_length: float):
        self.type: BeamType = beam_type
        self.continuous_loads: list[Load] = []
        self.point_loads: list[PointLoad] = []
        self.total_load: float = 0
        self.reaction_left = ReactionForce(0, 0)
        self.reaction_right = ReactionForce(0, beam_length)

    def get_second_moment_of_area(self) -> float:
        pass

    def get_first_moment_of_area(self, y) -> float:
        pass

    def set_load_function(self, start: float, end: float, function: LoadFunction):
        self.continuous_loads.append(Load(start, end, function))
        self.update_loads()

    def update_loads(self):
        sum_moments = 0
        sum_load = 0
        for load in  self.continuous_loads:
            average_load = load.get_area()
            sum_load += average_load
            sum_moments += average_load * load.get_avg_value_point()
        for load in self.point_loads:
            sum_load += load.magnitude
            sum_moments += load.magnitude * load.position

        self.reaction_left.magnitude = (sum_moments - self.reaction_right.position * sum_load) / (
                self.reaction_left.position - self.reaction_right.position)
        self.reaction_right.magnitude = sum_load - self.reaction_left.magnitude
        self.total_load = sum_load

    def get_shear_force(self, x: float):
        sum_left = 0
        for load in self.continuous_loads:
            if load.start > x:  # skip right side loads
                continue
            sum_left += load.get_area(0, x)
            pass
        for load in self.point_loads:
            if load.position > x:  # skip right side loads
                continue
            sum_left += load.magnitude
        if x < self.reaction_right.position:
            return self.reaction_left.magnitude - sum_left
        else:
            return self.reaction_left.magnitude + self.reaction_right.magnitude - sum_left

    def get_bending_moment(self, x: float):
        sum_moments = 0
        for load in self.continuous_loads:
            if load.start > x:  # skip right side loads
                continue
            avg_load_pos_x = load.get_avg_value_point(0, x)
            avg_load = load.get_area(0, x)
            sum_moments += (x - avg_load_pos_x) * avg_load
        for load in self.point_loads:
            if load.position > x:  # skip right side loads
                continue
            sum_moments += (x - load.position) * load.magnitude
        reaction_moment_left = self.reaction_left.magnitude * (x - self.reaction_left.position)
        if x < self.reaction_right.position:
            return reaction_moment_left - sum_moments
        else:
            reaction_moment_right = self.reaction_right.magnitude * (x - self.reaction_right.position)
            return reaction_moment_left + reaction_moment_right - sum_moments


class IBeam(Beam):
    def __init__(self, flange_width: float, flange_height: float, web_width: float, web_height: float, length: float):
        super().__init__("I-Beam", length)
        self.flange_w: float = flange_width
        self.flange_h: float = flange_height
        self.web_w: float = web_width
        self.web_h: float = web_height

    @override
    def get_second_moment_of_area(self) -> float:
        h1 = self.flange_h * 2 + self.web_h
        w1 = self.flange_w

        h2 = self.web_h
        w2 = self.flange_w - self.web_w

        return w1 * (h1 ** 3) / 12 - w2 * (h2 ** 3) / 12

    @override
    def get_first_moment_of_area(self, y: float) -> float:
        h1 = self.flange_h * 2 + self.web_h
        if y <= self.web_h / 2:
            return self.flange_w * self.flange_h * (h1 / 2 - self.flange_h / 2) + self.web_w / 2 * (
                    (h1 / 2 - self.flange_h) ** 2 - y ** 2)
        else:
            return self.flange_w / 2 * (h1 / 2 - y) ** 2
