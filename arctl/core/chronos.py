"""
Chronos Module v1.0

Temporal synchronization for discrete models in continuous time.

Modern LLMs suffer from "Future Shock": they deny events after their training cutoff.
Chronos solves this not by retraining, but by explicit TEMPORAL ALIGNMENT.

The module classifies time gaps and generates context injection signals to keep the model
aware of reality:
  - SYNC (< 1 min): Immediate continuity, high context retention
  - LAG (1 min - 24h): User lived through time the model didn't see
  - GAP (> 24h): Significant reality shift, recommend context reset

Philosophy:
    "The model is frozen in time. We are not. Tell it that it lives now."

Usage:
    from arctl.core.chronos import Chronos
    
    time_state, context_note = Chronos.sync(prev_time, current_time)
    
    if time_state == TimeState.LAG:
        # Inject context_note into the system prompt
        full_prompt = f"{context_note}\n\nUser query: {user_input}"
"""

from datetime import datetime
from typing import Tuple
from .states import TimeState

class Chronos:
    """
    Handles temporal synchronization.
    Prevents 'Future Shock' by explicitly stating the current reality anchor.
    """
    
    @staticmethod
    def sync(prev_ts: float, current_ts: float) -> Tuple[TimeState, str]:
        """
        Calculate time gap and generate context update signal.
        
        Classifies the temporal relationship between two timestamps and produces
        a synchronization note for context injection when needed.
        
        Args:
            prev_ts: Previous interaction timestamp (wall-clock seconds)
            current_ts: Current timestamp (wall-clock seconds)
        
        Returns:
            Tuple of:
            - TimeState: Classification (SYNC, LAG, or GAP)
            - str: Context synchronization note (empty for SYNC, non-empty for LAG/GAP)
        
        Time Thresholds:
            - SYNC: delta < 60 seconds (immediate flow, no context injection needed)
            - LAG: 60s <= delta < 86400s (24+ hour gap, suggest context reset)
            - GAP: delta >= 86400s (full day gap, energy restoration triggered)
        
        Example:
            >>> state, note = Chronos.sync(100.0, 110.0)
            >>> state == TimeState.SYNC
            True
            >>> note == ""
            True
            
            >>> state, note = Chronos.sync(100.0, 3700.0)
            >>> state == TimeState.LAG
            True
            >>> "[SYSTEM]: TEMPORAL SYNC" in note
            True
        
        Notes:
            - Assumes prev_ts <= current_ts (monotonic time)
            - SYNC returns empty note to avoid noise in the context
            - LAG/GAP return detailed notes for prompt injection
        """
        delta = current_ts - prev_ts
        
        # 1. Determine the Gap Type (Physics)
        if delta < 60:
            state = TimeState.SYNC
        elif delta < 86400:
            state = TimeState.LAG
        else:
            state = TimeState.GAP

        # 2. Generate the Cursor Update Signal (Semantics)
        current_date = datetime.fromtimestamp(current_ts).strftime("%Y-%m-%d %H:%M")
        
        if state == TimeState.SYNC:
            # Immediate flow. No need to remind the date every second.
            note = ""
        else:
            # Gap detected. Update the internal clock.
            # Explicitly tells the model that time has passed.
            note = (
                f"[SYSTEM]: TEMPORAL SYNC.\n"
                f"Previous Interaction: {int(delta/60)} min ago.\n"
                f"Current Reality Anchor: {current_date}.\n"
                f"NOTE: Treat all documents/events prior to {current_date} as PAST or PRESENT."
            )
            
        return state, note