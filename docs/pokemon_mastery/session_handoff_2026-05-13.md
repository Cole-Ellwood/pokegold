# Pokemon Mastery Session Handoff - 2026-05-13

Purpose: start a fresh Codex session without losing the Pokemon mastery study
state. The previous chat became too large and buggy, so this file records the
active goal, current artifacts, worktree context, and a copy-paste startup
prompt for the next session.

## Current Goal State

Previous thread goal status: paused, not complete.

Objective:

```text
Become a strategically competent high-level Pokemon singles advisor, roughly
equivalent to a solid 1500-ELO player, by studying expert Pokemon play,
maintaining a concise cookbook-style mastery notebook, reviewing long battles,
using simulations/calculators as grounding, and learning to advise Pokemon Gold
romhack / Gym Leader Lab boss battles with strong turn-1 planning, long-term
win-route tracking, plan revision, and romhack-specific mechanic validation.
```

Do not mark the goal complete. The current state is progress, not mastery. The
goal remains open until unseen long-form battles and practical boss-battle turn
advice demonstrate strong route planning, plan revision, and romhack-specific
mechanic handling.

## User Preferences That Matter

- Use web search constantly when useful. Smogon is the primary expert resource.
- Spend most work time studying expert play and converting it into practical
  move-choice lessons, not expanding tooling or broad prose.
- Treat local user examples and RLHF cards as light calibration only.
- Keep the notebook as a cookbook for turn advice, not a strategy essay.
- Do not overfocus Snorlax as a species. GSC Snorlax material is valuable as a
  proxy for anchor preservation, Rest cycles, setup denial, and long-term route
  conversion, but most Gym Leader Lab bosses use other anchor/converter shapes.
- Treat Gym Leader Lab as a mechanics fork. Local source/docs/debugger evidence
  outrank generic Pokemon memory and Pokemon Showdown behavior for romhack
  claims.
- The AI lab / preference-card system is not law. Use local boss rosters,
  local mechanics, expert play, and route reasoning.
- Eventually validate with real or simulated boss battles against a non-self
  opponent model, aiming for 80%+ over 50+ battles only after simulator trust is
  established.

## Repository / Git Context

Workspace:

```text
C:\Users\lolno\Downloads\pokemon gold hack
```

Current branch when this handoff was written:

```text
codex/cleanup-gsc-rebalance-split
```

Important worktree note:

- The worktree is dirty.
- `docs/pokemon_mastery/` is currently untracked as a directory.
- Many `audit/boss_ai_preference/*` and `tools/boss_ai_preference/*` files are
  also modified or untracked from prior work.
- Do not revert or clean these files unless the user explicitly asks.
- Do not stage or commit unless the user asks.

Useful status command:

```powershell
git status --short -- docs\pokemon_mastery tools\boss_ai_preference audit\boss_ai_preference
```

## Core Notebook Files

Start here:

```text
docs/pokemon_mastery/active_goal.md
docs/pokemon_mastery/README.md
docs/pokemon_mastery/training_cycle.md
docs/pokemon_mastery/cookbook.md
docs/pokemon_mastery/source_to_policy_ledger.md
docs/pokemon_mastery/boss_turn_advice_template.md
docs/pokemon_mastery/paused_turn_atlas.md
docs/pokemon_mastery/boss_route_maps/README.md
docs/pokemon_mastery/worked_examples/boss_live_turn_prompt_cards.md
docs/pokemon_mastery/worked_examples/boss_live_turn_practice_run_2026-05-13.md
docs/pokemon_mastery/worked_examples/live_turn_drills.md
```

High-value support directories:

```text
docs/pokemon_mastery/boss_route_maps/
docs/pokemon_mastery/worked_examples/
docs/pokemon_mastery/reviews/
docs/pokemon_mastery/romhack_deltas/
docs/pokemon_mastery/workspace/pro_notes/
```

Local mechanics/source anchors:

```text
data/trainers/parties.asm
data/moves/moves.asm
data/types/type_matchups.asm
docs/agent_navigation/gen2_vs_modern_mechanics.md
docs/agent_navigation/hack_mechanics_reference.md
engine/battle/type_passive_damage_mods.asm
engine/battle/move_effects/spikes.asm
engine/battle/move_effects/rapid_spin.asm
engine/battle/core.asm
```

## Recent Work Completed In The Large Session

The recent focus was turning expert/source lessons into live boss prompt cards
and practice answers. These were added or updated:

```text
docs/pokemon_mastery/source_to_policy_ledger.md
  STP-040: Encore Punishes The Last Executed Move

docs/pokemon_mastery/cookbook.md
  Recipe: Encore Target Discipline

docs/pokemon_mastery/boss_route_maps/pryce_turn1_route_sheet.md
  Dewgong Encore check

docs/pokemon_mastery/worked_examples/live_turn_drills.md
  Drill 038: Encore Target Versus Safe-Looking Support

docs/pokemon_mastery/paused_turn_atlas.md
  PTA-030: Encore Last-Move Lock Or Support Autopilot
  PTA-031: Obvious KO Into Temporary Trade State
  PTA-032: Clock Ownership Or Slow-Control Autopilot
  PTA-033: Set-Retain-Convert Hazard War
  PTA-034: Receiver-First Support Chain
  PTA-035: Rest-Only Anchor Versus RestTalk Autopilot

docs/pokemon_mastery/worked_examples/boss_live_turn_prompt_cards.md
  Card 009: Pryce Dewgong Encore / Spin Turn
  Card 010: Blaine Ninetales Weather / Safeguard Posture
  Card 011: Janine Explosion Trade Into Breaker Route
  Card 012: Morty Destiny Bond / Temporary Control Turn
  Card 013: Koga Poison / Trap Clock Ownership
  Card 014: Jasmine Set-Retain-Convert Hazard War
  Card 015: Bugsy Support Chain Into Scyther
  Card 016: Will Slowbro Rest / Amnesia Anchor

docs/pokemon_mastery/worked_examples/boss_live_turn_practice_run_2026-05-13.md
  Practice answers for Cards 009-016 and updated run findings.
```

The major lessons from those additions:

- Encore is priced from the exact last executed move and the route its 3-6 turn
  lock creates, not from a generic fear of support moves.
- Risk posture matters: "safe" is only safe if it preserves a winning route.
- Explosion and sacrifice are route trades. The lost role matters more than
  the current HP total.
- Destiny Bond and temporary-control states can make an obvious KO wrong.
- Poison/trap/hazard clocks are good only for the side that converts the next
  few turns.
- Hazards need set, retain, and convert. A layer is not inherently progress.
- Support chains are judged by the receiver, not by the support user's damage.
- Rest-only and RestTalk anchors have different branch trees; verify the actual
  local moveset.

## Verification State

Last repeated verification command:

```powershell
python -m unittest tools.boss_ai_preference.tests.test_type_evidence tools.boss_ai_preference.tests.test_benchmark_positions
```

Last observed result:

```text
Ran 18 tests
OK
```

Trailing whitespace scans on edited Pokemon mastery docs were clean.

Useful check command:

```powershell
$files = @(
  'docs\pokemon_mastery\worked_examples\boss_live_turn_prompt_cards.md',
  'docs\pokemon_mastery\worked_examples\boss_live_turn_practice_run_2026-05-13.md',
  'docs\pokemon_mastery\paused_turn_atlas.md',
  'docs\pokemon_mastery\source_to_policy_ledger.md',
  'docs\pokemon_mastery\cookbook.md',
  'docs\pokemon_mastery\worked_examples\live_turn_drills.md',
  'docs\pokemon_mastery\boss_route_maps\pryce_turn1_route_sheet.md'
)
foreach ($f in $files) {
  Select-String -Path $f -Pattern '[ \t]+$' |
    ForEach-Object { "${f}:$($_.LineNumber): trailing whitespace" }
}
```

## Best Next Concrete Action

The previous session was about to add a delayed-pressure live prompt:

```text
Will Xatu Future Sight / Houndoom Pursuit delayed-pressure turn
```

Reason:

- The prompt set now covers Encore, weather/Safeguard, Explosion, Destiny Bond,
  poison/trap clocks, hazard wars, support chains, and Rest cycles.
- It still needs a clean delayed-effect case where the important question is
  not "what happens this turn?" but "which Pokemon is forced to be active when
  Future Sight resolves, and does Pursuit punish the escape?"

Relevant source artifacts:

```text
docs/pokemon_mastery/boss_route_maps/will_turn1_route_sheet.md
docs/pokemon_mastery/source_to_policy_ledger.md
  STP-033: Delayed Effects Must Own The Resolution Turn
docs/pokemon_mastery/cookbook.md
  Recipe: Delayed-Damage Ledger Test
docs/pokemon_mastery/worked_examples/live_turn_drills.md
  Drill 029: Delayed Effect Versus Current-Turn Autopilot
```

Suggested additions:

```text
docs/pokemon_mastery/worked_examples/boss_live_turn_prompt_cards.md
  Card 017: Will Future Sight / Pursuit Resolution Turn

docs/pokemon_mastery/worked_examples/boss_live_turn_practice_run_2026-05-13.md
  Practice answer for Card 017

docs/pokemon_mastery/paused_turn_atlas.md
  PTA-036: Delayed Hit Resolution Or Current-Turn Autopilot
```

Use web search for Smogon delayed-effect / Future Sight / Doom Desire material
if needed, but local Will route sheet and local Future Sight source are the
romhack authority.

## Copy-Paste Prompt For New Session

```text
We are starting a fresh Codex session because the previous Pokemon mastery
thread became too large and buggy. Continue from the existing repo state rather
than restarting from scratch.

Workspace:
C:\Users\lolno\Downloads\pokemon gold hack

Branch at handoff:
codex/cleanup-gsc-rebalance-split

First, inspect the current goal and notebook state. If the goal tool is
available and there is no active goal, create this long-running goal. If a goal
already exists, do not duplicate it. Do not mark it complete:

Become a strategically competent high-level Pokemon singles advisor, roughly
equivalent to a solid 1500-ELO player, by studying expert Pokemon play,
maintaining a concise cookbook-style mastery notebook, reviewing long battles,
using simulations/calculators as grounding, and learning to advise Pokemon Gold
romhack / Gym Leader Lab boss battles with strong turn-1 planning, long-term
win-route tracking, plan revision, and romhack-specific mechanic validation.

Operating emphasis:
- Use web search constantly when useful; Smogon is the primary expert resource.
- Spend most work time studying expert play and reviewing games, not building
  tooling or broad notebook prose.
- Maintain the Pokemon mastery notebook as a concise cookbook for real battle
  advice.
- Convert source lessons into concrete artifacts: source-to-policy entries,
  paused-turn drills, live boss prompt cards, boss route maps, battle reviews,
  or mechanics checks.
- Use local RLHF/preference cards only as calibration, not as the curriculum.
- Keep vanilla GSC, later-generation abstract strategy, and Gym Leader Lab
  romhack mechanics separate.
- Treat the romhack as a mechanics fork. Local docs/source/debugger/fixtures
  outrank Pokemon Showdown and generic memory for romhack claims.
- Do not overfocus Snorlax as a species. Use Snorlax-heavy GSC material as a
  proxy for anchor preservation, Rest cycles, setup denial, Explosion trades,
  and long-term route conversion.
- Do not mark this goal complete until unseen long-form battles and practical
  boss-battle turn advice demonstrate strong route planning, plan revision,
  and romhack-specific mechanic handling.

Read these files first:
docs/pokemon_mastery/session_handoff_2026-05-13.md
docs/pokemon_mastery/active_goal.md
docs/pokemon_mastery/README.md
docs/pokemon_mastery/training_cycle.md
docs/pokemon_mastery/cookbook.md
docs/pokemon_mastery/source_to_policy_ledger.md
docs/pokemon_mastery/boss_turn_advice_template.md
docs/pokemon_mastery/paused_turn_atlas.md
docs/pokemon_mastery/boss_route_maps/README.md
docs/pokemon_mastery/worked_examples/boss_live_turn_prompt_cards.md
docs/pokemon_mastery/worked_examples/boss_live_turn_practice_run_2026-05-13.md

Important recent additions already done:
- STP-040: Encore Punishes The Last Executed Move
- Recipe: Encore Target Discipline
- Drill 038: Encore Target Versus Safe-Looking Support
- Boss prompt Cards 009-016:
  Pryce Dewgong Encore / Spin Turn
  Blaine Ninetales Weather / Safeguard Posture
  Janine Explosion Trade Into Breaker Route
  Morty Destiny Bond / Temporary Control Turn
  Koga Poison / Trap Clock Ownership
  Jasmine Set-Retain-Convert Hazard War
  Bugsy Support Chain Into Scyther
  Will Slowbro Rest / Amnesia Anchor
- Paused-turn atlas entries PTA-030 through PTA-035 for those patterns.

Git/worktree caution:
- The repo is dirty.
- docs/pokemon_mastery/ is untracked.
- audit/boss_ai_preference/ and tools/boss_ai_preference/ include modified and
  untracked files from prior work.
- Do not revert, clean, stage, or commit unless explicitly asked.

Verification that has been passing:
python -m unittest tools.boss_ai_preference.tests.test_type_evidence tools.boss_ai_preference.tests.test_benchmark_positions

Best next concrete action:
Add a delayed-pressure practice artifact for Will Xatu / Future Sight / Pursuit.
The goal is to train planning around the resolution turn, not the setup turn.
Suggested files to edit:
- docs/pokemon_mastery/worked_examples/boss_live_turn_prompt_cards.md
  Add Card 017: Will Future Sight / Pursuit Resolution Turn
- docs/pokemon_mastery/worked_examples/boss_live_turn_practice_run_2026-05-13.md
  Add the practice answer for Card 017
- docs/pokemon_mastery/paused_turn_atlas.md
  Add PTA-036: Delayed Hit Resolution Or Current-Turn Autopilot

Relevant local/expert anchors:
- docs/pokemon_mastery/boss_route_maps/will_turn1_route_sheet.md
- source_to_policy_ledger.md STP-033: Delayed Effects Must Own The Resolution Turn
- cookbook.md Recipe: Delayed-Damage Ledger Test
- worked_examples/live_turn_drills.md Drill 029
- Local Future Sight sources listed in Will route sheet:
  data/moves/moves.asm
  engine/battle/move_effects/future_sight.asm
  engine/battle/core.asm
- Use web search for Smogon Future Sight / Doom Desire or delayed-pressure
  material if useful, but local source is the authority for romhack behavior.

Expected style:
- Before editing, inspect the relevant files and local patterns.
- Keep edits scoped.
- Prefer practical move-choice artifacts over broad prose.
- After editing, run the existing unittest command and a trailing whitespace
  scan on edited docs.
- Final response should say what changed, what source/expert anchors were used,
  what tests passed, and that the goal remains incomplete.
```
