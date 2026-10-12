from dataclasses import dataclass


@dataclass
class SupportState:
    support_type: str  # e.g., "Pin", "Roller"
    position: float
