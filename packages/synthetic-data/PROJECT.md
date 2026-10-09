# PROJECT.md — synthetic-data optimization loop guardrails

Human-authored. The agent reads this and does not edit it. If a rule here needs to
change, a human changes it.

## Optimization target

Maximize `SCORE` as printed by `tests/evaluation.py`, where 100 means every realism
metric sits inside its target band. Baseline at loop setup: **20.43**.

The score measures how football-realistic the synthetic event stream is. It is a
proxy for the judging criterion "creativity and optimized synthetic data creation"
(`hackathon_rules/official_rules.md:206`).

## The immutable rule

Generation and evaluation are separate systems.

- **Writable:** `src/**` only.
- **Read-only:** `tests/**`, including `tests/evaluation.py`, `tests/reference/event_contract.json`,
  and `tests/reference/realism_targets.json`.

A `PreToolUse` hook in `.claude/settings.json` denies writes to `tests/**` and to any
`evaluation.py`. This is enforced by the harness, not by good intentions — the agent
cannot edit the thing that grades it, so it cannot score well by redefining success.

Also out of bounds, because they are the same move in a different costume:
- Changing `N_MATCHES` or `SEED` (they live in the verifier, so the hook already blocks it).
- Special-casing the generator on the evaluation seed, or detecting that it is being
  evaluated and behaving differently.
- Hardcoding outputs to hit a metric without the underlying event stream being coherent.

## Invariants — never trade score for these

1. **Synthetic data only.** No real match data, footage, or scraped feeds enter this
   package, ever. The generator must produce events from first principles or from
   hand-authored statistical priors. This is a hackathon disqualification risk, not a
   style preference (`official_rules.md:168-170`).
2. **The event contract holds.** `tests/evaluation.py` exits 2 on any contract violation
   and refuses to print a score. An invariant failure is a bug to fix, not a low score
   to average out.
3. **Determinism.** `generate_matches(n, seed)` must return identical events for identical
   arguments. A non-reproducible generator makes every score in `memory.md` worthless.
4. **Stdlib-or-declared.** New third-party dependencies need a human's approval first;
   say which hero technology the dependency maps to.
5. **Readable code.** Judges score whether code is "well-structured, documented, and
   maintainable". A clever one-liner that gains 0.3 points and nobody can read is a net loss.

## Loop protocol

1. Read `memory.md` in full before proposing anything.
2. State a hypothesis in one sentence, naming the metric it should move and the direction.
3. Make the smallest change to `src/**` that tests the hypothesis. One variable at a time —
   a bundled change that improves the score teaches nothing about which part worked.
4. Run `python3 tests/evaluation.py`.
5. **Score improved:** keep the change, append the entry to `memory.md`, commit.
6. **Score degraded or unchanged:** revert immediately (`git checkout -- src/`), append the
   entry to `memory.md` anyway. Failed experiments are the more valuable half of the journal.
7. **Exit 2 (invariant violation):** revert. Do not try to satisfy the invariant by weakening it.
8. Never repeat a hypothesis already logged in `memory.md`.

## Stopping criteria

Stop and ask for human review when any of these is true:

- Three consecutive iterations produce no score improvement.
- Score reaches 95 or above — remaining gains are probably metric-gaming, not realism.
- An experiment would require editing anything outside `src/**`.
- The next idea needs a new third-party dependency.
- An invariant can only be satisfied by changing the contract.
