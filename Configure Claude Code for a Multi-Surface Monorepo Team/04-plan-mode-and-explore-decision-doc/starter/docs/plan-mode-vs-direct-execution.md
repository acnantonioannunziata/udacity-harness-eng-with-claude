> "Software engineering is increasingly moving toward planning and reviewing rather than immediately writing code. Investing effort up front to understand the change reduces mistakes, aligns implementation with intent, and helps prevent costly rework later." — Knight-Webb, *SWE Is Becoming Plan and Review* (Module 8 Anchor Talk)

This doc walks four concrete decisions against our codebase: one plan-mode example, one direct-execution example, one Explore-subagent example, and one combined-workflow example.

---

## 1. Plan-mode example

A good plan-mode candidate is extracting a shared cart-loading pattern from:

- `src/components/Cart/Cart.tsx`
- `src/components/Checkout/Checkout.tsx`
- `src/components/MiniCart/MiniCart.tsx`

All three components currently fetch and manage cart state independently. Before making changes, Claude should investigate how each component handles loading, caching, error states, and refresh behavior, then propose a shared hook implementation in a new hooks module.

This is a plan-mode task because it spans multiple files, affects architecture, has multiple valid implementation approaches, and introduces a new shared abstraction. The team should review the proposed design before any edits occur.

Following the Knight-Webb principle, planning first helps prevent costly rework. Discovering an incorrect hook contract after editing three components is significantly more expensive than reviewing the plan beforehand.

---
## 2. Direct-execution example

A direct-execution task is adding a `min: 0` validation check inside the quantity-validation function in `src/api/orders/handler.ts`.

This change affects one function only. The change is well-scoped, the expected behavior is obvious, and there are no architectural decisions to make.

Before invoking Claude, the author already knows what the patch should be: add a minimum-value validation that rejects negative quantities.

Because this is a change to one function and the resulting diff is easy to predict, direct execution is the appropriate choice. Planning would add overhead without improving the outcome.

---

## 3. Explore-subagent example

Suppose we need to find every place that calls `processRefund`.

Rather than filling the main conversation with search results, an Explore subagent performs the investigation and inventories the call sites across:

- `src/api/orders/refund.ts`
- `src/api/billing/issue.ts`
- `src/services/payment.ts`

The Explore subagent is used to isolate verbose discovery output from the main conversation. Instead of flooding the main session with call-site searches, grep results, and intermediate notes, the subagent performs the investigation independently and returns only a concise summary.

The Explore subagent writes its findings into a scratchpad file such as `tmp/refund-callsites.md`. This follows the scratchpad pattern from the Architect's Playbook: discovery notes are preserved outside the main conversation and survive context-window limits.

Only the summarized inventory is returned to the main session, while the verbose discovery output remains isolated inside the exploration workflow.

The calling session receives only a concise summary of what was discovered. The detailed exploration remains isolated, preserving context and reducing noise.

This is the correct pattern whenever the intermediate investigation is much larger than the final answer.

---

## 4. Combined workflow — plan mode for investigation, then direct execution

Consider renaming `ordersRepo.findById` to `ordersRepo.getById` in `src/db/orders.ts` to align with the team's repository naming convention.

This task combines plan mode for investigation with direct execution for implementation.

Step 1 — Plan mode investigates and proposes.

First determine where `findById` is referenced. The investigation must answer questions such as:

- Which files call `findById`?
- Are any references indirect or dynamically constructed?
- Are there compatibility concerns?

The output is a proposed rename plan and a validated call-site inventory.

Step 2 — Human approval.

The developer reviews the investigation results and approves the proposed rename strategy.

Step 3 — Direct execution.

Once the call-site inventory is known, the refactor becomes mechanical. Claude updates the implementation, renames call sites, and runs the relevant tests.

The investigation phase requires planning. The implementation phase is predictable execution. This workflow demonstrates that plan mode and direct execution are complementary rather than mutually exclusive.