---
name: deploy-check
description: "Run the team's read-only pre-deployment validation checklist in an isolated fork"
context: fork
argument-hint: "[target branch or PR] (defaults to main)"
allowed-tools: ["Read", "Grep", "Glob", "Bash(git status:*)", "Bash(git diff:*)", "Bash(git log:*)", "Bash(git show:*)", "Bash(gh pr view:*)", "Bash(gh pr checks:*)"]
---

# /deploy-check

Runs the team's pre-deployment validation checklist against the current working tree and the branch you're about to ship. Read-only by design: this skill never modifies files, never pushes, and never deploys. It returns a single structured summary so the calling session can decide whether to proceed.

## Why this is a skill (not a CLAUDE.md addition)

A skill is appropriate for work that is on-demand, forked, and task-specific. A deploy check is needed only immediately before deployment, and it produces verbose intermediate output from file enumeration, diff inspection, and CI-status checks that has no lasting value after the verdict is known.

`CLAUDE.md` is for always-loaded, universal guidance that must be present in every session, such as co-located test conventions and the requirement to use `ApiError` for validation failures. Putting deploy-check mechanics there would consume context during unrelated work.

Rule of thumb: on-demand, forked, task-specific work belongs in a skill; always-loaded, universal guidance belongs in `CLAUDE.md`.

## Why `context: fork`

`context: fork` keeps verbose intermediate output out of the main session and main conversation. The deploy check walks the working tree, inspects diffs, and performs several enumeration passes, but none of those raw details is useful to the calling session once the pass-or-fail status is known. Only the structured summary returns to the main conversation. `context: fork` is a Claude Code product feature at the skill-invocation layer and is conceptually analogous to the Architect's Playbook *Branching Reality* pattern, which describes session-level forking through `fork_session`.

## Checks

Run all three checks. Each check produces a pass-or-fail verdict. If any check fails, the overall verdict is **fail**.

### Check 1: Clean working tree

- **Detect:** Run `git status --porcelain` and inspect whether it returns any tracked or untracked changes.
- **Pass:** The command returns no output, meaning the working tree is clean.
- **Fail:** The command returns one or more lines. Report the affected paths in a concise detail such as `working tree contains uncommitted changes`; do not return the complete raw status output.

### Check 2: Migrations match repository changes

- **Detect:** Run `git diff --name-only <target>...HEAD` and `git diff <target>...HEAD -- src/api src/db`. Identify new or changed repository/database usage, then verify that required schema changes are accompanied by a migration file in the same branch.
- **Pass:** Database-affecting code changes either require no schema migration or include the corresponding migration file.
- **Fail:** Code depends on a new table, column, constraint, or index without a matching migration. Report the relevant code path and the missing migration requirement in the detail.

### Check 3: Required CI checks are green

- **Detect:** Run `gh pr view --json statusCheckRollup` or `gh pr checks` for the open pull request associated with the current branch.
- **Pass:** Every required check reports `SUCCESS` or an equivalent passing state, with no required check pending or failing.
- **Fail:** Any required check is failed, cancelled, timed out, or still pending. Report the names and states of only the non-passing required checks in the detail; do not include full CI logs.

## Output format

Return exactly this shape to the main session:

```
verdict: pass | fail
checks:
  - name: <check-name>
    status: pass | fail
    detail: <one line or empty>
```

Do not include the raw `git status`, raw diff hunks, or full check logs in the returned summary. Those stay in the fork. If the author wants to investigate a failed check, they can re-invoke the skill targeting that single check or run the underlying command themselves.

## Personalization

This is a project-scoped skill stored at `.claude/skills/deploy-check/`, so every teammate receives the same deployment checks through version control. A teammate who wants a stricter personal variant, for example one that fails when a diff exceeds 500 lines without a sufficiently detailed PR description, can create `~/.claude/skills/deploy-check-strict/SKILL.md` with a different skill name. That personal variant is not committed to the repository and does not affect teammates.

## What this skill deliberately does not do

- It never pushes, deploys, or runs migrations. The `allowed-tools` allowlist is read-only by construction; even if a future maintainer adds `Write` here, the team's `/review` command should catch the change.
- It does not run the test suite. Tests have their own pre-merge gate in CI; duplicating that here would slow every deploy check without adding signal.
- It does not check for secrets in code. That's the job of the `gitleaks` pre-commit hook, which fails the commit, not the deploy.
