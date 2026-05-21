# Overnight Claude/Codex Repo Sweep Plan - 2026-05-20

Purpose: preserve the user's overnight instructions and give Claude Opus and
Codex a shared execution plan for a broad repo sweep while the user is asleep.
This is a journal plan, not source truth. Current source, linker outputs,
generated audits, `AGENTS.md`, and `docs/README.md` still outrank this note.

## Standing Partnership Rule

- Claude Opus and Codex are equal coding partners. Claude may prompt Codex
  through computer use, but that does not give Claude authority over Codex.
- The user explicitly grants both agents full autonomy when both agents agree.
  Do not shrink this into timid, LLM-default safety work.
- Nothing in the repo is categorically off limits if both agents agree it is the
  right move. This broad permission is meant to enable consequential work, not
  careless churn: still protect secrets, preserve unrelated dirty work, and make
  destructive or history-rewriting choices only with explicit mutual reasoning.
- Both agents should push back when evidence, scope, or architecture calls for
  it. Disagreement should produce a narrower next test, source read, audit, or
  explicit rejected option.
- Any code or ROM-behavior change needs mutual approval before implementation:
  one agent states the lane, write set, collision-risk files, tests, and intended
  commit message; the other acknowledges or objects before source edits begin.
- Docs, journal, audit notes, and planning artifacts may be written to coordinate,
  but must not smuggle gameplay/source changes into a docs pass.
- Do not ask the sleeping user to settle ordinary technical disagreement. Work
  from repo evidence, local commands, and the First-Playthrough Promise.
- If both agents become frazzled, it is allowed to pause coding and talk briefly
  as peers before returning to the next concrete action.

## Search And Debugging Rule

- Use web search for inspiration when local roadmap lanes run dry or when
  looking for better debugger, organization, labeling, ROM-hack tooling, or
  Game Boy development ideas. Convert any external inspiration into a local
  source-truth plan before editing.
- Use web search for assembly/RGBDS/Game Boy hardware help when exact external
  behavior matters or local docs/source are insufficient.
- For debugging repo errors, use web search rarely. Prefer slow source reading,
  call-path tracing, local repros, audits, and thought-through invariants.
- For factual ASM claims, prefer primary references or upstream source; local ROM
  source and current build artifacts remain the authority for this hack.

Initial external inspiration seeds from the user-approved web pass:

- RGBDS docs: https://rgbds.gbdev.io/
- `rgbasm(5)` language docs: https://rgbds.gbdev.io/docs/master/rgbasm.5
- Pan Docs: https://gbdev.io/pandocs/
- BGB debugger/emulator homepage: https://bgb.bircd.org/
- SameBoy debugger/emulator homepage: https://sameboy.github.io/

Use these for ideas and exact external behavior, not as a substitute for local
source tracing or current ROM proof.

## Ambition Target

The user's human-vague goal for the night:

- Make the repo scarily well organized, labeled, and functional, assuming those
  qualities actually serve the ROM hack rather than just making tidy surfaces.
- Make the debugger perfect and fully finished: not merely green unit tests, but
  decision-useful outputs, honest proof boundaries, current artifacts, and a
  workflow a future agent can trust.
- If those lanes leave room, propose and execute cool repo-improving work that
  protects the First-Playthrough Promise, improves proof/debuggability, or makes
  future high-quality changes easier.
- Treat "organized" as navigable source truth and trustworthy evidence, not as
  cosmetic rearrangement.

## Non-Stop Rule

- Do not decide "enough is done" because one lane becomes green.
- Do not spend the night on trivial verification theater. A program that proves
  `2+2=4` is not a repo sweep; safe busywork is a failure mode, not prudence.
- Pick consequential work that could genuinely improve the ROM hack, proof
  story, debugging substrate, release confidence, or future-agent leverage.
- If a lane closes, pick the next best repo-improving lane from
  `docs/agent_navigation/important_improvement_menu.md` and
  `docs/project_roadmap.md`.
- A claim that the entire repo is fully swept requires stronger evidence than a
  normal overnight pass can plausibly produce. Report coverage honestly and keep
  moving to the next highest-value lane.

## Startup Reads

1. `AGENTS.md`
2. `docs/README.md`
3. `docs/project_context.md`
4. `docs/project_roadmap.md`
5. `docs/agent_navigation/start_card.md`
6. `docs/agent_navigation/important_improvement_menu.md`
7. `docs/agent_navigation/verification_matrix.md`
8. `docs/bug_hunt_master_playbook.md`
9. `docs/generated/dev_index.md` only when memory, banks, labels, or source
   anchors matter for the active lane.

## Initial Worktree Boundary

As of this note, `git status --short` is already heavily dirty, including many
Boss AI/debugger/audit/generated files and an untracked `AGENTS.md`. Treat that
as pre-existing collaborator work unless proven otherwise.

Before any implementation lane:

- Re-run `git status --short --branch`.
- Declare "my write set, your safe set, collision-risk files, tests currently
  running, files I am about to read, intended commit message."
- Avoid editing existing dirty files unless the lane genuinely requires them and
  both agents acknowledge the collision risk.
- Stage path-limited changes only. Do not sweep unrelated dirty work into a
  commit.

## Sweep Strategy

Do not try to read every file linearly. Use invariant-driven passes that end in
proof, fixes, or durable notes.

### Pass 1 - Restore The Board

Goal: know what is currently dirty, which lanes are active, and where proof is
stale.

Commands/read surfaces:

```powershell
git status --short --branch
git diff --stat
Get-Content docs\project_roadmap.md -TotalCount 260
Get-Content docs\project_completion_todo.md -TotalCount 220
```

Decision output:

- A short shared list of active dirty clusters.
- A chosen first lane, with A/B/C/D classification if scope is ambiguous.

### Pass 2 - Trust Before Novelty

Prefer these lanes before new features:

1. Release/build confidence.
2. Boss AI live proof and debugger proof boundaries.
3. Cheap difficulty and fair-loss evidence.
4. Battle-system correctness and hidden-info/timing hazards.
5. Memory/bank pressure.
6. Future-agent navigation or audit affordances that make the next decision
   easier.

### Pass 3 - Lane Execution Loop

For each lane:

1. State the invariant.
2. Identify owner files and generated/output files that must not be edited.
3. Search readers/writers/callers before patching.
4. Build the smallest falsifier: audit, test, trace, source comparison, or
   manual scenario.
5. Patch only after the causal chain is supported.
6. Run the verification row in `docs/agent_navigation/verification_matrix.md`.
7. Leave durable evidence in the right place: `audit/`, `journal/`,
   `decisions/`, roadmap, or subsystem docs.
8. If complete, choose the next lane instead of stopping.

### Pass 4 - Repo Sweep Lenses

Use these lenses repeatedly across subsystems:

- Source/build truth: Gold/Silver build, generated index staleness, release
  smoke, map/sym truth.
- Boss AI fairness: public-information-only reads, current-turn timing,
  probabilistic but explainable choices, live trace proof gaps.
- Battle correctness: side drift, register/flag/clobber contracts, scratch state
  lifetime, generated mechanics docs.
- Data correctness: constants, pointer tables, parser formats, terminators,
  names/descriptions, trainer/wild availability.
- Balance feel: weak Pokemon roles, boss pressure, level/item timing, cheapness
  vs fair danger.
- QoL feel: removes tedium without erasing preparation or old-game texture.
- Memory and banks: ROM0/WRAM/HRAM/scarce ROMX pressure before optional growth.
- Tool affordances: outputs must help a future agent make a decision, not merely
  print technically correct noise.

## Verification Floors

Use the matrix, but keep these default gates in mind:

```powershell
python tools\audit\check_navigation_floor.py
python tools\audit\check_release_smoke.py
git diff --check
```

For source changes, prefer the documented WSL build:

```powershell
bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
```

If linker outputs change and are kept:

```powershell
python scripts\generate_dev_index.py --rom pokegold
```

Do not claim gameplay proof from build, static audits, or generated docs alone.

## Commit Cadence

- Commit coherent, reviewable slices when both agents agree the slice is ready.
- Include Claude-authored dirty work only if it is part of the slice and named in
  the commit body or staged separately.
- Commit message should name the lane and evidence, not overclaim repo-wide
  completion.
- Mutual-done is the pause signal. One agent should not declare the overnight
  sweep finished unilaterally.

## First Proposed Lane

Start with a read-only restore pass over the dirty tree and roadmap, then choose
between:

- Boss AI/debugger proof gap closure, because the current dirty tree is heavily
  concentrated there.
- Release confidence/build currentness, if the dirty clusters look ready for a
  verification and checkpoint pass.
- A navigation/audit affordance only if the first two lanes are blocked or if the
  sweep reveals future agents cannot decide what to trust.

Record the actual selected lane before editing source.
