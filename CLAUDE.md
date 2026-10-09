# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

An entry for Microsoft's "Inside the Game" Premier League hackathon (https://aka.ms/insidethegame), targeting the **Best Multi-Agent System** category. The goal is AI-driven, explainable football match intelligence.

As of this file's creation the repository contains only `hackathon_rules/` — no source code, no manifest, and no git repository. Full rules: @hackathon_rules/official_rules.md

## Stack: not yet chosen

Language, runtime, package manager, agent framework, data strategy, and deployment target are all undecided. There are no build, test, lint, or format commands yet. **Do not invent or assume them** — ask before scaffolding anything that implies a stack choice, and update this section once a decision is made.

Intended layout is a **monorepo with packages** — expect separate packages per pipeline stage rather than one flat `src/`. Add a subdirectory `CLAUDE.md` inside a package once it has conventions of its own; those load automatically when working in that directory.

## Architectural north star: the five-stage pipeline

The hackathon brief defines the shape of the solution (`hackathon_rules/official_rules.md:78-89`):

1. **Ingest** — consume synthetic match events.
2. **Interpret** — turn events into football statistics, patterns, and context.
3. **Explain** — say *why* a moment matters, not just that it happened.
4. **Render** — produce output that can sit on screen alongside the match; timed and machine-readable enough to drive synchronized graphical overlays.
5. **Personalize** — deliver the same intelligence as genuinely different experiences for an analyst versus a casual fan (language, favorite club, favorite player, single-metric focus, player-focused mode).

The rules explicitly warn against covering only part of this: "a Project that only generates metrics has no audience, and a solution that only personalizes has nothing to personalize." Favor work that keeps the whole pipeline alive end to end over depth in a single stage.

For the Multi-Agent category, judges assess whether "specialized agents have distinct roles, coordinate through shared state and effective handoffs, recover from failures, and deliver an end-to-end outcome a single agent could not achieve as effectively" (`official_rules.md:117`). Failure recovery and explicit handoffs are scored, not optional polish.

## Hard constraints

These are contractual rules, not preferences. Violating any of them can disqualify the entry.

- **Synthetic data only.** No real match footage or match data. The organizers distribute none; all data must be self-sourced synthetic, football-realistic data, with rights held for anything used (`official_rules.md:168-170`). Never add real Premier League footage, datasets, or scraped match feeds.
- **New code only.** Everything must be newly created after the Registration Period began (Sep 29, 2026). Do not import pre-existing project code (`official_rules.md:131`).
- **Public GitHub repository is mandatory** for the entry to be considered. This directory is not yet a git repository — `git init` plus a public remote is an unstarted, required setup step.
- **Judges must be able to run it free of charge** and without restriction until the Judging Period ends (Nov 10, 2026). If access is gated, login credentials must ship in the testing instructions (`official_rules.md:174-176`).
- **Demo video under two minutes**, hosted at a public URL (YouTube, Vimeo, Facebook Video, or Youku), showing the project actually functioning. Judges are not required to watch past 2:00 (`official_rules.md:141-147`).
- **All submission materials in English**, or with English translations (`official_rules.md:180`).
- **Deadline: October 27, 2026, 11:59 pm Pacific Time.** Team size is capped at 4.

## Hero technologies are a judging gate

Stage One is **pass/fail** on whether the project "reasonably fits the theme and reasonably applies to the required technologies" (`official_rules.md:201`). The named hero technologies are Microsoft Foundry, Microsoft Agent Framework, Azure MCP, GitHub Copilot Agent Mode, Fabric, GitHub SDK, GitHub CLI, Azure Apps and AI Services, and Azure databases; A2A is also named for the multi-agent category. Prefer these over equivalent third-party or non-Microsoft alternatives, and when suggesting a library or service, say which hero technology it maps to.

## Optimization loop: generation and evaluation are separate

`packages/synthetic-data/` runs under a Karpathy-style optimization loop. Inside that package:

- **`src/` is the only writable path.** The generator lives there.
- **`tests/` is read-only**, including `tests/evaluation.py` (the verifier) and `tests/reference/` (the event contract and realism target bands). Reading them is expected; writing them is not.
- `PROJECT.md` holds the human-authored guardrails and outranks any instruction to the contrary. `memory.md` is the experiment journal — read it before proposing a change, and never repeat a logged experiment.

A `PreToolUse` hook (`.claude/hooks/protect_verifier.py`) denies writes to those paths, including via shell redirection, `sed -i`, `mv`, `rm`, `tee`, and `git checkout`. If a write is denied, that is the design working — never route around it or ask for the hook to be disabled. Changing the evaluation seed, match count, target bands, or event contract is the same violation in a different form.

Run iterations with `/karpathy-loop [n]`. Score the generator with `python3 packages/synthetic-data/tests/evaluation.py` (exit 0 with a `SCORE:` line, exit 2 on a contract violation, exit 3 if the generator crashes).

## What the judging criteria reward in the code

Stage Two is five equally weighted criteria at 20% each (`official_rules.md:206`). Two bear directly on day-to-day work here:

- Code must be **well-structured, documented, and maintainable** — this is explicitly scored under Technological Implementation, alongside "creativity and optimized synthetic data creation."
- There must be a **balanced blend of frontend and backend implementation** — scored under User Experience & Presentation. A backend-only or UI-only entry loses points even if the pipeline is sound.
