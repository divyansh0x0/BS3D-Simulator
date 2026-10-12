"""Backward compatibility module for core.Beam."""

from core.beam import Beam, BeamEquilibriumState
from core.integration import SimpsonIntegrator, simpsonIntegral, simpson_one_third
from core.loads import Load, LoadProfileMap, PointLoad, ReactionForce
from core.sections import CircularBeam, IBeam, RectangularBeam
from core.types import BeamType, LoadFunction, LoadType, Point2D

__all__ = [
    "BeamType",
    "LoadType",
    "LoadFunction",
    "Point2D",
    "SimpsonIntegrator",
    "simpsonIntegral",
    "simpson_one_third",
    "ReactionForce",
    "PointLoad",
    "Load",
    "LoadProfileMap",
    "Beam",
    "BeamEquilibriumState",
    "RectangularBeam",
    "CircularBeam",
    "IBeam",
]