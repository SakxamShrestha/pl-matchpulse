#!/usr/bin/env python3
"""Deterministic verifier for the synthetic football event generator.

READ-ONLY to the optimization loop. A PreToolUse hook blocks writes to this
path. If the score needs to change, a human changes the targets -- not the agent.

Contract with the loop:
  exit 0  -> evaluation completed; stdout ends with a line "SCORE: <float>"
  exit 2  -> the generator violated a hard invariant; score is meaningless
  exit 3  -> the generator could not be imported or crashed

Stdlib only, on purpose: a verifier with dependencies is a verifier that can
break for reasons unrelated to the thing being measured.
"""

from __future__ import annotations

import json
import math
import os
import sys
import traceback
from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
PACKAGE_ROOT = os.path.dirname(HERE)
SRC = os.path.join(PACKAGE_ROOT, "src")
REFERENCE = os.path.join(HERE, "reference")

# Fixed evaluation conditions. Changing these changes what "score" means and
# invalidates every entry in memory.md, so they are pinned here deliberately.
N_MATCHES = 30
SEED = 20261027

PITCH_LENGTH = 105.0
PITCH_WIDTH = 68.0
GOAL_CENTRE = (PITCH_LENGTH, PITCH_WIDTH / 2.0)


def load_json(name: str) -> Dict[str, Any]:
    with open(os.path.join(REFERENCE, name), "r", encoding="utf-8") as handle:
        return json.load(handle)


# --------------------------------------------------------------------------
# Invariants: structural correctness. Failing these is a bug, not a low score.
# --------------------------------------------------------------------------

def check_invariants(matches: List[List[Dict[str, Any]]], contract: Dict[str, Any]) -> List[str]:
    required = contract["required_fields"]
    valid_types = set(contract["event_types"])
    valid_outcomes = set(contract["outcomes"])
    errors: List[str] = []

    def fail(msg: str) -> None:
        if len(errors) < 20:
            errors.append(msg)

    if not matches:
        fail("generator produced zero matches")
        return errors

    for match in matches:
        if not match:
            fail("generator produced an empty match")
            continue

        teams = set()
        last_clock: Dict[int, int] = {}
        prev_event: Dict[str, Any] = {}

        for index, event in enumerate(match):
            missing = [field for field in required if field not in event]
            if missing:
                fail("event missing fields %s" % missing)
                continue

            match_id = event["match_id"]
            teams.add(event["team"])

            if event["period"] not in (1, 2):
                fail("period %r not in (1, 2)" % (event["period"],))
            if not isinstance(event["clock_s"], int) or event["clock_s"] < 0:
                fail("clock_s %r is not a non-negative int" % (event["clock_s"],))
            if event["type"] not in valid_types:
                fail("unknown event type %r" % (event["type"],))
            if event["outcome"] not in valid_outcomes:
                fail("unknown outcome %r" % (event["outcome"],))

            try:
                x, y = float(event["x"]), float(event["y"])
            except (TypeError, ValueError):
                fail("x/y not numeric: %r, %r" % (event["x"], event["y"]))
            else:
                if not (0.0 <= x <= PITCH_LENGTH):
                    fail("x %.2f outside pitch length" % x)
                if not (0.0 <= y <= PITCH_WIDTH):
                    fail("y %.2f outside pitch width" % y)

            period = event["period"]
            if isinstance(period, int) and isinstance(event["clock_s"], int):
                if period in last_clock and event["clock_s"] < last_clock[period]:
                    fail(
                        "clock went backwards in %s period %d: %d after %d"
                        % (match_id, period, event["clock_s"], last_clock[period])
                    )
                last_clock[period] = event["clock_s"]

            if event["type"] == "goal":
                if not prev_event:
                    fail("goal is the first event of a match, with no preceding shot")
                elif prev_event.get("type") != "shot":
                    fail("goal at index %d not immediately preceded by a shot" % index)
                elif prev_event.get("team") != event["team"]:
                    fail("goal credited to a different team than the preceding shot")

            prev_event = event

        if len(teams) != 2:
            fail("match has %d distinct teams, expected exactly 2" % len(teams))

    return errors


# --------------------------------------------------------------------------
# Metrics: the things actually being optimized.
# --------------------------------------------------------------------------

def compute_metrics(matches: List[List[Dict[str, Any]]]) -> Dict[str, float]:
    n = float(len(matches))
    totals: Counter = Counter()
    pass_attempts = pass_success = 0
    shot_distances: List[float] = []
    possession_shares: List[float] = []

    for match in matches:
        totals["events"] += len(match)
        per_team: Counter = Counter()

        for event in match:
            etype = event["type"]
            totals[etype] += 1

            if etype == "pass":
                pass_attempts += 1
                if event["outcome"] == "success":
                    pass_success += 1
            elif etype == "shot":
                shot_distances.append(
                    math.hypot(GOAL_CENTRE[0] - float(event["x"]), GOAL_CENTRE[1] - float(event["y"]))
                )

            # Possession proxy: on-ball actions only, so off-ball pressure and
            # defensive events don't inflate a team's share.
            if etype in ("pass", "carry", "shot", "goal"):
                per_team[event["team"]] += 1

        on_ball = sum(per_team.values())
        if on_ball:
            possession_shares.append(max(per_team.values()) / float(on_ball))

    shots = float(totals["shot"])
    return {
        "pass_completion_rate": (pass_success / float(pass_attempts)) if pass_attempts else 0.0,
        "passes_per_match": totals["pass"] / n,
        "shots_per_match": shots / n,
        "goals_per_match": totals["goal"] / n,
        "shot_conversion_rate": (totals["goal"] / shots) if shots else 0.0,
        "fouls_per_match": totals["foul"] / n,
        "events_per_match": totals["events"] / n,
        "max_possession_share": (sum(possession_shares) / len(possession_shares)) if possession_shares else 0.0,
        "shot_mean_distance_to_goal_m": (sum(shot_distances) / len(shot_distances)) if shot_distances else 0.0,
        "pass_type_share": (totals["pass"] / float(totals["events"])) if totals["events"] else 0.0,
    }


def score_metric(value: float, spec: Dict[str, float]) -> float:
    """1.0 inside the target band, decaying linearly to 0.0 over `tolerance`."""
    low, high, tolerance = spec["low"], spec["high"], spec["tolerance"]
    if low <= value <= high:
        return 1.0
    distance = (low - value) if value < low else (value - high)
    return max(0.0, 1.0 - (distance / float(tolerance)))


def evaluate(metrics: Dict[str, float], targets: Dict[str, Any]) -> Tuple[float, List[Tuple[str, float, float]]]:
    rows: List[Tuple[str, float, float]] = []
    weighted_sum = weight_total = 0.0

    for name, spec in targets["metrics"].items():
        value = metrics.get(name, 0.0)
        subscore = score_metric(value, spec)
        weight = float(spec["weight"])
        weighted_sum += subscore * weight
        weight_total += weight
        rows.append((name, value, subscore))

    total = (weighted_sum / weight_total) * 100.0 if weight_total else 0.0
    return total, rows


def main() -> int:
    sys.path.insert(0, SRC)
    try:
        from generator import generate_matches  # noqa: WPS433 (import inside function is deliberate)
    except Exception:
        sys.stderr.write("FATAL: could not import generator from %s\n" % SRC)
        traceback.print_exc()
        return 3

    try:
        matches = generate_matches(N_MATCHES, SEED)
    except Exception:
        sys.stderr.write("FATAL: generate_matches(%d, %d) raised\n" % (N_MATCHES, SEED))
        traceback.print_exc()
        return 3

    contract = load_json("event_contract.json")
    targets = load_json("realism_targets.json")

    errors = check_invariants(matches, contract)
    if errors:
        sys.stderr.write("INVARIANT VIOLATIONS (%d shown):\n" % len(errors))
        for error in errors:
            sys.stderr.write("  - %s\n" % error)
        sys.stderr.write("\nScore not computed. Fix the contract violations first.\n")
        return 2

    metrics = compute_metrics(matches)
    total, rows = evaluate(metrics, targets)

    print("Synthetic data realism evaluation")
    print("  matches=%d  seed=%d" % (N_MATCHES, SEED))
    print()
    print("  %-32s %12s %10s %18s" % ("metric", "value", "subscore", "target band"))
    print("  " + "-" * 74)
    for name, value, subscore in sorted(rows, key=lambda row: row[2]):
        spec = targets["metrics"][name]
        band = "%g - %g" % (spec["low"], spec["high"])
        print("  %-32s %12.4f %10.3f %18s" % (name, value, subscore, band))
    print()
    print("SCORE: %.2f" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
