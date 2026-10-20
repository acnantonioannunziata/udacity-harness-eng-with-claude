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

Each test log includes a system header or project path so that its output can be unambiguously associated with the corresponding system. The submission also includes run-level evidence beyond the automated test logs:

- `evidence/01_agentic_loop/` contains the run `20261019_135042` summary, eight non-empty turn-by-turn traces, queue records, escalation records, and an artifact manifest.
- `evidence/04_orchestration/shift_run_output.txt` contains the exact SQL-filtered Shift C command, the `--since 2026-04-01T00:00:00Z` value, exit code 0, the `shift C: 17 new defects` result, and state-file size measurements.
- `evidence/04_orchestration/hot_state.json` is 965 bytes, and `evidence/04_orchestration/shift_scratchpad.jsonl` is 646 bytes after the verified run.

---

## Part 1 — Per-system

### System 1 — Agentic loop

#### 1. Loop control

Loop termination is decided in `claims_intake/loop.py`, inside the `run()` function beginning at line 46. The harness continues when `response.stop_reason == "tool_use"` and dispatches every structured tool-use block. When `response.stop_reason == "end_turn"`, `run()` appends the final assistant content and returns a `FinalState`, terminating the loop. Any other stop reason raises `UnexpectedStopReason` at lines 130–131 rather than being silently accepted. This makes the model's structured response state, rather than its prose, the control signal for the loop.

The submitted trace `evidence/01_agentic_loop/traces/claim_07_tree_falls_on_car.jsonl`, from run `20261019_135042`, demonstrates this behavior turn by turn. Turns 1 through 4 each record `stop_reason: "tool_use"` and the harness continues after every turn. Turn 4 invokes the terminal `route_to_adjuster` tool, and turn 5 records `stop_reason: "end_turn"` with no additional tool calls, causing the harness to return. The trace therefore provides four `tool_use` transitions followed by one `end_turn` transition.

#### 2. Anti-pattern

One anti-pattern checked by `tests/test_antipatterns.py` is controlling execution through string matching against model-generated prose. Such logic would be fragile because a harmless wording change could incorrectly stop the loop or route a claim. In my implementation, control flow depends on structured `stop_reason` values and tool calls. The System 1 test run completed with **30 passing tests**.

#### 3. Tool design

`route_to_adjuster` and `escalate_to_human` are intentionally overlapping terminal actions because both end automated claim processing, but they represent different outcomes. `route_to_adjuster` is used when the claim has enough validated information for ordinary handling, while `escalate_to_human` is used when ambiguity, low confidence, policy concerns, or missing facts make automated routing unsafe.

Tool failures are constructed by `_err()` in `claims_intake/tools.py`, lines 196–204. `_err()` serializes a structured JSON object containing `is_error: true`, an error category, a `retryable` flag, and a message. This is safer than returning plain-text errors because the model and harness can identify failures through explicit fields instead of interpreting informal wording.

A concrete outcome appears in `evidence/01_agentic_loop/summary.md`: `claim_04_neighbor_injury` was escalated after 2 turns. Its submitted trace, `evidence/01_agentic_loop/traces/claim_04_neighbor_injury.jsonl`, shows one `tool_use` turn followed by `end_turn` without a valid terminal tool invocation. The deterministic backstop therefore escalated the claim instead of allowing processing to finish without a routing decision. The run summary records six routed claims and two escalated claims across eight processed fixtures.

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

The warm database was seeded from `fixtures/defects.json`. Indexed retrieval is implemented by `WarmStore.defects_since()` in `shift_monitor/warm.py`, using a bounded SQL query that filters records by timestamp, orders the results, and applies a limit. This keeps irrelevant historical rows out of the model prompt.

The submitted run artifact `evidence/04_orchestration/shift_run_output.txt` records the exact command:

`python -m shift_monitor run-shift --shift C --since 2026-04-01T00:00:00Z --recorded-response fixtures/recorded_responses/shift_C_2026-04-30.json`

The run completed with exit code 0 and printed `shift C: 17 new defects`. Filtering in SQLite therefore reduced the input to the 17 April records required for the Shift C analysis rather than loading the complete defect history.

#### 12. Crash recovery

`recovery.py` defines `STALE_RESUME_THRESHOLD_MINUTES = 30`. The recovery decision uses both completion state and age: a recent incomplete run can resume, while an old or completed run starts fresh. The tests cover the boundary around the 30-minute threshold and verify both resume and fresh-start behavior. This avoids treating stale partial reasoning as if it belonged to the current execution.

#### 13. Small state

The submitted `evidence/04_orchestration/hot_state.json` is 965 bytes, well below the approximate 5 KB budget. It contains 17 recent defect hashes, the current shift summary, three active alerts, and threshold statuses. The accompanying `evidence/04_orchestration/shift_run_output.txt` records the same 965-byte measurement after the successful Shift C run.

The submitted `evidence/04_orchestration/shift_scratchpad.jsonl` is 646 bytes after the verified run. The scratchpad contains append-only shift findings, including the entry documenting 17 defects analyzed since `2026-04-01T00:00:00Z`. Keeping immediate hot state small matters because the monitor is designed to operate across many shifts without allowing the state loaded for every invocation to grow without bound. Larger historical data remains in SQLite, while the scratchpad preserves compact append-only findings.

---

## Part 2 — Synthesis

#### 14. Three layers

- **Model:** The model boundary is implemented in `claims_intake/client.py`. `make_client()` constructs the Anthropic client, while `DEFAULT_MODEL = "claude-haiku-4-5-20251001"` selects the model used for semantic interpretation and tool selection. The resulting model behavior is visible in `evidence/01_agentic_loop/traces/claim_07_tree_falls_on_car.jsonl`, where the model requests policy lookup, records claim facts, classifies the claim, assesses severity, and selects `route_to_adjuster`.

- **Harness:** `claims_intake/loop.py` implements the stop-reason-driven execution protocol, continuing only on `tool_use`, returning on `end_turn`, and raising `UnexpectedStopReason` for unsupported states. `claims_intake/tools.py` implements the structured tool contracts, JSON success and error results, and the terminal routing and escalation actions.

- **Orchestration:** `shift_monitor/pipeline.py` coordinates SQL-filtered retrieval, model invocation, hot-state updates, and scratchpad persistence across a shift run. The completed orchestration is demonstrated by `evidence/04_orchestration/shift_run_output.txt`, which records a successful Shift C run over 17 filtered defects.

These layers address different failure modes. The Model layer supplies semantic judgment, the Harness layer controls how model outputs may affect execution, and the Orchestration layer coordinates retrieval, invocation, and durable state across the wider workflow.

#### 15. Deterministic vs prompt

A deterministic behavior is the System 1 loop's use of structured `stop_reason` values and terminal tool calls. The harness decides whether to continue, stop, or reject an unexpected state without interpreting prose. A prompt-guided behavior is semantic claim classification, where the model must interpret the facts and choose an appropriate action. Deterministic mechanisms are better for safety boundaries and execution guarantees; prompt guidance is better for tasks requiring language understanding and contextual judgment. In run `20261019_135042`, six claims were routed and two were escalated, while the harness maintained the same structured execution protocol for every claim.

#### 16. Context, two faces

System 2 manages context within one long conversation. It reduced the transcript from **38,708** to **16,907 tokens**, a **56.32% reduction**, while retaining the **15,789-token** active issue. System 4 manages context across executions: it stored immediate operational state in a **965-byte** `hot_state.json`, deeper defect history in SQLite, and append-only findings in `shift_scratchpad.jsonl`. Both systems prioritize currently relevant information, but System 2 compresses conversation history inside one assembled prompt, while System 4 externalizes history across durable storage layers.

#### 17. Reliability you cannot see in one run

The isolation mechanism is implemented in `shift_monitor/fork.py`. `fork_for_hypothesis()` begins at line 17 and copies the base `hot_state.json` into a hypothesis-specific working directory using `shutil.copyfile`. The function does not modify the base hot-state file. Each hypothesis receives its own directory and therefore its own isolated working state and scratchpad.

`merge_findings()` begins at line 28. It reads entries from each completed fork scratchpad and calls `destination.append(entry)` for every finding. It therefore appends findings to the main scratchpad without replacing or rewriting its existing entries.

These guarantees are checked by `test_fork_for_hypothesis_copies_state_without_mutating_base`, `test_two_forks_produce_independent_scratchpads`, and `test_merge_findings_appends_without_rewriting_existing` in `tests/test_us04_fork_scratchpad.py`. The System 4 suite completed with 33 passing tests. A single successful output such as `shift C: 17 new defects` cannot reveal cross-fork mutations, scratchpad contamination, or rewriting of existing records, so these tests provide reliability evidence that manual inspection of one run cannot provide.

#### 18. Blast radius

The largest risk in the Claims Intake Agent is sending a customer claim to an inappropriate destination or allowing processing to end without a valid terminal outcome. The implementation limits valid terminal actions to `route_to_adjuster` and `escalate_to_human`, uses structured tool schemas, and controls execution through `stop_reason` in `claims_intake/loop.py`.

In run `20261019_135042`, the submitted `evidence/01_agentic_loop/summary.md` records six routed claims and two escalated claims. `evidence/01_agentic_loop/traces/claim_04_neighbor_injury.jsonl` contains a `tool_use` turn followed by `end_turn`, while `evidence/01_agentic_loop/traces/claim_06_low_confidence_escalation.jsonl` contains two `tool_use` turns followed by `end_turn`. Neither trace contains a valid terminal tool invocation before `end_turn`.

Instead of allowing those claims to finish silently, the deterministic backstop escalated `claim_04_neighbor_injury` after 2 turns and `claim_06_low_confidence_escalation` after 3 turns, as recorded in `evidence/01_agentic_loop/summary.md` and `evidence/01_agentic_loop/escalations.jsonl`. This own-run evidence demonstrates how explicit terminal actions, structured tool results, and deterministic escalation reduce the blast radius of ambiguous or incomplete model behavior.

---

## Part 3 — Honest assessment

#### 19. What broke

An earlier System 4 replay used a retrieval timestamp that did not align with the fixture scenario and returned zero new defects. The invocation was corrected by using `--since 2026-04-01T00:00:00Z` and the offline fixture `fixtures/recorded_responses/shift_C_2026-04-30.json`.

The corrected command and its complete output are preserved in `evidence/04_orchestration/shift_run_output.txt`. The run completed with exit code 0, printed `shift C: 17 new defects`, produced a 965-byte `evidence/04_orchestration/hot_state.json`, and left a 646-byte `evidence/04_orchestration/shift_scratchpad.jsonl`. The problem was therefore in the replay invocation parameters rather than in indexed retrieval, state updating, or scratchpad persistence.

#### 20. What you'd change

The first submission included the System 1 run summary but omitted the non-empty trace files from run `20261019_135042`. For example, `claim_07_tree_falls_on_car.jsonl` existed in the run directory and recorded four `tool_use` turns followed by `end_turn`, but it was not available to the reviewer under `evidence/`. The corrected submission now includes it as `evidence/01_agentic_loop/traces/claim_07_tree_falls_on_car.jsonl`.

I would add a machine-readable evidence manifest and a pre-submission validator. The manifest would record each system, source run ID, required artifact path, byte size, command, exit code, and creation timestamp. The validator would fail the packaging step when a required artifact is absent or zero bytes, when a System 1 trace lacks both `tool_use` and `end_turn`, or when the System 4 run output lacks the required `--since` value and `shift C: 17 new defects` result.

I would also make replay scenarios self-describing by storing the expected retrieval timestamp alongside each recorded response. This change is motivated by the earlier failed replay documented in the project history and by the corrected command now preserved in `evidence/04_orchestration/shift_run_output.txt`. Together, these checks would make the submission evidence reproducible and would prevent a working implementation from failing review because its run artifacts were omitted or could not be verified.