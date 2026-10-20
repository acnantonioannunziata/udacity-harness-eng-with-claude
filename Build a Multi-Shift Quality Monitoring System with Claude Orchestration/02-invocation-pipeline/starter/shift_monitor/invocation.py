"""Three invocation shapes.

thin     - prompt only.
rich     - hot state + new defects.
resumed  - prior partial findings + new defects since the last manifest step.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from .state import HotState

InvocationShape = Literal["thin", "rich", "resumed"]


@dataclass(frozen=True)
class Invocation:
    shape: InvocationShape
    prompt: str


def thin(prompt: str) -> Invocation:
    return Invocation(shape="thin", prompt=prompt)


def rich(
    role: str, hot_state: HotState, new_defects: Sequence[Mapping[str, Any]]
) -> Invocation:
    lines = [
        f"You are the on-call {role} for Northridge Plant 3.",
        "",
        "## Current hot state",
        f"- recent_defect_hashes: {json.dumps(hot_state.recent_defect_hashes)}",
        f"- current_shift_summary: {hot_state.current_shift_summary}",
        f"- active_alerts: {json.dumps(hot_state.active_alerts)}",
        f"- threshold_statuses: {json.dumps(hot_state.threshold_statuses, sort_keys=True)}",
        "",
        "## New defects since last shift",
    ]

    if new_defects:
        for index, defect in enumerate(new_defects, start=1):
            lines.extend(
                [
                    f"### Defect {index}",
                    f"- id: {defect.get('id', '')}",
                    f"- ts: {defect.get('ts', '')}",
                    f"- shift: {defect.get('shift', '')}",
                    f"- component: {defect.get('component', '')}",
                    f"- severity: {defect.get('severity', '')}",
                    f"- description: {defect.get('description', '')}",
                ]
            )
    else:
        lines.append("- (none)")

    lines.extend(
        [
            "",
            "Provide the following:",
            "1. Summary",
            "2. Findings",
            "3. Recommended actions",
            "4. Updated hot state proposal as a fenced JSON block containing "
            "current_shift_summary, active_alerts, and threshold_statuses.",
        ]
    )

    return Invocation(shape="rich", prompt="\n".join(lines))


def resumed(
    session_id: str,
    summary: str,
    latest_message: str,
    prior_steps: Sequence[Mapping[str, Any]],
    new_defects: Sequence[Mapping[str, Any]],
) -> Invocation:
    lines = [
        f"Resuming orchestration session {session_id}.",
        "",
        "## Prior partial findings",
    ]

    if prior_steps:
        for step in prior_steps:
            name = str(step.get("name", "unnamed"))
            payload_text = repr(step.get("payload", {}))
            if len(payload_text) > 200:
                payload_text = payload_text[:197] + "..."
            lines.append(f"- {name}: {payload_text}")
    else:
        lines.append("- (none)")

    lines.extend(
        [
            "",
            "## Prior summary",
            summary,
            "",
            "## New defects since last partial step",
        ]
    )

    if new_defects:
        for index, defect in enumerate(new_defects, start=1):
            lines.extend(
                [
                    f"### Defect {index}",
                    f"- id: {defect.get('id', '')}",
                    f"- ts: {defect.get('ts', '')}",
                    f"- component: {defect.get('component', '')}",
                    f"- severity: {defect.get('severity', '')}",
                    f"- description: {defect.get('description', '')}",
                ]
            )
    else:
        lines.append("- (none)")

    lines.extend(["", "## Latest instruction", latest_message])
    return Invocation(shape="resumed", prompt="\n".join(lines))
