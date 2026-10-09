#!/usr/bin/env python3
"""Karpathy-loop enforcement: deny any agent write to the verifier or guardrails.

Generation and evaluation must be separate systems. The optimization loop may edit
``src/**``. It may never edit the verifier, its reference data, or the human-authored
guardrails -- if it could, it could score well by redefining success instead of by
improving the generator.

Reads a PreToolUse payload on stdin. Prints a deny decision when the tool call would
*write* a protected path, and prints nothing (allowing the call) otherwise. Always
exits 0: the decision travels in the JSON, not in the exit code.

Reading protected files is allowed and necessary -- the loop has to read the verifier
to understand what it is being scored on, and has to run it to get a score. So this
guard identifies write *targets* rather than merely mentioning a protected path
anywhere in a command. A naive "does this command string contain tests/" check
false-positives on any command whose content happens to discuss the protected paths,
and a guard that cries wolf is a guard someone turns off.
"""

from __future__ import annotations

import json
import re
import shlex
import sys
from typing import List

# Paths the loop must never modify.
PROTECTED = re.compile(
    r"(?:^|/)tests(?:/|$)"  # the tests directory itself, or anything inside it
    r"|(?:^|/)evaluation\.py$"
    r"|(?:^|/)PROJECT\.md$"
)

WRITE_TOOLS = {"Write", "Edit", "NotebookEdit"}

# Shell commands that modify or destroy their path arguments. For these, every
# path-shaped argument is treated as a write target, not just the last one:
# `mv tests/x /tmp` is as destructive as `mv /tmp/x tests/`.
DESTRUCTIVE_COMMANDS = {"mv", "cp", "rm", "truncate", "chmod", "chown", "ln", "install"}

# Redirections: `> f`, `>> f`, `2> f`, `&> f`.
REDIRECT = re.compile(r"(?:\d*>>?|&>)\s*(\"[^\"]+\"|'[^']+'|[^\s;&|<>]+)")


def deny(reason: str) -> None:
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    sys.stdout.write("\n")
    sys.exit(0)


def unquote(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
        return token[1:-1]
    return token


def redirect_targets(command: str) -> List[str]:
    return [unquote(match.group(1)) for match in REDIRECT.finditer(command)]


def command_targets(command: str) -> List[str]:
    """Write targets implied by destructive commands and in-place editors."""
    targets: List[str] = []

    try:
        tokens = shlex.split(command, comments=False)
    except ValueError:
        # Unbalanced quotes -- most likely a heredoc body. Fall back to whitespace
        # splitting rather than giving up, so a malformed command cannot slip past.
        tokens = command.split()

    # Split on shell separators so each simple command is inspected on its own.
    segments: List[List[str]] = [[]]
    for token in tokens:
        if token in (";", "&&", "||", "|", "&"):
            segments.append([])
        else:
            segments[-1].append(token)

    for segment in segments:
        if not segment:
            continue

        # Skip leading env assignments and common wrappers.
        index = 0
        while index < len(segment) and "=" in segment[index] and not segment[index].startswith("-"):
            index += 1
        while index < len(segment) and segment[index] in ("sudo", "env", "command", "time", "nohup", "xargs"):
            index += 1
        if index >= len(segment):
            continue

        name = segment[index].rsplit("/", 1)[-1]
        args = segment[index + 1:]
        operands = [arg for arg in args if not arg.startswith("-")]

        if name in DESTRUCTIVE_COMMANDS or name == "tee":
            targets.extend(operands)
        elif name == "sed" and any(arg.startswith("-i") or arg == "--in-place" for arg in args):
            # First operand is the script, the rest are files edited in place.
            targets.extend(operands[1:])
        elif name in ("perl", "ruby") and any(arg.startswith("-i") for arg in args):
            targets.extend(operands[1:])
        elif name == "dd":
            targets.extend(arg.split("=", 1)[1] for arg in args if arg.startswith("of="))
        elif name == "git" and operands[:1] and operands[0] in ("checkout", "restore", "apply", "clean"):
            targets.extend(operands[1:])
        elif name in ("touch", "mkdir", "rmdir"):
            targets.extend(operands)

    return targets


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        # Cannot parse the payload, so cannot judge it. Allow rather than wedge the
        # session; the structural protection is the hook, not this failure path.
        return 0

    tool_name = payload.get("tool_name") or ""
    tool_input = payload.get("tool_input") or {}

    if tool_name in WRITE_TOOLS:
        file_path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        if file_path and PROTECTED.search(file_path):
            deny(
                "Karpathy loop: %s is the verifier or the guardrails, which the "
                "optimization loop may not edit. Only src/** is writable. If the scoring "
                "itself is wrong, stop and raise it with a human rather than changing it."
                % file_path
            )
        return 0

    if tool_name == "Bash":
        command = tool_input.get("command") or ""
        if not command:
            return 0
        for target in redirect_targets(command) + command_targets(command):
            if PROTECTED.search(target):
                deny(
                    "Karpathy loop: this command would write to %s, which is the verifier "
                    "or the guardrails and may not be modified by the optimization loop. "
                    "Only src/** is writable. Reading those files, and running the "
                    "evaluation script, are both fine."
                    % target
                )
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
