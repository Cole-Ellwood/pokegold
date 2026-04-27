# Balance Intent

Audience: future Codex/helper agents. Purpose: stop balance reviews from
reverse-engineering design intent from scattered source diffs.

## Blunt Maintainer Note

This should have already existed before broad Pokemon stat, learnset, and
evolution edits. Without a species-level intent record, every review has to
guess whether a weird Pokemon is a deliberate niche, a joke pick, a boss-only
tool, a progression gate, or just forgotten. That is wasted time, and worse, it
turns "find weak Pokemon that slipped through" into archaeology instead of
balance work.

The source still wins for exact implementation facts. This file records human
intent. If the source and this file disagree, either update the source or mark
the intent as stale instead of silently trusting either one.

## First-Playthrough Balance Promise

Balance exists to make old Pokemon knowledge incomplete again. Do not buff weak
Pokemon just to make numbers bigger. Give forgotten, strange, or historically
bad Pokemon a reason to make a veteran player hesitate, experiment, and ask
"could this actually work?"

A good buff creates discovery pressure: the player recognizes the Pokemon, but
cannot rely on the old solved tier list to dismiss it. A bad buff only inflates
stats, erases identity, or makes early Johto trivial.

## Required Balance Workflow

1. Read `docs/codex_context.md` for the project objective.
2. Read this file for species-level intent rules and unresolved design gaps.
3. Read `docs/evolution_policy.md` before judging any unevolved-looking Pokemon.
4. Regenerate and inspect `docs/generated/balance_audit.md`:

```powershell
python scripts\generate_balance_audit.py
```

5. Put unresolved candidates in `docs/buff_backlog.md` instead of leaving them
   as chat-only observations.

## Fast Source Checks

Use these before making balance claims in prose:

```powershell
rg -n -C 3 "^(Ponyta|Seel|Rhyhorn|Dragonair|Chinchou|Smoochum)EvosAttacks:" data/pokemon/evos_attacks.asm
rg -n "\b(UNOWN|DITTO|SMEARGLE|WOBBUFFET)\b" docs data engine constants -g "*.md" -g "*.asm"
git diff -- data/pokemon/evos_attacks.asm data/pokemon/base_stats scripts/generate_balance_audit.py docs/balance_intent.md docs/evolution_policy.md docs/buff_backlog.md
```

Generated audit rows are hints, not decisions. Before writing "forgotten",
"intentional", "standalone", or "gimmick", check the current source block,
`docs/evolution_policy.md`, this registry, and trainer/encounter usage.

## Intent Registry Schema

When a species is touched, add or update a row with this meaning:

| Field | Meaning |
| --- | --- |
| Pokemon | Species constant, matching `constants/pokemon_constants.asm`. |
| Intent Status | `locked`, `provisional`, `needs-review`, or `unknown`. |
| Power Tier | `early`, `midgame`, `late`, `boss-grade`, `gimmick`, or `intentionally-weak`. |
| Role | The reason this Pokemon should exist on a team. |
| Required Hooks | Stats, typing, moves, item, availability, or AI usage needed for that role. |
| Do Not Accidentally Change | Specific identity pieces future edits should preserve. |
| Open Questions | Things that still need human balance judgment. |

## Current Intent Gaps

No active top-priority gaps remain for the removed-evolution cases or documented
gimmicks listed in the manual registry below. Continue using
`docs/buff_backlog.md` and `docs/generated/balance_audit.md` for lower-priority
watchlist work.

## Documented Gimmick Audit Rule

`scripts/generate_balance_audit.py` parses locked rows with Power Tier `gimmick`
from this registry and marks them `documented-gimmick`. A Pokemon should only
have that combination after this registry states its role, required hooks, and
what future edits must preserve. Do not use `locked` plus `gimmick` to hide
unresolved weak Pokemon from the high-signal queue.

## Review Heuristics

- A low BST can be fine only if the Pokemon has a documented role that actually
  wins games: extreme speed, extreme bulk, unique typing, strong early
  availability, a unique item, a high-value support move, or a boss-specific
  tactical reason.
- If a Pokemon no longer evolves, judge it as a final form until
  `docs/evolution_policy.md` says otherwise.
- A species with no reliable STAB should have a reason: coverage attacker,
  utility specialist, status platform, or intentional gimmick.
- If a stat spread was heavily changed earlier and later regressed, do not
  assume the regression was deliberate. Put it in `docs/buff_backlog.md`.
- If a species relies on a held item, document that item. Future reviewers cannot
  infer "this is fine with Stick/Light Ball/Thick Club" from base stats alone.
- Boss usage matters. A Pokemon can be weak for the player but strong in a boss
  context if the boss supplies level, item, move timing, or team support. Record
  that explicitly.

## Manual Intent Registry

Add locked/provisional rows here as balance decisions are made.

| Pokemon | Intent Status | Power Tier | Role | Required Hooks | Do Not Accidentally Change | Open Questions |
| --- | --- | --- | --- | --- | --- | --- |
| `SEEL` | locked | early | Evolves into `DEWGONG` at level 34; not intended as a standalone final. | `EVOLVE_LEVEL, 34, DEWGONG`; normal Water TM/HM access. | Do not remove the evolution without creating a new standalone role. | None. |
| `CHINCHOU` | locked | early/midgame | Evolves into `LANTURN` at level 27; early Water/Electric utility before final bulk. | `EVOLVE_LEVEL, 27, LANTURN`; preserve Water/Electric identity. | Do not strand as a low-BST final by removing evolution again. | None. |
| `SMOOCHUM` | locked | early/midgame | Evolves into `JYNX` at level 30; baby stats are not meant to carry a final role. | `EVOLVE_LEVEL, 30, JYNX`; Ice/Psychic TM coverage. | Do not rely on baby stats plus TMs as final-form compensation. | None. |
| `PONYTA` | locked | midgame | Evolves into `RAPIDASH` at level 40; fast Fire attacker progression line. | `EVOLVE_LEVEL, 40, RAPIDASH`; Fire Blast and speed identity. | Keep Rapidash reachable from Ponyta unless explicitly re-splitting the line. | None. |
| `RHYHORN` | locked | midgame | Evolves into `RHYDON` at level 42; physical Ground/Rock tank line. | `EVOLVE_LEVEL, 42, RHYDON`; Earthquake/Rock Slide access. | Do not leave Rhyhorn as a slow low-special-bulk final. | None. |
| `DRAGONAIR` | locked | late | Evolves into `DRAGONITE` at level 55; late pseudo-legend progression. | `EVOLVE_LEVEL, 55, DRAGONITE`; slow-growth Dragon availability. | Avoid cheap early Dragonite access, but keep the line intact. | None. |
| `UNOWN` | locked | gimmick | One-move Hidden Power specialist and Ruins collection reward. | Raw stats `148/102/48/48/102/48`; Hidden Power-only levelset. | Preserve one-move identity unless adding an explicit Unown-only mechanic. | Needs playtesting for encounter timing and Hidden Power variance. |
| `DITTO` | locked | gimmick | Imposter-style auto-transform utility with extra HP, but not a high-HP mirror-sweeper by default. | Raw stats `100/48/48/48/48/48`; `engine/battle/ditto_imposter.asm`; Transform legality. | Do not add normal attacking coverage or inflate HP without rechecking Transform math. | Needs playtesting for player value and boss abuse risk. |
| `SMEARGLE` | locked | gimmick | Fast custom toolkit through repeated Sketch access. | Raw stats `90/45/75/110/45/75`; Sketch every 10 levels. | Preserve Sketch-only identity, low direct offense, and below-elite Speed. | Needs progression audit for practical move acquisition. |
| `WOBBUFFET` | locked | gimmick | High-HP reactive trap using Counter, Mirror Coat, Safeguard, and Destiny Bond. | Raw stats `220/33/65/33/33/65`; reactive move kit; AI fairness checks. | Do not evaluate with normal attacking coverage or generic STAB heuristics. | Needs boss/player fairness playtest. |
| `FARFETCH_D` | provisional | midgame | Stick-backed physical crit attacker that gives Route 38 a strange-but-real Normal/Flying pickup instead of a solved joke bird. | Raw stats `60/130/55/60/58/62`; wild held items `STICK, STICK`; Peck, Fury Attack, Wing Attack, Swords Dance, Slash, False Swipe; Cut/Fly/Steel Wing TM/HM access. | Preserve low bulk and middling Speed; do not turn it into generic Dodrio/Fearow speed offense or remove the Stick dependency. | Playtest Route 38 catch feel and Bird Keeper Jose/Perry trainer showcases. |
| `ARIADOS` | provisional | midgame | Slow Bug/Poison hazard trapper: it wins value by laying Spikes, slowing or trapping, and draining/statusing while its bulk buys turns. | Raw stats `110/90/100/40/60/60`; Ariados gets `SPIKES` at level 22 on evolution and `SPIDER_WEB` by level 37; Leech Life, Toxic/Sludge Bomb/Giga Drain TM access; Koga showcases Spikes/Toxic/Giga Drain/Spider Web. | Preserve low Speed and non-sweeper damage; do not fix it by making it a generic fast Bug attacker or by hiding its utility behind reminder-only level 1 moves. | Playtest evolved Spinarak around level 22-37 and Koga's trap/hazard turn feel. |
| `LEDIAN` | provisional | midgame | Fast Bug/Flying screen passer and baton tempo piece that gives Bugsy a support role without relying on Pineco's Spikes/Rapid Spin package. | Raw stats `90/115/65/105/45/120`; Leech Life, Wing Attack, Reflect, Light Screen, Quiver Dance, Baton Pass. | Preserve fast support identity; do not turn it into a generic special Quiver sweeper. | Watch early Bugsy pacing and player access timing. |
| `DEWGONG` | provisional | midgame | Bulky Ice/Water utility spinner that can Encore, Haze, and pressure Dragons/Grass without borrowing Starmie. | Raw stats `120/70/95/80/95/105`; Rapid Spin, Encore, Ice Beam, Haze. | Preserve defensive Ice utility; do not flatten into another pure Surf/Ice Beam Water. | Watch midgame durability around Pryce. |
| `JYNX` | provisional | late | Frail fast Ice/Psychic sleep breaker used when a Psychic team wants special pressure without another Starmie/Alakazam clone. | Raw stats `75/50/55/115/135/95`; Lovely Kiss, Ice Beam, Psychic, Perish Song. | Preserve frailty and sleep-risk identity. | Watch Lovely Kiss swinginess in Sabrina. |
| `LANTURN` | provisional | late | Bulky Water/Electric pivot that replaces generic Starmie/Kingdra coverage with slower status pressure and mixed resist utility. | Raw stats `125/58/76/75/105/105`; Thunder Wave, Thunderbolt, Surf, Ice Beam, Calm Mind, Hydro Pump. | Preserve low-physical-offense pivot identity. | Watch Water-type power creep. |
| `SUDOWOODO` | provisional | midgame/late | Slow Rock wall and phazing hazard carrier for teams that previously used Onix/Donphan as generic Rock/Ground glue. | Raw stats `90/125/145/45/30/75`; Rock Slide, Low Kick, Spikes, Roar, Earthquake TM. | Preserve slow physical wall identity; do not make it fast or specially offensive. | Watch whether Chuck and Brock uses feel distinct. |
| `POLITOED` | provisional | late | Rain support Water with sleep pressure and enough bulk to be a real Misty alternative to Cloyster/Kingdra. | Raw stats `100/70/80/85/115/105`; Rain Dance, Hypnosis, Hydro Pump, Ice Beam, Quiver Dance. | Preserve support Water identity; do not outclass Lapras as the bulky Ice answer. | Watch overlap with Lapras on Misty. |
| `MANTINE` | provisional | late | Water/Flying special wall and hazard-control pivot that lets Dragon teams answer Ice/Water pressure without Donphan. | Raw stats `95/40/85/90/105/140`; Rapid Spin, Haze, Wing Attack, Hydro Pump, Confuse Ray. | Preserve special-wall identity and low Attack. | Watch if Rapid Spin reads naturally enough. |
| `QWILFISH` | provisional | late | Fast Poison/Water Spikes trade piece for poison teams, with enough speed and Attack to threaten before exploding. | Raw stats `85/105/130/95/65/65`; Spikes, Sludge Bomb, Surf, Explosion, Hydro Pump. | Preserve spiky physical utility identity. | Watch Explosion pressure in Janine. |
| `CORSOLA` | provisional | late | Rock/Water Recover spinner for Rock teams that need hazard control without importing Donphan or Starmie. | Raw stats `95/80/130/45/75/130`; Spikes, Recover, Rapid Spin, Toxic, Rock Slide. | Preserve slow defensive utility identity. | Watch late Brock stall pacing. |
| `ELECTRODE` | provisional | late | Electric-team hazard control through a literal fast spinning ball, replacing off-type Donphan glue on Surge. | Rapid Spin added to existing fast Electric/Explosion kit. | Preserve frailty; do not add bulk to make the fastest spinner too safe. | Watch if Rapid Spin plus Explosion is too clean. |
| `DELIBIRD` | provisional | midgame/late | Special-delivery Ice/Flying utility wall: still goofy because `PRESENT` exists, but no longer only a joke. | Raw stats `100/55/45/75/65/150`; Present, Quick Attack, Icy Wind, Aurora Beam, Agility, Wing Attack, Haze, Blizzard. | Preserve Present identity, low physical offense, and Silver-only late-midgame catch timing; do not turn it into a generic high-damage Ice sweeper. | Playtest Ice Path catch feel and Pokefan Colin's level 32 showcase. |
