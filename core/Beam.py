"""Backward compatibility module for core.Beam."""

from core.beam import Beam, BeamEquilibriumState, BeamForceCache, InternalForceResult
from core.integration import (
    RombergIntegrator,
    SimpsonIntegrator,
    romberg_integral,
    simpsonIntegral,
    simpson_one_third,
)
from core.loads import (
    CumulativeSamplePoint,
    Load,
    LoadContributionCache,
    LoadCumulativeMap,
    PartialLoadContribution,
    PointLoad,
    ReactionForce,
)
from core.sections import CircularBeam, IBeam, RectangularBeam
from core.types import BeamType, LoadFunction, LoadType, Point2D

__all__ = [
    "BeamType",
    "LoadType",
    "LoadFunction",
    "Point2D",
    "RombergIntegrator",
    "romberg_integral",
    "SimpsonIntegrator",
    "simpsonIntegral",
    "simpson_one_third",
    "ReactionForce",
    "PointLoad",
    "Load",
    "CumulativeSamplePoint",
    "LoadCumulativeMap",
    "PartialLoadContribution",
    "LoadContributionCache",
    "Beam",
    "BeamEquilibriumState",
    "InternalForceResult",
    "BeamForceCache",
    "RectangularBeam",
    "CircularBeam",
    "IBeam",
]