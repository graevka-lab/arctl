"""
Chronos Module v1.0
Synchronizes the discrete Model Cursor with the continuous User Cursor.
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
        Calculates the time gap and generates a context update signal.
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