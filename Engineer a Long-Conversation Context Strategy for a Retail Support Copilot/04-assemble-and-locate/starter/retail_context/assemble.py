"""Position-aware context assembly.

Layout (top to bottom):
  # Case Facts
  # Resolved: Refund inquiry
  # Resolved: Subscription cancellation
  # Active issue: Payment-method update

This places key findings at both context boundaries: Case Facts at the top and
the active turn-by-turn conversation at the bottom, next to the new user turn.
Resolved narrative occupies the lower-attention middle. Sections are exclusive,
with no interleaving.
"""

from __future__ import annotations

from dataclasses import dataclass

from retail_context.case_facts import CaseFacts
from retail_context.compressor import Compressed
from retail_context.tokens import count


RESOLVED_TITLES: dict[str, str] = {
    "refund": "# Resolved: Refund inquiry",
    "subscription": "# Resolved: Subscription cancellation",
}

ACTIVE_TITLES: dict[str, str] = {
    "payment_update": "# Active issue: Payment-method update",
}


@dataclass
class AssembledContext:
    markdown: str
    case_facts_block: str
    resolved_blocks: dict[str, str]
    active_block: str
    active_raw_text: str

    def section_tokens(self) -> dict[str, int]:
        sections = {
            "case_facts": count(self.case_facts_block),
        }

        for issue_id, block in self.resolved_blocks.items():
            sections[f"resolved_{issue_id}"] = count(block)

        sections["active"] = count(self.active_block)
        return sections

    def total_tokens(self) -> int:
        return count(self.markdown)


def build(case_facts: CaseFacts, compressed: Compressed) -> AssembledContext:
    case_facts_block = case_facts.to_markdown().rstrip("\n") + "\n"

    resolved_blocks: dict[str, str] = {}

    for issue_id in ("refund", "subscription"):
        if issue_id not in compressed.summaries:
            raise KeyError(
                f"Missing resolved summary for issue_id: {issue_id}"
            )

        summary_text = compressed.summaries[issue_id].text.strip()

        resolved_blocks[issue_id] = (
            f"{RESOLVED_TITLES[issue_id]}\n\n"
            f"{summary_text}\n"
        )

    active_title = ACTIVE_TITLES.get(
        compressed.active_issue_id,
        f"# Active issue: {compressed.active_issue_id}",
    )

    active_block = (
        f"{active_title}\n\n"
        f"{compressed.active_text}\n"
    )

    markdown = (
        case_facts_block
        + "\n"
        + resolved_blocks["refund"]
        + "\n"
        + resolved_blocks["subscription"]
        + "\n"
        + active_block
    )

    return AssembledContext(
        markdown=markdown,
        case_facts_block=case_facts_block,
        resolved_blocks=resolved_blocks,
        active_block=active_block,
        active_raw_text=compressed.active_text,
    )