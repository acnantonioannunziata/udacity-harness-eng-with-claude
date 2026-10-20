# Reflection Brief — Harness Engineering Capstone

**Name:** Antonio Annunziata  
**Date:** October 19, 2026

## Environment

- **Models / API:** `claude-haiku-4-5-20251001` was used for System 1. Systems 1 and 2 used the Claude API through the Vocareum environment.
- **OS / Python:** Linux 6.6.97+, Python 3.13.0.
- **Verification:** The four systems passed their test suites with 30, 30, 35, and 33 passing tests respectively.
- **Approximate API spend:** The System 1 run reported an estimated total cost of **$0.1313**. System 3 required no API call, and System 4 used a recorded response.

## Verification evidence

The submitted `evidence/` directory contains identifiable verification output for all four systems:

- **System 1 — Agentic loop:** `evidence/01_agentic_loop_pytest.txt` shows the project path, 30 collected tests, and `30 passed`.
- **System 2 — Context strategy:** `evidence/02_context_strategy_pytest.txt` shows the project path, 30 collected tests, and `30 passed`.
- **System 3 — Claude Code configuration:** `evidence/03_claude_code_validator_and_pytest.txt` shows validator output `OK` with exit code 0, followed by 35 collected tests and `35 passed`.
- **System 4 — Orchestration:** `evidence/04_orchestration_pytest.txt` shows the project path, 33 collected tests, and `33 passed`.

Each evidence file includes a system header or project path so that its output can be unambiguously associated with the corresponding system.

---

## Part 1 — Per-system

### System 1 — Agentic loop

#### 1. Loop control

Loop termination is decided in `claims_intake/loop.py`, inside the `run()` function. The harness continues the loop when `response.stop_reason == "tool_use"`. When `response.stop_reason == "end_turn"`, `run()` appends the final assistant content and returns a `FinalState`, terminating the loop. Any other stop reason raises `UnexpectedStopReason` rather than being silently accepted. This makes the model's structured response state, rather than its prose, the control signal for the loop.

This behavior is demonstrated by `runs/20261019_135042/traces/claim_07_tree_falls_on_car.jsonl`, where four turns with `stop_reason == "tool_use"` are followed by a final turn with `stop_reason == "end_turn"`, ending with `route_to_adjuster`.

#### 2. Anti-pattern

One anti-pattern checked by `tests/test_antipatterns.py` is controlling execution through string matching against model-generated prose. Such logic would be fragile because a harmless wording change could incorrectly stop the loop or route a claim. In my implementation, control flow depends on structured `stop_reason` values and tool calls. The System 1 test run completed with **30 passing tests**.

#### 3. Tool design

`route_to_adjuster` and `escalate_to_human` are overlapping terminal actions because both end automated claim processing, but they represent different outcomes. Their descriptions distinguish ordinary routing from cases that require human review, such as unresolved ambiguity, low confidence, policy disputes, or missing facts. Tool failures are returned as structured JSON with `is_error=true`, allowing the agent and harness to recognize an error explicitly. A plain-text error would be less reliable because it would require interpreting unstructured wording.

#### 4. Your numbers

The run `20261019_135042` processed eight claims and produced `summary.md`, eight trace files, queue records, and `escalations.jsonl`. A useful example is `claim_03_water_damage`, which completed in **5 turns**, required **1 clarification**, consumed **15,958 input tokens** and **982 output tokens**, and had an estimated cost of **$0.0209**. The complete run had an estimated cost of **$0.1313**. This claim cost more than the simpler four-turn claims because the harness needed an additional clarification turn before reaching a terminal outcome.

### System 2 — Context strategy

#### 5. The reduction

According to `runs/20261019-134745/budget.json` and the run output, the baseline transcript contained **38,708 tokens** and the assembled context contained **16,907 tokens**, producing a **56.32% reduction**. The active section accounted for **15,789 tokens**, the largest part of the assembled context. The active issue remained detailed because it represented the unresolved portion of the conversation, where exact information could still affect the final resolution.

#### 6. Summarize vs preserve

The strategy is status-based: resolved conversations are compressed, while the active conversation is preserved in detail. In run `20261019-134745`, `resolved_refund` used **488 tokens**, `resolved_subscription` used **444 tokens**, `case_facts` used **204 tokens**, and the active section used **15,789 tokens**. This allocation focuses the context budget on information that can still influence the current case while retaining compact summaries of already resolved work.

#### 7. Facts block

In `runs/20261019-134745/eval.jsonl`, all **6 of 6** evaluation questions passed. In `eval_control.jsonl`, Q6 failed when the case-facts block was removed, while Q1 still passed. Q6 required the exact structured status token `in_progress`. This result shows that the facts block preserves explicit structured state that the stripped control context could not reliably recover. The control therefore regressed on at least one evaluation, as required.

### System 3 — Claude Code config

#### 8. Path-scoped rules

The file `.claude/rules/tests.md` defines test-file glob patterns such as:

```yaml
paths:
  - "**/*.test.tsx"
  - "**/*.test.ts"
```

This is more flexible than placing all guidance in a directory-level `CLAUDE.md`, because the rules follow matching files wherever they appear in the repository. Path-scoped rules can also layer together. For example, a React test can receive both React-specific guidance and testing guidance when it matches both rule sets.

#### 9. Forked skill

The deploy-check skill declares `context: fork` and uses a restricted `allowed-tools` list containing read-oriented tools such as `Read`, `Grep`, `Glob`, and selected Git commands. The fork separates deployment investigation from the main session's working context. The read-only allowlist also reduces the risk that a validation task will modify repository state while inspecting the project.

#### 10. Scope

Project-level configuration includes `./CLAUDE.md` and the shared `.claude/` directory committed with the repository. User-level configuration belongs under `~/.claude/` and is appropriate for personal instructions, commands, and skills that should not be imposed on the whole team. Running `python -m ecommerce_team_config .` in the completed `starter` project returned **`OK`**, and the System 3 test suite completed with **35 passing tests**.

### System 4 — Orchestration

#### 11. Push work down

The warm database was seeded from `fixtures/defects.json`. Indexed retrieval is implemented by `WarmStore.defects_since()` in `shift_monitor/warm.py`, using a bounded SQL query that filters by timestamp, orders the records, and applies a limit. The recorded run used `--since 2026-04-01T00:00:00Z` and returned **17 new defects**. Filtering in SQLite keeps irrelevant historical rows out of the prompt and gives the model only the records required for the shift analysis.

#### 12. Crash recovery

`recovery.py` defines `STALE_RESUME_THRESHOLD_MINUTES = 30`. The recovery decision uses both completion state and age: a recent incomplete run can resume, while an old or completed run starts fresh. The tests cover the boundary around the 30-minute threshold and verify both resume and fresh-start behavior. This avoids treating stale partial reasoning as if it belonged to the current execution.

#### 13. Small state

The generated `data/hot_state.json` was **965 bytes**, well below the approximate **5 KB** budget. It contained 17 recent defect hashes, the current shift summary, three active alerts, and threshold statuses. The same run appended a **323-byte** record to `data/shift_scratchpad.jsonl`, identifying the 17 analyzed defects and the resulting conclusion. Keeping hot state small matters because the monitor is designed to operate over many shifts without allowing immediately loaded state to grow without bound.

---

## Part 2 — Synthesis

#### 14. Three layers

- **Model:** The model performs semantic work such as interpreting claim facts and selecting an appropriate terminal action. A concrete Model-layer artifact is `runs/20261019_135042/traces/claim_07_tree_falls_on_car.jsonl`, which records the model's sequence of tool requests and its final `route_to_adjuster` action.
- **Harness:** `claims_intake/loop.py`, structured tool schemas, validators, and state-size checks constrain how model output is executed and accepted.
- **Orchestration:** `shift_monitor/pipeline.py` coordinates indexed retrieval, model invocation, state updates, and scratchpad persistence across a shift run.

These layers address different failure modes. The model supplies judgment, the harness enforces local execution rules, and orchestration coordinates the wider workflow and durable state.

#### 15. Deterministic vs prompt

A deterministic behavior is the System 1 loop's use of structured `stop_reason` values and terminal tool calls. The harness decides whether to continue, stop, or reject an unexpected state without interpreting prose. A prompt-guided behavior is semantic claim classification, where the model must interpret the facts and choose an appropriate action. Deterministic mechanisms are better for safety boundaries and execution guarantees; prompt guidance is better for tasks requiring language understanding and contextual judgment. In run `20261019_135042`, six claims were routed and two were escalated, while the harness maintained the same structured execution protocol for every claim.

#### 16. Context, two faces

System 2 manages context within one long conversation. It reduced the transcript from **38,708** to **16,907 tokens**, a **56.32% reduction**, while retaining the **15,789-token** active issue. System 4 manages context across executions: it stored immediate operational state in a **965-byte** `hot_state.json`, deeper defect history in SQLite, and append-only findings in `shift_scratchpad.jsonl`. Both systems prioritize currently relevant information, but System 2 compresses conversation history inside one assembled prompt, while System 4 externalizes history across durable storage layers.

#### 17. Reliability you cannot see in one run

The System 4 fork tests verify that separate hypothesis scratchpads remain independent and that merging findings appends results without rewriting existing records. A single successful shift run would not reveal cross-fork mutation or ordering bugs. The **33 passing tests**, especially the fork and scratchpad tests, provide evidence for isolation properties that cannot be demonstrated by the final `shift C: 17 new defects` output alone.

#### 18. Blast radius

The largest risk in the Claims Intake Agent is sending a customer claim to an inappropriate destination or allowing processing to end without a valid terminal outcome. The design limits terminal actions to `route_to_adjuster` or `escalate_to_human`, uses structured tool schemas, and controls the loop through `stop_reason`.

In run `20261019_135042`, `summary.md` records six routed claims and two escalated claims. The traces for `claim_04` and `claim_06` show that the model ended its turn without issuing a valid terminal action, so the deterministic backstop escalated those claims instead of allowing processing to finish silently. This own-run evidence demonstrates how explicit terminal actions, structured errors, and the backstop reduce the blast radius of ambiguous or incomplete model behavior.

---

## Part 3 — Honest assessment

#### 19. What broke

An earlier System 4 replay used a retrieval timestamp that did not align with the fixture scenario and returned zero new defects. I corrected the invocation by using the required timestamp, `--since 2026-04-01T00:00:00Z`. The verified run then printed **`shift C: 17 new defects`**, generated a **965-byte** `hot_state.json`, and appended a **323-byte** line to `shift_scratchpad.jsonl`. The issue was therefore in the replay invocation parameters rather than in the indexed retrieval, state update, or scratchpad implementation.

#### 20. What you'd change

I would make replay scenarios self-describing by storing the scenario timestamp alongside each recorded response and validating that timestamp before execution. This would reduce the chance of using a `--since` value that excludes the fixture records. I would also include the resolved run ID, timestamp, record count, and artifact paths in a small machine-readable run manifest so that the reflection brief and submission evidence can be checked against one authoritative record.
