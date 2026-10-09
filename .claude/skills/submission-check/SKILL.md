---
name: submission-check
description: Audit this repository against the Microsoft "Inside the Game" hackathon submission requirements — public repo, demo video, testing access, synthetic-data-only compliance, English materials, hero-technology usage, and the Oct 27 2026 deadline. Use before submitting, or whenever the user asks whether the entry is submission-ready.
---

# Submission readiness check

Audit the repository against the hackathon's submission requirements and report a pass/fail per item with evidence. This is a **read-only audit** — do not fix anything unless the user asks.

Authoritative source: `@hackathon_rules/official_rules.md`. Re-read the relevant sections rather than trusting the summaries below, since rule text may have been updated.

## Checklist

Work through every item. For each, state **PASS**, **FAIL**, or **CANNOT VERIFY** (for things not visible from the repo, like the video URL on the hackathon site), plus one line of evidence — a file path, a command's output, or an explicit note that nothing in the repo attests to it.

1. **Public GitHub repository** — Confirm this is a git repository (`git rev-parse --git-dir`), has a GitHub remote (`git remote -v`), and that the remote is public. Use `gh repo view --json visibility` if `gh` is available. A public repo is mandatory for the entry to be considered.

2. **New code only** — Check the earliest commit date (`git log --reverse --format=%ad -1`). All work must postdate the Sep 29 2026 Registration Period start. Flag any vendored or copied code that looks pre-existing.

3. **Synthetic data only** — This is the highest-risk rule. Search the repo for real match data or footage: video/image files, large data files, and fetches against real football data sources. Check that any data generator is clearly synthetic and that `README` and code comments say so. Report any file you cannot confirm is synthetic. No real match footage or match data is permitted, and rights must be held for everything used.

4. **Judges can run it free of charge** — Look for a `README` with setup and testing instructions that a judge could follow. If the project is hosted behind any login, confirm credentials are included in those instructions. Confirm nothing requires payment.

5. **Demo video** — Look for a public video URL (YouTube, Vimeo, Facebook Video, or Youku) recorded in the repo (`README`, submission notes). Flag if absent. Remind the user it must be under two minutes and must show the project actually functioning. Length cannot be verified from the repo — report as CANNOT VERIFY and ask.

6. **English-only materials** — Scan `README`, docs, and user-facing strings for non-English content lacking an English translation.

7. **Hero technology usage (Stage One pass/fail)** — Stage One is pass/fail on whether the project reasonably applies the required technologies. Identify which hero technologies the code actually uses, with file evidence: Microsoft Foundry, Microsoft Agent Framework, Azure MCP, GitHub Copilot Agent Mode, Fabric, GitHub SDK, GitHub CLI, Azure Apps and AI Services, Azure databases, A2A. Name any that are claimed in docs but absent from the code — that gap is a Stage One risk.

8. **Five-stage pipeline coverage** — Confirm each stage is actually implemented, not just planned: Ingest, Interpret, Explain, Render, Personalize. Name the package or module covering each. Flag any stage with no implementation; the rules warn against covering only part of the pipeline.

9. **Multi-agent category fit** — The targeted category is Best Multi-Agent System. Verify the code shows specialized agents with distinct roles, coordination through shared state, explicit handoffs, and failure recovery. Failure recovery is scored — flag its absence specifically.

10. **Frontend/backend balance** — Judges score "a balanced blend of frontend and backend implementation." Report the rough split and flag a lopsided entry.

11. **Deadline** — Submission closes **October 27, 2026, 11:59 pm Pacific Time**. Report today's date and the time remaining.

## Output

Finish with a short summary: the count of FAIL items first (these are blocking), then CANNOT VERIFY items the user must confirm themselves, then a one-line overall verdict. Rank any failures by how likely they are to disqualify the entry versus merely cost points.
