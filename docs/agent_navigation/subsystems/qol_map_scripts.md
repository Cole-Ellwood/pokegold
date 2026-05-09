# QoL And Map Script Micro-Index

Use this when the task mentions QoL, friction, Day-Care service text, Repel,
Pokemon Center timing, NPC text, map scripts, specials, or event routing.

QoL promise: remove needless friction so the player can stay in the journey.
Do not remove the preparation, route pressure, or old-game texture that helps
Johto feel bigger than the player.

## Fast Route

| Need | Go to |
| --- | --- |
| QoL policy and remaining candidates | `docs/qol_handoff.md` |
| Project guardrails | `docs/project_context.md` |
| Map/script source routing | `docs/project_map.md`, `docs/generated/dev_index.md` |
| Map scripts | `maps/` |
| Map attributes/data | `data/maps/` |
| Specials | `engine/events/specials.asm`, `data/events/special_pointers.asm` |
| Overworld step events | `engine/overworld/`, `engine/overworld/events.asm` |
| Standard scripts | `engine/events/std_scripts.asm` |

## Current QoL Shape

Already implemented:

- FAST text speed for new games.
- Move Reminder page size `4`.
- Bicycle auto-register after receipt when no valid item is already registered.
- Custom held-item description cleanup.
- Route 34 / Day-Care service text for Move Reminder discovery.
- Pokemon Center pause trimming that preserves the same heal flow.
- Repel renewal prompt with Max Repel, Super Repel, Repel priority.
- Constrained HM-slot relief: seven key items handle field use while badge/story
  gates remain, and the former HM discs behave as TM51-TM57. The implementation
  uses the existing key-item pocket size exactly; do not add another key item
  here without handling capacity or removing a key item.
  The tools are registerable `CANT_TOSS` key items, old HM reward flags can
  backfill missing tools for legacy saves, and badge/advice text should keep
  naming the replacement tools rather than "Pokemon must know the HM" wording.

No low-risk QoL candidate from `docs/qol_handoff.md` is currently queued.
Reopen this lane only for manual Repel feel checks, a bug report, or a new QoL
candidate that respects the pacing guardrails.

Do not treat running shoes, reusable TMs, free portable PC, cheaper/free healing,
EXP changes, or further route-skip/HM expansion as low-risk QoL. Those touch
pacing, resource pressure, boss preparation, or Gen 2 feel.

## Map Script Edit Checklist

Before editing a map/script:

1. Locate the map file under `maps/`.
2. Check `docs/generated/dev_index.md` for its map-script bank and free space.
3. Check any special pointer in `data/events/special_pointers.asm`.
4. Prefer text-only changes when the task is communication/signage.
5. Avoid new event flags, WRAM, or persistent state unless the feature truly
   requires it.

## Repel And Pokemon Center Caution

Repel renewal must preserve step-event ordering, poison, egg, Day-Care, bike
shop call, link-room behavior, item priority, and no-consumption-on-decline.
It must not offer Bag-item renewal while `ENGINE_BUG_CONTEST_TIMER` is set.
`python tools\audit\check_release_smoke.py` now guards the source-level item
priority and step-count writes, but it is not a substitute for emulator feel.

Pokemon Center trimming must preserve the heal prompt, `special HealParty`,
`HealMachineAnim`, `special RestartMapMusic`, Pokerus checks, phone behavior,
and nurse facing/turn sequence unless visually tested.

## Verification

Use `docs/agent_navigation/verification_matrix.md` row
`Docs-only routing, roadmap, handoff, or organization` for docs routing, or
`Map scripts, events, specials, QoL scripts` for source changes. Build both ROMs
after source changes and name any manual emulator gap. Map and QoL changes are
especially prone to "compiled but not experienced" false confidence.
