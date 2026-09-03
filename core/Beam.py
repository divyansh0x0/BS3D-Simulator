from dataclasses import dataclass
from typing import override

import numpy as np

from types import BeamType, LoadFunction

@dataclass
class Load:
    start: float
    end: float
    function: LoadFunction

class Beam:
    def __init__(self, type: BeamType):
        self.type: BeamType = type
        self.load_function: list[Load] = []
        self.moments: list[float] = [];
    def get_second_moment_of_area(self) -> float:
        pass

    def get_first_moment_of_area(self, y) -> float:
        pass
    def get_loads(self) -> list[float]:
        pass
    def get_moments(self) -> list[float]:
        return self.moments
    def set_load_function(self, start: float, end: float, function: LoadFunction):
        self.load_function.append(Load(start, end,function))
    def set_moments(self, index, position: float, magnitude: float):
        self.moments.insert(index, position)


class IBeam(Beam):
    def __init__(self, flange_width: float, flange_height: float, web_width: float, web_height: float):
        super().__init__("I-Beam")
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
    def get_first_moment_of_area(self, y) -> float:
        h1 = self.flange_h * 2 + self.web_h
        if y <= self.web_h / 2:
            return self.flange_w * self.flange_h * (h1 / 2 - self.flange_h / 2) + self.web_w / 2 * (
                    (h1 / 2 - self.flange_h) ** 2 - y ** 2)
        else:
            return self.flange_w / 2 * (h1 / 2 - y) ** 2

