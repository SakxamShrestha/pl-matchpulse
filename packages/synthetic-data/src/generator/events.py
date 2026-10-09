"""Naive baseline synthetic football event generator.

This is the BASELINE. It is deliberately unsophisticated: event types are drawn
from a flat-ish distribution, outcomes are near coin-flips, and positions are
uniform over the pitch. It satisfies the event contract but scores poorly on
realism, which is the point -- it leaves the optimization loop real headroom.

This file (and anything else under src/) is the only place the loop may edit.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List

PITCH_LENGTH = 105.0
PITCH_WIDTH = 68.0
PERIOD_SECONDS = 45 * 60

EVENT_TYPES = [
    "pass",
    "carry",
    "shot",
    "tackle",
    "interception",
    "clearance",
    "foul",
    "save",
    "goal_kick",
    "throw_in",
    "corner",
    "pressure",
]

OUTCOMES = ["success", "failure", "neutral"]


def generate_match(match_id: str, rng: random.Random) -> List[Dict[str, Any]]:
    """Generate one match's worth of events as a flat, time-ordered list."""
    home, away = f"{match_id}-home", f"{match_id}-away"
    events: List[Dict[str, Any]] = []

    for period in (1, 2):
        n_events = rng.randint(500, 700)
        clocks = sorted(rng.randint(0, PERIOD_SECONDS) for _ in range(n_events))
        for clock_s in clocks:
            team = home if rng.random() < 0.5 else away
            event_type = rng.choice(EVENT_TYPES)
            event = {
                "match_id": match_id,
                "period": period,
                "clock_s": clock_s,
                "team": team,
                "player_id": f"{team}-p{rng.randint(1, 14)}",
                "type": event_type,
                "x": rng.uniform(0.0, PITCH_LENGTH),
                "y": rng.uniform(0.0, PITCH_WIDTH),
                "outcome": rng.choice(OUTCOMES),
            }
            events.append(event)

            # A shot sometimes becomes a goal; the contract requires the goal
            # event to immediately follow its shot, same team, same match.
            if event_type == "shot" and rng.random() < 0.08:
                goal = dict(event)
                goal["type"] = "goal"
                goal["outcome"] = "success"
                events.append(goal)

    return events


def generate_matches(n_matches: int, seed: int) -> List[List[Dict[str, Any]]]:
    """Generate `n_matches` matches deterministically from `seed`.

    The evaluator calls this with a fixed seed, so the same generator code must
    always produce the same events and therefore the same score.
    """
    rng = random.Random(seed)
    return [generate_match(f"m{i:03d}", rng) for i in range(n_matches)]
