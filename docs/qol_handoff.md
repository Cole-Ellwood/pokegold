# Low-Risk QoL Handoff

This handoff is for implementing quality-of-life changes in this Pokemon Gold
hack without drifting from the project intent.

## Read First

- `docs/codex_context.md`: project intent. QoL should remove tedium, not
  decisions, and must not trivialize boss preparation.
- `docs/project_map.md`: routing guide for source areas.
- `docs/generated/dev_index.md`: source anchors and memory pressure. Treat ROM0,
  WRAM0, WRAMX, HRAM, and tight ROMX banks as scarce.
- `docs/mechanics_changes_from_base.md`: confirms existing QoL/mechanics. Do not
  re-suggest or duplicate Move Reminder, TM Tutor, voucher rewards, branching
  evolution choice, or trainer-battle bag restrictions.

The worktree may already be dirty. Do not revert unrelated user or previous
Codex changes. Do not edit generated ROM/linker artifacts by hand.

## First-Playthrough QoL Boundary

QoL exists to let the player stay immersed in scary, unknown Johto, not to make
the journey frictionless. Remove menu pain, unclear service discovery, and
needless repetition. Preserve preparation, route pressure, resource decisions,
and the slight old-game texture that makes the world feel larger than the
player.

If a convenience makes a veteran stop respecting routes, bosses, items, or team
prep, it works against the hack even when it feels modern.

## Current Status And Recommended Order

Already implemented low-risk QoL in this handoff:

- Default new games to FAST text speed.
- Move Reminder page size is `4`.
- Bicycle auto-registers on receipt when no valid item is already registered.

Recommended remaining order:

1. Tighten/help text for new custom items and TM Voucher.
2. Add/adjust Day-Care signage or NPC text pointing to the TM Tutor and Move
   Reminder.
3. Consider Repel renewal prompt last; it is useful but has the most edge cases.
4. Consider Pokemon Center pause trimming only if it preserves heal animation,
   music restart, and Pokerus behavior.

Avoid running shoes, free portable PC, reusable TMs, cheaper/free healing, EXP
changes, or HM removal as "low-risk" QoL. Those affect pacing, boss prep,
resource pressure, or Gen 2 feel.

## Already Implemented

### Default Text Speed FAST

- Source: `data/default_options.asm`.
- Current state: the first `wOptions` byte is `TEXT_DELAY_FAST`.
- Scope: new games only; existing saves keep their saved option.
- Verify: new-game defaults show FAST in the Options menu; cycling FAST/MID/SLOW
  still works.

### Move Reminder Page Size

- Source: `engine/events/move_reminder.asm`.
- Current state: `MOVE_REMINDER_PAGE_SIZE` is `4`.
- Do not raise it to `5` with the current scratch layout. Worst-case 5 move
  names plus `NEXT` and `CANCEL` needs 79 bytes, while the contiguous scratch
  area from `wStringBuffer2` through `wStringBuffer5` is 70 bytes.
- Edge cases:
  - no available moves still prints the no-moves text;
  - exactly page-size moves shows no `NEXT`;
  - page-size + 1 moves shows `NEXT` and then remaining moves;
  - `CANCEL` always exits;
  - long move names do not overwrite window borders.
- Verify manually if possible with a species that has many reminder moves.

### Auto-Register Bicycle If Empty

- Sources: `maps/GoldenrodBikeShop.asm`, `engine/overworld/select_menu.asm`,
  `engine/items/pack.asm` for registration behavior reference.
- Current state: `GoldenrodBikeShopAutoRegisterBicycle` runs only after
  `giveitem BICYCLE` succeeds. It calls `CheckRegisteredItem` first, so existing
  valid registrations are preserved and stale registrations are cleared.
- It sets both:
  - `wWhichRegisteredItem`: key-item pocket encoded with registered slot number.
  - `wRegisteredItem`: `BICYCLE`.
- It mirrors the key-item registration encoding from `RegisterItem` in
  `engine/items/pack.asm`; do not call `RegisterItem` directly from the map
  script.
- Edge cases:
  - player already has another registered item: leave it alone;
  - player receives Bicycle with nothing registered: SELECT uses Bicycle;
  - full key-item pocket: do not set `EVENT_GOT_BICYCLE`;
  - if Bicycle is somehow removed, existing `CheckRegisteredItem` clears stale
    registration.
- Verify: receive Bicycle, press SELECT outside; repeat with another registered
  item already set.

## Remaining Candidates

### Clearer Custom Item Text

- Main sources: `data/items/descriptions.asm`, possibly map/gym text where
  vouchers are mentioned.
- Keep item order and pointer table alignment unchanged.
- Respect two-line item description constraints. Short text is safer than exact
  mechanical detail that overflows or misleads.
- Good targets:
  - `TMVoucherDesc`: point to TM Tutor by Day-Care.
  - `ChoiceBandDesc`, `ChoiceSpecsDesc`, `ChoiceScarfDesc`: mention boost plus
    move lock.
  - `AssaultVestDesc`: mention Sp.Def boost and status-move block.
  - `EvioliteDesc`, `AirBalloonDesc`, `ShellBellDesc`, `MetronomeItemDesc`.
- Verify: build succeeds; item descriptions render without wrapping into nearby
  UI.

### Day-Care Service Signage

- Source: `maps/DayCare.asm`.
- Prefer text-only changes or an existing background event if practical.
- Do not add event flags or persistent state.
- Do not disturb Day-Care egg/mon callbacks or object positions unless necessary.
- Goal: make it clear that the Day-Care contains both the TM Tutor and Move
  Reminder, and that TM Vouchers become lesson credits there.
- Verify: Day-Care loads, egg callback behavior still works, both service NPCs
  remain reachable.

### Repel Renewal Prompt

- Sources: `engine/overworld/events.asm`, `engine/events/repel.asm`,
  `engine/items/item_effects.asm`, `data/text/common_1.asm`.
- Current flow: `DoRepelStep` decrements `wRepelEffect`; when it reaches zero it
  calls `RepelWoreOffScript` and returns carry, causing the step not to continue
  into poison/egg/Day-Care/bike-step processing during that same event.
- This is the riskiest QoL item. Keep it isolated and test hard.
- Must preserve:
  - no prompt if no Repel items are available;
  - old wore-off message when no renewal occurs;
  - no item consumption unless renewal succeeds;
  - correct item priority, preferably Max Repel, then Super Repel, then Repel;
  - no wild encounter on the exact step where the prompt runs;
  - Bug Contest, poison, egg, Day-Care, bike-shop call, and link-room behavior.
- Avoid new WRAM/SRAM. Use existing script variables/buffers if needed, or a
  small farcall helper in roomy ROMX space if script-only logic becomes awkward.
- Verify:
  - Repel wears off with none in bag;
  - with only Repel, only Super Repel, only Max Repel, and multiple types;
  - declining renewal;
  - accepting renewal consumes exactly one item and sets correct step count;
  - step counters and poison/egg behavior continue normally afterward.

### Pokemon Center Friction Trim

- Source: `engine/events/std_scripts.asm`, `PokecenterNurseScript`.
- Lowest-risk approach: reduce pauses only, not flow.
- Do not remove:
  - initial heal yes/no prompt;
  - `special HealParty`;
  - `HealMachineAnim`;
  - `special RestartMapMusic`;
  - Pokerus check and phone call behavior;
  - nurse turnobject sequence unless visually tested.
- Verify repeated healing, no-heal decline, Pokerus first detection, and music
  restoration after healing.

## Verification Checklist

- Run a build if tools are available. On this Windows workspace, previous docs
  noted `make` may not be on `PATH`; check before assuming.
- Run relevant audits when touched areas overlap:
  - `python tools\audit\check_release_smoke.py`
  - `python tools\audit\check_docs_navigation.py`
- If linker outputs change and are kept, refresh:
  - `python scripts\generate_dev_index.py --rom pokegold`
- Check `git diff --stat` and inspect the actual diff before final response.
- Do not include `.gbc`, `.o`, `.map`, `.sym`, `dist/`, `.local/`, `outbox/`, or
  scratch artifacts unless explicitly requested.

## Suggested First Batch

For a safe next implementation pass, do only:

- clearer custom item descriptions / voucher text;
- Day-Care text/signage hint.

Leave Repel renewal and Pokemon Center trimming for a second pass unless the user
explicitly wants them now.
