from dataclasses import dataclass

from core.types import LoadType


@dataclass
class LoadState:
    load_type: LoadType


@dataclass
class PointLoadState(LoadState):
    magnitude_kn: float = 0.0
    position_m: float = 0.0

    def __init__(self, magnitude_kn: float = 0.0, position_m: float = 0.0):
        super().__init__("Point")
        self.magnitude_kn = magnitude_kn
        self.position_m = position_m


@dataclass
class UDLLoadState(LoadState):
    intensity_kn_m: float = 0.0
    start_position_m: float = 0.0
    end_position_m: float = 0.0

    def __init__(self, intensity_kn_m: float = 0.0, start_position_m: float = 0.0, end_position_m: float = 0.0):
        super().__init__("UDL")
        self.intensity_kn_m = intensity_kn_m
        self.start_position_m = start_position_m
        self.end_position_m = end_position_m


@dataclass
class UVLLoadState(LoadState):
    start_intensity_kn_m: float = 0.0
    end_intensity_kn_m: float = 0.0
    start_position_m: float = 0.0
    end_position_m: float = 0.0

    def __init__(self, start_intensity_kn_m: float = 0.0, end_intensity_kn_m: float = 0.0,
                 start_position_m: float = 0.0, end_position_m: float = 0.0):
        super().__init__("UVL")
        self.start_intensity_kn_m = start_intensity_kn_m
        self.end_intensity_kn_m = end_intensity_kn_m
        self.start_position_m = start_position_m
        self.end_position_m = end_position_m
