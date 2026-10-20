---
description: Review a pull request, diff, or file against team standards and repository conventions
argument-hint: Pass a PR reference, git diff range, commit range, or file path to review
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(git show:*)
  - Bash(git status:*)
  - Bash(gh pr view:*)
  - Bash(gh pr checks:*)
  - Bash(gh pr diff:*)
---

# /review — team PR review

You are reviewing the diff identified by `$ARGUMENTS` against this repository's conventions. Apply the path-scoped rules in `.claude/rules/` (they auto-load based on the files touched) and the shared standards in `.claude/standards/`.

## Phase 1 — Interview pattern

Before reporting findings, determine whether the author's intent is clear. If the change is ambiguous, ask clarifying questions first rather than producing findings immediately.

Interview before reporting when any of the following conditions exist:

- Dependency changes in files such as `package.json`, `package-lock.json`, `pyproject.toml`, or lockfiles where the reason for the change is unclear.
- Public API response shape changes that may be intentional contract changes.
- Database schema or column changes where migration intent is not obvious.
- Refactors that modify production code without corresponding test changes.
- Changes that touch multiple surfaces simultaneously such as `src/api/`, `src/components/`, and `src/db/`.
- Large file moves or renames where behavior may be unchanged.

Example interview questions:

- "Was this API response change intended to be backward compatible?"
- "Is test coverage already provided elsewhere for this refactor?"
- "Is this schema change accompanied by a migration outside the current diff?"

Only proceed to findings after receiving clarification or when intent is already clear from the diff.

## Phase 2 — Review criteria

### Must report

Report findings for:

- Logic errors.
- Missing `await` in async code paths.
- Race conditions and concurrency hazards.
- Off-by-one errors and boundary-condition bugs.
- Raw SQL using user-controlled input.
- Missing authentication or authorization checks.
- Secrets, credentials, or tokens committed to source control.
- Use of `dangerouslySetInnerHTML`.
- Violations of path-scoped rules in `.claude/rules/`.
- Violations of shared standards in `.claude/standards/`.
- Breaking API changes.
- Breaking database schema changes.
- Unsafe migrations or migrations lacking rollback consideration.
- Data-loss risks.

### Skip

Do not report findings for:

- Minor formatting issues handled automatically by Prettier, ESLint, or equivalent tooling.
- Naming preferences when the existing name is already clear and accurate.
- Personal stylistic preferences not documented in project rules or standards.
- TODO comments that already reference tracked tickets.
- Alternative implementations that are functionally equivalent and compliant with standards.
- Subjective code-style disagreements lacking maintainability, correctness, security, or convention impact.

## Phase 3 — Bundling: interacting vs. independent findings

Bundle interacting findings into a single report when they affect the same code path or require the same corrective change.

Examples of interacting findings:

- Missing `await` plus missing transaction handling in the same function.
- Incorrect operation ordering combined with missing error handling in the same workflow.
- Multiple defects that require modifying the same block of code.

Report independent findings separately when they occur in different files, different functions, or require unrelated fixes.

Heuristic:

> If fixing finding A changes the code finding B references, the findings are interacting and should be bundled together.

Otherwise they should be reported as separate findings.

## Phase 4 — Output format

For each finding, produce:

```
[severity] path/to/file.ts:line
finding: <one-sentence description>
fix: <one-sentence recommendation>
```

Severity is `bug` | `security` | `convention` | `breaking`. End with a one-line verdict: `approve`, `comment`, or `request-changes`.

## Examples

### Example 1 — Independent findings

Input diff:

```diff
--- a/src/api/orders/handler.ts
+++ b/src/api/orders/handler.ts
@@
-return ApiError.notFound()
+return { status: 404 }

@@
-const order = await repository.get(id)
+const order = await db.query("select * from orders")
```

Output:

```text
[convention] src/api/orders/handler.ts:12
finding: Handler returns a custom response shape instead of the standard error contract.
fix: Return the approved ApiError response type.

[convention] src/api/orders/handler.ts:18
finding: API handler bypasses the repository layer and accesses the database directly.
fix: Move data access into a repository under src/db/.

request-changes
```

### Example 2 — Interacting findings

Input diff:

```diff
--- a/src/api/refunds/refundOrder.ts
+++ b/src/api/refunds/refundOrder.ts
@@
-paymentService.refund(order)
-db.save(refund)
+paymentService.refund(order)
+db.save(refund)
```

Output:

```text
[bug] src/api/refunds/refundOrder.ts:20
finding: The refund workflow contains interacting defects including missing awaits, missing transaction protection, and unsafe ordering between payment processing and database writes.
fix: Execute refund and persistence operations inside a transaction and await each async step in the correct order.

request-changes
```

## Notes

- This command is project-scoped (`.claude/commands/review.md`) so everyone on the team gets the same review. If you want to layer personal preferences (e.g. a stricter accessibility check on your own PRs), put a `~/.claude/commands/review-strict.md` in your home directory — it will not affect teammates.
- If a finding requires running code or modifying files to verify, ask the author to run a specific check rather than attempting it from the review session. This command's `allowed-tools` are read-only by design.