"""
Chronos — temporal synchronization for discrete models in continuous time.

Protocol (T-SPIRAL_ALIGNMENT): time as geometry; 8 layers
YEARS | MONTHS | WEEKS | DAYS | HOURS | MINUTES | SECONDS | MILLISECONDS.
State logic: coordinate <= CURSOR (NOW) → FROZEN_STATE [READ_ONLY];
coordinate > CURSOR → PROBABILISTIC_FIELD [READ_WRITE]. NOW is the
phase-transition boundary. This module implements that logic in Python
(time_to_layers, temporal_state_at, Chronos.sync).

Usage:
    from arctl.core.chronos import Chronos, temporal_state_at, time_to_layers

    time_state, context_note = Chronos.sync(prev_time, current_time)
    state = temporal_state_at(coordinate=100.0, cursor=200.0)
    layers = time_to_layers(1700000000.0)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .states import TimeState

# Thresholds (seconds)
SYNC_THRESHOLD = 60
GAP_THRESHOLD = 86400  # 24 hours


# --- 8 layers: TIME_AS_GEOMETRY ---
LAYERS = ("YEARS", "MONTHS", "WEEKS", "DAYS", "HOURS", "MINUTES", "SECONDS", "MILLISECONDS")


@dataclass(frozen=True)
class TimeLayers:
    """Decomposition of a timestamp into 8 layers (years down to milliseconds)."""

    years: int
    months: int
    weeks: int
    days: int
    hours: int
    minutes: int
    seconds: int
    milliseconds: int

    def to_dict(self) -> dict[str, int]:
        return {
            "YEARS": self.years,
            "MONTHS": self.months,
            "WEEKS": self.weeks,
            "DAYS": self.days,
            "HOURS": self.hours,
            "MINUTES": self.minutes,
            "SECONDS": self.seconds,
            "MILLISECONDS": self.milliseconds,
        }


def time_to_layers(ts: float) -> TimeLayers:
    """Convert Unix timestamp to 8-layer decomposition (UTC)."""
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    iso = dt.isocalendar()
    ms = int((ts % 1) * 1000)
    return TimeLayers(
        years=dt.year,
        months=dt.month,
        weeks=iso[1],
        days=dt.day,
        hours=dt.hour,
        minutes=dt.minute,
        seconds=dt.second,
        milliseconds=ms,
    )


class TemporalCoordinateState(Enum):
    """State of a time coordinate relative to the cursor (NOW)."""

    FROZEN_STATE = "READ_ONLY"
    PROBABILISTIC_FIELD = "READ_WRITE"


def temporal_state_at(coordinate: float, cursor: float) -> TemporalCoordinateState:
    """Past (coordinate <= cursor) is FROZEN_STATE; future (coordinate > cursor) is PROBABILISTIC_FIELD."""
    if coordinate <= cursor:
        return TemporalCoordinateState.FROZEN_STATE
    return TemporalCoordinateState.PROBABILISTIC_FIELD


def _gap_state(delta: float) -> TimeState:
    if delta < SYNC_THRESHOLD:
        return TimeState.SYNC
    if delta < GAP_THRESHOLD:
        return TimeState.LAG
    return TimeState.GAP


def _format_duration_ago(delta: float) -> str:
    if delta < 60:
        return f"{int(delta)} sec ago"
    if delta < 3600:
        return f"{int(delta / 60)} min ago"
    if delta < 86400:
        return f"{int(delta / 3600)} h ago"
    return f"{int(delta / 86400)} days ago"


class Chronos:
    """Temporal sync: classifies gaps (SYNC/LAG/GAP) and builds context notes using 8-layer time."""

    @staticmethod
    def sync(prev_ts: float, current_ts: float) -> tuple[TimeState, str]:
        """
        Classify time gap and generate context note. Uses current_ts as CURSOR (NOW).
        Returns (TimeState, note); note is empty for SYNC.
        """
        delta = max(0.0, current_ts - prev_ts)
        state = _gap_state(delta)

        if state == TimeState.SYNC:
            return state, ""

        cursor_layers = time_to_layers(current_ts)
        current_date = datetime.fromtimestamp(current_ts, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M"
        )
        ago = _format_duration_ago(delta)

        note = (
            f"[SYSTEM]: TEMPORAL SYNC.\n"
            f"Previous: {ago}.\n"
            f"CURSOR (NOW): {current_date} UTC | "
            f"layers={cursor_layers.years}-{cursor_layers.months:02d}-{cursor_layers.days:02d} "
            f"{cursor_layers.hours:02d}:{cursor_layers.minutes:02d}:{cursor_layers.seconds:02d}.{cursor_layers.milliseconds:03d}\n"
            f"STATE: t<=NOW -> FROZEN_STATE [READ_ONLY]; t>NOW -> PROBABILISTIC_FIELD [READ_WRITE].\n"
            f"Treat events before {current_date} as PAST or PRESENT."
        )
        return state, note
