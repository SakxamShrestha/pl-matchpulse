# memory.md — optimization journal

Append-only experiment log. Read this in full before proposing a hypothesis; never
repeat one already recorded here. Record failures with the same care as successes —
a logged failure is what stops the loop re-running a dead end on iteration 40.

Score source: `python3 tests/evaluation.py` (30 matches, seed 20261027).

## Entry format

```
### Iteration N — <one-line hypothesis>
- **Metric targeted:** <metric name>, expected direction
- **Change:** <what was edited in src/, in one or two lines>
- **Score:** <before> → <after>  (<KEPT|REVERTED>)
- **Per-metric delta:** <only the metrics that moved>
- **Lesson:** <what this tells the next iteration; "nothing" is not an acceptable answer>
- **Commit:** <sha, if kept>
```

---

### Iteration 0 — baseline, no change
- **Metric targeted:** none; establishing the starting point
- **Change:** none. Naive generator as committed at loop setup: flat event-type
  distribution over 12 types, near coin-flip outcomes, uniform positions over the pitch.
- **Score:** — → **20.43**  (KEPT)
- **Per-metric subscores:** `max_possession_share` 1.000, `shot_conversion_rate` 0.878,
  `events_per_match` 0.542, and **0.000** on all seven others:
  `pass_completion_rate` (0.343 vs 0.78–0.86), `passes_per_match` (99 vs 800–1000),
  `shots_per_match` (97.6 vs 20–30), `goals_per_match` (7.0 vs 2.4–3.2),
  `fouls_per_match` (98.9 vs 18–26), `shot_mean_distance_to_goal_m` (57.5 vs 14–20),
  `pass_type_share` (0.083 vs 0.45–0.58).
- **Lesson:** The flat event-type distribution is the single largest source of error — it
  simultaneously starves `passes_per_match`/`pass_type_share` and floods
  `shots_per_match`/`fouls_per_match`, five zeroed metrics from one cause. Weighting the
  event-type distribution toward passes is the obvious first hypothesis. Separately,
  uniform `x`/`y` is why shot distance is 57m: shots need to be spatially conditioned on
  being near the goal, which means position cannot stay independent of event type.
- **Commit:** —
