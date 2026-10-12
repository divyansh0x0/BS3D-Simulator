from core.integration import simpsonIntegral
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


class Load:
    start: float
    end: float
    function: LoadFunction

    def __init__(self, start: float, end: float, function: LoadFunction):
        self.start = start
        self.end = end
        self.function = function
        self.step_size = 0.01

    def get_area(self, start: None | float = None, end: None | float = None) -> float:
        if start is None:
            start = self.start
        if end is None:
            end = self.end
        end = min(end, self.end)
        start = max(start, self.start)
        return simpsonIntegral(self.function, start, end, self.step_size)

    def get_avg_value_point(self, start: None | float = None, end: None | float = None) -> float:
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
