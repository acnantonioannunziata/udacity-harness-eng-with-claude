# E-Commerce Platform — Shared Claude Code Conventions

This file is the **project-level** entry point for the e-commerce monorepo. Every teammate's Claude session loads it automatically.

## Scope: what belongs here vs. elsewhere

| Scope | Location | Shared with team? | Typical contents |
|---------|----------|------------------|------------------|
| Project-level | `./CLAUDE.md`, `.claude/` | Yes, version controlled | Repository standards, workflows, coding conventions, commands, skills |
| User-level | `~/.claude/` | No, not shared through version control | Personal preferences such as preferred commit message style, editor habits, response verbosity |
| Directory-level | `subdir/CLAUDE.md` | Yes, if committed | Rules that apply only to a specific area of the repository such as a frontend app, API service, or migration directory |

The team keeps shared conventions at project and directory scope so everyone receives the same guidance, while user-level settings remain personal and do not affect teammates.

## Shared standards (modular via @-imports)

The actual conventions live in focused files so this entry point stays scannable:

@.claude/standards/frontend.md
@.claude/standards/api.md
@.claude/standards/database.md
@.claude/standards/testing.md

Path-scoped rules in [.claude/rules/](.claude/rules/) layer on top of these standards and activate only when Claude is editing matching files (React components, API handlers, test files).

## Repository layout

```text
src/components/   React components (functional + hooks)
src/pages/        Top-level routes
src/api/          Node.js API handlers
src/db/           PostgreSQL repository-pattern modules
```

Tests are co-located: `Foo.tsx` lives next to `Foo.test.tsx`.

## Troubleshooting

If a CLAUDE.md instruction is not being followed, run `/memory` to see exactly which configuration files were loaded into the current session.

## Team workflows

- `/review <pr-ref>` — codified PR review checklist. (You will author this in Exercise 2.)
- `/deploy-check` — read-only pre-deployment validation. (You will author this in Exercise 3.)

For decisions about when to use plan mode vs. direct execution on this codebase, you will produce a team decision doc in Exercise 4.