import math
from typing import override

from core.beam import Beam


class RectangularBeam(Beam):
    height: float
    width: float
    _second_moment: float

    def __init__(self, height: float, width: float, length: float):
        super().__init__("Rectangular", length)
        self.height = height
        self.width = width
        # Precomputed one-time geometric property
        self._second_moment = (self.width * self.height**3) / 12.0

    @override
    def get_second_moment_of_area(self) -> float:
        return self._second_moment

    @override
    def get_first_moment_of_area(self, y: float) -> float:
        return (self.height**2 / 4.0 - y**2) * self.width / 2.0

    @override
    def get_width(self, y: float) -> float:
        return self.width

    @override
    def get_height(self) -> float:
        return self.height


class CircularBeam(Beam):
    diameter: float
    _second_moment: float
    _radius_sq: float

    def __init__(self, diameter: float, length: float):
        super().__init__("Circular", length)
        self.diameter = diameter
        # Precomputed one-time geometric properties
        self._second_moment = (math.pi * self.diameter**4) / 64.0
        self._radius_sq = (self.diameter / 2.0) ** 2

    @override
    def get_second_moment_of_area(self) -> float:
        return self._second_moment

    @override
    def get_first_moment_of_area(self, y: float) -> float:
        return ((self._radius_sq - y**2) ** 1.5) * 2.0 / 3.0

    @override
    def get_width(self, y: float) -> float:
        return 2.0 * math.sqrt(max(0.0, self._radius_sq - y**2))

    @override
    def get_height(self) -> float:
        return self.diameter


class IBeam(Beam):
    flange_w: float
    flange_h: float
    web_w: float
    web_h: float
    _total_height: float
    _second_moment: float

    def __init__(
        self,
        flange_width: float,
        flange_height: float,
        web_width: float,
        web_height: float,
        length: float,
    ):
        super().__init__("IBeam", length)
        self.flange_w = flange_width
        self.flange_h = flange_height
        self.web_w = web_width
        self.web_h = web_height
        self._total_height = self.flange_h * 2.0 + self.web_h

        h1 = self._total_height
        w1 = self.flange_w
        h2 = self.web_h
        w2 = self.flange_w - self.web_w
        self._second_moment = w1 * (h1**3) / 12.0 - w2 * (h2**3) / 12.0

    @override
    def get_second_moment_of_area(self) -> float:
        return self._second_moment

    @override
    def get_first_moment_of_area(self, y: float) -> float:
        h1 = self._total_height
        abs_y = abs(y)
        if abs_y <= self.web_h / 2.0:
            return self.flange_w * self.flange_h * (h1 / 2.0 - self.flange_h / 2.0) + self.web_w / 2.0 * (
                (h1 / 2.0 - self.flange_h) ** 2 - abs_y**2
            )
        else:
            return self.flange_w / 2.0 * ((h1 / 2.0) ** 2 - abs_y**2)

    @override
    def get_width(self, y: float) -> float:
        if abs(y) <= self.web_h / 2.0:
            return self.web_w
        return self.flange_w

    @override
    def get_height(self) -> float:
        return self._total_height
