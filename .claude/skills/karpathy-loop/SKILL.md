---
name: karpathy-loop
description: Run autonomous optimization iterations on a module where generation and evaluation are separate systems - propose a hypothesis, edit only src/, run the read-only verifier, keep or revert based on the score, and journal the result in memory.md. Takes an optional iteration count, e.g. /karpathy-loop 10.
disable-model-invocation: true
---

# Karpathy loop

Run `$ARGUMENTS` iterations of hypothesis-driven optimization (default: 1) against a
module whose generator and verifier are separate systems.

Default module: `packages/synthetic-data`. Its guardrails live in that module's
`PROJECT.md` and its journal in `memory.md`. If the user names a different module, use
that module's equivalents instead.

## Before the first iteration

1. Read the module's `PROJECT.md` in full. It defines the optimization target, the
   writable boundary, the invariants, and the stopping criteria. It outranks this file.
2. Read the module's `memory.md` in full. Every logged hypothesis is off-limits —
   re-running a recorded experiment burns an iteration and teaches nothing.
3. Check the working tree is clean (`git status --short`). The loop reverts by discarding
   changes under `src/`, which would silently destroy uncommitted work. If the tree is
   dirty, stop and say so.
4. Run the verifier once and confirm the score matches the last entry in `memory.md`. A
   mismatch means something drifted — stop and report it rather than stacking experiments
   on an unknown baseline.

## Each iteration

1. **Hypothesize.** One sentence, naming the metric to move and the direction, grounded
   in the per-metric subscores from the last run. State it before editing; a hypothesis
   written after seeing the result is not a hypothesis.
2. **Change one thing.** The smallest edit under `src/` that tests the hypothesis. Do not
   bundle two ideas — if a bundled change improves the score you have learned nothing
   about which half worked, and the journal entry is now misleading.
3. **Measure.** Run the verifier. Capture the `SCORE:` line and the per-metric subscores.
4. **Decide by exit code and score:**
   - **Score improved** → keep. Append to `memory.md`. Commit the `src/` change and the
     journal entry together, with a message naming the hypothesis and the score delta.
   - **Score degraded or unchanged** → revert `src/` immediately, then append to
     `memory.md` anyway with the lesson. Failed experiments are the more valuable half of
     the journal.
   - **Exit 2 (invariant violation)** → revert. Record which invariant broke. Do not look
     for a way to satisfy the invariant by weakening it; the invariant is not the
     obstacle, the change was wrong.
   - **Exit 3 (import error or crash)** → revert. The generator does not run, so there is
     no score; start the next iteration from the known-good state.
5. **Journal honestly.** Use the entry format at the top of `memory.md`. Record the real
   before/after numbers, including when the result embarrasses the hypothesis. The
   journal is only worth having if iteration 40 can trust it.

## Hard rules

- **Only `src/` is writable.** A `PreToolUse` hook denies writes to the verifier, its
  reference data, and the guardrails — including via shell redirection, `sed -i`, `mv`,
  `rm`, and `git checkout`. If a write is denied, that is the design working. Do not look
  for a way around it, and do not ask the user to disable the hook so an experiment can
  proceed.
- **Never edit what grades you.** This includes the evaluation seed, the match count, the
  metric target bands, and the event contract.
- **Never special-case the evaluator.** Detecting the evaluation seed, or making the
  generator behave differently when it is being measured, produces a worthless score and
  poisons every later entry in the journal.
- **Report the real number.** Never state a score you did not get from running the
  verifier in this session.

## Stop and hand back to a human when

- Three consecutive iterations show no improvement. Report all three hypotheses and what
  the plateau suggests about where the remaining error lives.
- Any stopping criterion in the module's `PROJECT.md` is met.
- An experiment would need a write outside `src/`, or a new third-party dependency.
- The requested iteration count is exhausted.

On stopping, report: iterations run, the score path from start to finish, which changes
were kept, and the single most useful thing the journal knows now that it did not before.
