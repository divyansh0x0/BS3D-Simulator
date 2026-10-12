"""Backward compatibility module for frontend.StateManager."""

from frontend.models import (
    BeamDimensions,
    CircularDimensions,
    IBeamDimensions,
    LoadState,
    MaterialType,
    PointLoadState,
    RectangularDimensions,
    SupportState,
    UDLLoadState,
    UVLLoadState,
)
from frontend.state_manager import AnalysisConfig, DiagramDataMap, StateManager

__all__ = [
    "BeamDimensions",
    "RectangularDimensions",
    "CircularDimensions",
    "IBeamDimensions",
    "SupportState",
    "LoadState",
    "PointLoadState",
    "UDLLoadState",
    "UVLLoadState",
    "MaterialType",
    "StateManager",
    "AnalysisConfig",
    "DiagramDataMap",
]
