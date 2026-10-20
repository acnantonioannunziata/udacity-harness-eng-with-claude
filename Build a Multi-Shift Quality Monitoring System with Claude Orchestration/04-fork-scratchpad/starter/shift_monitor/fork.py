"""Layer 3 fork: copy hot state into an isolated working directory per hypothesis.

`fork_session` here is the application-side framing: the SDK / CLI primitive lives at
Layer 2; here we reproduce the semantics (shared baseline, isolated scratchpads,
no cross-contamination) using state-file copies.
"""

from __future__ import annotations

import shutil
from collections.abc import Iterable
from pathlib import Path

from .scratchpad import Scratchpad


def fork_for_hypothesis(
    base_hot_state_path: Path,
    hypothesis_id: str,
    forks_root: Path,
) -> Path:
    fork_dir = forks_root / hypothesis_id
    fork_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(base_hot_state_path, fork_dir / "hot_state.json")
    return fork_dir


def merge_findings(scratchpad_paths: Iterable[Path], main_scratchpad: Path) -> None:
    destination = Scratchpad(main_scratchpad)

    for scratchpad_path in scratchpad_paths:
        if not scratchpad_path.exists():
            continue

        source = Scratchpad(scratchpad_path)
        for entry in source.read():
            destination.append(entry)
