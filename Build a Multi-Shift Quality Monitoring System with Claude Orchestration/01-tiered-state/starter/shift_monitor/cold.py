"""Cold tier: monthly Markdown summaries derived deterministically from the warm tier."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .warm import WarmStore


@dataclass
class ColdStore:
    store: WarmStore
    cold_dir: Path

    def write_monthly_summary(self, year: int, month: int) -> Path:
        month_key = f"{year:04d}-{month:02d}"
        output_path = self.cold_dir / f"{month_key}.md"
        total = self.store.count_for_month(year, month)
        top_components = self.store.top_components_for_month(year, month, n=3)

        lines = [
            f"# {month_key}",
            "",
            f"Total defects: {total}",
            "",
            "## Top components",
        ]
        lines.extend(
            f"- {component}: {count} defects"
            for component, count in top_components
        )

        self.cold_dir.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path
