from enum import Enum
from typing import NamedTuple, Optional
from dataclasses import dataclass

class OperationalMode(Enum):
    STANDARD = "STD"
    EMERGENCY = "EMG"
    COOLDOWN = "CDN"
    FALLBACK = "FBK"

class TimeState(Enum):
    SYNC = "SYNC"       # < 1 min
    LAG = "LAG"         # > 1 min
    GAP = "GAP"         # > 24 hours

@dataclass(frozen=True)
class RawMetrics:
    entropy: float
    divergence: float
    repetition: float

class SamplingConfig(NamedTuple):
    temperature: float
    top_p: Optional[float] = None