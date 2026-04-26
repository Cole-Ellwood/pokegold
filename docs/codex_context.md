# Codex Context

This file is the project intent source of truth for future Codex work. Read it
before making mechanics, balance, AI, or progression changes. If another helper
doc conflicts with the objective or fairness rules here, update that doc to match
this one.

## Agent Doc Policy

- Audience: future Codex/helper agents, not human readers.
- Optimize helper docs for rapid code navigation, source verification, and safe
  implementation.
- Prefer explicit paths, commands, labels, constraints, and current-vs-remaining
  status over explanatory prose.
- Human readability is secondary to machine-searchable facts and auditability.

## First Read Checklist

Before changing gameplay code, read these in order:

1. `docs/README.md` for helper-doc routing and truth precedence.
2. `docs/codex_context.md` for project intent.
3. `docs/project_map.md` for task routing and canonical source locations.
4. `docs/agent_navigation/README.md` for constant-time task routing, source-zone
   classification, and verification floors.
5. `docs/generated/dev_index.md` for current banks, labels, source anchors, and
   memory pressure.
6. Relevant spec/change docs, especially:
   - `docs/boss_ai_spec.md`
   - `docs/codex_review_playbook.md`
   - `docs/mechanics_changes_from_base.md`
   - `docs/manifest.md`

## North Star

This hack should make Pokemon Gold feel like a fair but very hard version of the
base game. Boss fights are the centerpiece: gym leaders, rival fights, the Elite
Four, Champion, and Red should push the player hard without cheating.

## Design Priorities

1. Boss difficulty comes first.
   - Major trainers should feel closer to a strong human opponent than the base
     Gen 2 AI.
   - The AI should be optimal enough to punish lazy play, but not deterministic
     enough to be solved like a script.
   - Good play should win through planning, adaptation, and risk management, not
     grinding or guessing hidden information.

2. Fairness is non-negotiable.
   - AI may use legal inference from observed battle state.
   - AI must not read hidden player party slots, unrevealed moves, unrevealed
     held items, private stat data, future player input, or manipulated RNG.
   - AI and player must use the same battle rules.
   - Current-turn player input is not legal evidence. If code observes a player
     switch or move during action parsing, store it as pending/current-turn data
     and only let future-turn decisions consume it.

3. Quality-of-life changes support the main game.
   - Prefer changes that reduce needless friction without removing meaningful
     battle or team-building decisions.
   - Avoid QoL changes that trivialize boss preparation.

4. Weak Pokemon should become usable.
   - Buffs should create real team-building options for Pokemon that were poor in
     the base game.
   - Buffs may be bold, but should still serve the fair-difficulty goal.

## Default Decision Rule

Gameplay comes first while preserving the Gen 2 feel where practical. If a
faithful Gen 2 behavior makes the hack less fair, less readable, or less
strategic, it can be changed. If a modern behavior improves the game but badly
damages the feel of Pokemon Gold, adapt it instead of copying it directly.

## Boss AI Invariants

- Boss AI should be strong through legal play, not hidden information.
- Allowed inputs include current public battle state, revealed player moves,
  seen player species, observed switching patterns, legal damage estimates, and
  the AI trainer's own party/moves/items.
- Forbidden inputs include unrevealed player party members, unrevealed moves,
  unrevealed held items, private stat data, future player button input, or RNG
  manipulation after choosing an action.
- Prefer weighted or probabilistic choices among strong lines over one fixed
  perfect answer. The player should not be able to solve a boss by memorizing a
  deterministic script.
- If the AI makes a surprising play, it should be explainable from information a
  strong human opponent could reasonably infer.
- Do not add boss-only battle rules unless the user explicitly asks for a
  special encounter gimmick. The default is one shared ruleset for player and AI.
- Timing matters for fairness: enemy move choice happens before player input,
  but enemy switch/item logic can happen after player action parsing. Never let
  switch/item decisions react to the player's current-turn switch input.

## Balance Defaults

- Difficulty should come from smarter opponents, better teams, and meaningful
  mechanics rather than forced grinding.
- A player who understands the mechanics and adapts should be able to win without
  hidden knowledge.
- Weak Pokemon buffs should give each species a reason to exist on a team.
  Prefer distinct roles over flattening everything into generic high stats.
- Avoid broad buffs that accidentally erase boss-fight tension or make early
  routes trivial.
- When buffing an option, check its availability, learnset, typing, held item
  synergy, and boss usage before assuming the change is isolated.

## Quality-Of-Life Defaults

- QoL should remove tedium, not decisions.
- Good QoL examples: clearer access to legal moves, fewer dead-end interactions,
  smoother party management, less repetitive menu friction.
- Risky QoL examples: unlimited healing access, free escape from strategic
  resource pressure, or changes that let players ignore boss preparation.

## Memory And Build Policy

- Developer documentation and indexes must stay outside the ROM.
- Do not edit `.gbc`, `.o`, `.map`, or `.sym` files directly.
- `pokegold.map` and `pokegold.sym` are linker outputs used as current truth for
  addresses and free space.
- Truth precedence is: current source and linker outputs first,
  `docs/generated/dev_index.md` second, and hand-authored helper docs third for
  intent and workflow. If helper docs disagree with source or linker truth,
  update the docs.
- Refresh `docs/generated/dev_index.md` after a successful build changes linker
  addresses:
  `python scripts/generate_dev_index.py --rom pokegold`
- Treat ROM0, WRAM0, WRAMX, HRAM, and nearly full ROMX banks as scarce. If new
  optional code/data does not require a tight bank, move it to roomier ROMX
  space and call it by bank-aware helpers.
- After memory-sensitive changes, compare old and new bank usage before
  declaring the work done.

## Implementation Defaults

- Prefer existing repo patterns, macros, and calling conventions.
- Keep changes near the relevant subsystem unless moving code is needed for bank
  pressure.
- For battle changes, check both player and enemy flows. Gen 2 battle code often
  has mirrored paths or side-specific state.
- For AI changes, verify no-cheating behavior by inspecting which variables are
  read.
- Boss trainers should use the boss model rather than legacy move scoring. If a
  legacy scoring helper is re-enabled for boss tiers, inspect both
  `engine/battle/ai/scoring.asm` and `engine/battle/ai/boss.asm` for hidden
  information reads.
- For data changes, check the pointer table and the data table together.
- For map or script changes, check the map script bank and any special function
  pointer it calls.
- For RAM changes, confirm the memory region has space and that save-compatible
  data is not moved casually.

## Review Defaults

- Use `docs/codex_review_playbook.md` for bug hunts and code reviews.
- Look for violations of project intent first, not just crashes.
- For Boss AI, review timing, hidden-information reads, legacy scoring helpers,
  and WRAM budget before reviewing tactical strength.
- Treat generated docs as stale if `.map`/`.sym` changed and the index was not
  regenerated.

## Done Criteria

A gameplay or AI change is not done until these are considered:

- It matches the north star and does not introduce hidden-information cheating.
- It compiles or has a clear note explaining why local build tools could not run.
- Relevant generated docs are refreshed if linker addresses changed.
- The change touches only intended source files and generated docs.
- The final explanation mentions any remaining memory pressure, test gaps, or
  behavior that needs playtesting.

## Practical Notes For Future Work

- Documentation and generated indexes must stay outside the ROM; do not spend
  cartridge space on developer-only navigation.
- Use existing source structure, labels, and RGBDS linker outputs before adding
  new abstractions.
- Consult `docs/generated/dev_index.md` before broad searches or memory-sensitive
  edits.
- Treat ROM0, WRAM, HRAM, and nearly full ROMX banks as warning zones.
