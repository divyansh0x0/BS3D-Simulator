import math
from typing import override

from core.beam import Beam


class RectangularBeam(Beam):
    def __init__(self, height: float, width: float, length: float):
        super().__init__("Rectangular", length)
        self.height: float = height
        self.width: float = width

    @override
    def get_second_moment_of_area(self) -> float:
        h = self.height
        w = self.width
        return (w * h ** 3) / 12

    @override
    def get_first_moment_of_area(self, y: float) -> float:
        h = self.height
        w = self.width
        return (h ** 2 / 4 - y ** 2) * w / 2

    @override
    def get_width(self, y: float) -> float:
        return self.width

    @override
    def get_height(self) -> float:
        return self.height


class CircularBeam(Beam):
    def __init__(self, diameter: float, length: float):
        super().__init__("Circular", length)
        self.diameter: float = diameter

    @override
    def get_second_moment_of_area(self) -> float:
        d = self.diameter
        return (math.pi * d ** 4) / 64

    @override
    def get_first_moment_of_area(self, y: float) -> float:
        d = self.diameter
        return ((d ** 2 / 4 - y ** 2) ** 1.5) * 2 / 3

    @override
    def get_width(self, y: float) -> float:
        r = self.diameter / 2
        return 2 * math.sqrt(max(0, r ** 2 - y ** 2))

    @override
    def get_height(self) -> float:
        return self.diameter


class IBeam(Beam):
    def __init__(self, flange_width: float, flange_height: float, web_width: float, web_height: float, length: float):
        super().__init__("IBeam", length)
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
        abs_y = abs(y)
        if abs_y <= self.web_h / 2:
            return self.flange_w * self.flange_h * (h1 / 2 - self.flange_h / 2) + self.web_w / 2 * (
                    (h1 / 2 - self.flange_h) ** 2 - abs_y ** 2)
        else:
            return self.flange_w / 2 * ((h1 / 2) ** 2 - abs_y ** 2)

    @override
    def get_width(self, y: float) -> float:
        if abs(y) <= self.web_h / 2:
            return self.web_w
        else:
            return self.flange_w

    @override
    def get_height(self) -> float:
        return self.flange_h * 2 + self.web_h
