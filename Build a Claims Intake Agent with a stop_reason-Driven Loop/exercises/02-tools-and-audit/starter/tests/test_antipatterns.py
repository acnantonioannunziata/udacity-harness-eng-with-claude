"""Anti-pattern audit.

Verifies, by static AST analysis, that the agentic loop does NOT:
- use string-membership tests against text content to drive control flow
- use an integer-literal iteration cap as its primary stopping mechanism
- omit reference to `stop_reason` as the loop-breaking signal

And that the package broadly does not branch on `claim_type` equality
outside of the tool-schema definitions and the cost-estimate module.

Each test parses the relevant file with `ast` and walks the tree. There are
no runtime imports of claims_intake here — the audit is static, so it works
even if loop.py / tools.py do not run end-to-end.
"""

from __future__ import annotations

import ast
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "claims_intake"
LOOP_PY = PKG / "loop.py"


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


# ---------------------------------------------------------------------------
# Anti-pattern 1 — no string-membership tests against assistant text in the loop
# ---------------------------------------------------------------------------
def test_no_string_membership_against_text_in_loop() -> None:
    tree = _parse(LOOP_PY)
    offenders = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue

        has_in_operator = any(isinstance(op, ast.In) for op in node.ops)
        left_is_string = (
            isinstance(node.left, ast.Constant)
            and isinstance(node.left.value, str)
        )

        if has_in_operator and left_is_string:
            offenders.append(ast.unparse(node))

    assert not offenders, (
        "Found string-membership tests in loop.py: "
        + "; ".join(offenders)
    )


# ---------------------------------------------------------------------------
# Anti-pattern 2 — no integer-literal iteration cap as the primary stop mechanism
# ---------------------------------------------------------------------------
def test_no_integer_literal_iteration_cap_in_loop() -> None:
    tree = _parse(LOOP_PY)
    offenders = []

    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            iterator = node.iter

            is_range_call = (
                isinstance(iterator, ast.Call)
                and isinstance(iterator.func, ast.Name)
                and iterator.func.id == "range"
            )

            if is_range_call:
                has_integer_argument = any(
                    isinstance(arg, ast.Constant)
                    and isinstance(arg.value, int)
                    and not isinstance(arg.value, bool)
                    for arg in iterator.args
                )

                if has_integer_argument:
                    offenders.append(ast.unparse(node.iter))

        if isinstance(node, ast.While) and isinstance(node.test, ast.Compare):
            has_integer_on_right = any(
                isinstance(comparator, ast.Constant)
                and isinstance(comparator.value, int)
                and not isinstance(comparator.value, bool)
                for comparator in node.test.comparators
            )

            if has_integer_on_right:
                offenders.append(ast.unparse(node.test))

    assert not offenders, (
        "Found an integer-literal iteration cap in loop.py: "
        + "; ".join(offenders)
        + ". Use a Budget instead."
    )


# ---------------------------------------------------------------------------
# Positive evidence — stop_reason is the value that breaks the while loop
# ---------------------------------------------------------------------------
def test_stop_reason_is_loop_control() -> None:
    tree = _parse(LOOP_PY)

    has_stop_reason_reference = any(
        (
            isinstance(node, ast.Attribute)
            and node.attr == "stop_reason"
        )
        or (
            isinstance(node, ast.Name)
            and node.id == "stop_reason"
        )
        for node in ast.walk(tree)
    )

    assert has_stop_reason_reference, (
        "loop.py must reference stop_reason as the loop-control signal"
    )

    while_nodes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.While)
    ]

    loop_exits_on_stop_reason = False

    for while_node in while_nodes:
        body_text = "\n".join(
            ast.unparse(statement)
            for statement in while_node.body
        )

        mentions_stop_reason = "stop_reason" in body_text
        has_return_or_raise = any(
            isinstance(node, (ast.Return, ast.Raise))
            for statement in while_node.body
            for node in ast.walk(statement)
        )

        if mentions_stop_reason and has_return_or_raise:
            loop_exits_on_stop_reason = True
            break

    assert loop_exits_on_stop_reason, (
        "A while loop must use stop_reason and exit through return or raise"
    )


# ---------------------------------------------------------------------------
# Decision-tree-in-Python — no `if claim_type == "..."` branches in the package
# ---------------------------------------------------------------------------
def test_no_claim_type_equality_branching_in_package() -> None:
    """Decision logic about claim type lives in the model, not in Python."""
    offenders = []
    exempt_files = {"tools.py", "pricing.py", "__init__.py"}

    for path in PKG.rglob("*.py"):
        if path.name in exempt_files:
            continue

        tree = _parse(path)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue

            has_equality_operator = any(
                isinstance(operator, ast.Eq)
                for operator in node.ops
            )

            if not has_equality_operator:
                continue

            left_is_claim_type = (
                isinstance(node.left, ast.Name)
                and node.left.id == "claim_type"
            ) or (
                isinstance(node.left, ast.Attribute)
                and node.left.attr == "claim_type"
            )

            if not left_is_claim_type:
                continue

            compared_to_string = any(
                isinstance(comparator, ast.Constant)
                and isinstance(comparator.value, str)
                for comparator in node.comparators
            )

            if compared_to_string:
                relative_path = path.relative_to(PKG)
                offenders.append(
                    f"{relative_path}:{node.lineno}: {ast.unparse(node)}"
                )

    assert not offenders, (
        "Found claim_type equality branching in the package: "
        + "; ".join(offenders)
        + ". Move the decision into the model via tool calls."
    )
