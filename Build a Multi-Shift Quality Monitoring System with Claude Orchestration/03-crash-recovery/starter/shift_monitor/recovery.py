"""Resume-vs-fresh decision logic for crash recovery.

The 30-minute threshold is about one-sixteenth of an 8-hour shift cycle: a
resume inside this window is still operating on the same shift's working set;
anything older is treated as a stale partial that should restart from scratch
with previously captured findings available as context.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from .manifest import ManifestState

# About one-sixteenth of an 8-hour shift. Incomplete work at or below this age
# still belongs to the same active working set and can safely be resumed.
STALE_RESUME_THRESHOLD_MINUTES = 30

Decision = Literal["resume", "fresh"]


def decide(state: ManifestState, now: datetime) -> Decision:
    if not state.steps:
        return "fresh"

    if state.complete:
        return "fresh"

    age = now - state.steps[-1].ts
    threshold = timedelta(minutes=STALE_RESUME_THRESHOLD_MINUTES)
    return "resume" if age <= threshold else "fresh"
