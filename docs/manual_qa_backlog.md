# Manual QA Backlog

Things that **a human playing the ROM** needs to verify, because audits can't.
Coding agents cannot read this off the source.

If audits cover it, **don't list it here** — point at the audit instead.
This file is the inventory of *unaudited* surface area, not a re-statement
of what `tools/audit/check_release_smoke.py` already proves.

## How to read a row

Each item:
- **What** — concrete in-game scenario (specific Pokemon, level, move, map).
- **Why** — the audit gap. What can't be proven from source alone.
- **How to test** — the steps a player runs.
- **Last verified** — date + ROM SHA1 + outcome, or `pending`.

Rows live under one of the **Areas** below. Add new rows under the right
area; create a new area only when none of the existing ones fit.

## Areas

### Save format

| What | Why | How to test | Last verified |
| --- | --- | --- | --- |
| Fresh save → quit → load on same ROM | `SAVE_FORMAT_VERSION=1` was just wired; round-trip never been played. | New game → save → reset → load. Confirm party / location / time match. | pending |
| Hall of Fame survives save/load | HoF lives in its own SRAM section that the marker doesn't touch; no audit confirms layout-stable across builds. | Beat E4 → enter HoF → save → reset → re-enter HoF screen, confirm team renders. | pending |
| Active Box survives save/load | Box layout sits immediately after the new marker byte in SRAM bank 1. Audit fingerprints the labels but not on-cart byte alignment. | Deposit a Pokemon → save → reset → withdraw, confirm the same Pokemon. | pending |
| Legacy save (pre-marker SHA `7de0879a`) loads or rejects cleanly | `$FF` graceful migration path is implemented but never run on a real legacy save. Wrong outcome = silent data corruption, not a crash. | Apply `dist/pokegold-data-rebalance.bps` to the baseline and load with the current ROM. Either it loads with no glitches OR it shows "no save" — anything in between is a bug. | pending |

### Boss AI fairness

| What | Why | How to test | Last verified |
| --- | --- | --- | --- |
| Each gym leader feels fair at intended level | Boss AI overlay is on top of vanilla scoring; "feel" is not an audit-able property. The full list with rationales lives in `docs/boss_ai_bug_testing_plan.md`. | Run the per-leader scenarios from `docs/boss_ai_bug_testing_plan.md`. | pending |
| Whitney with a level-18 Geodude wipes (still) | Cited as a deliberate difficulty case in `CLAUDE.md`. If she stops wiping, the rebalance overshot. | Train a Geodude to level 18, fight Whitney, record outcome. | pending |
| Rival fights show the right plan flavor per stage | Plan/role logic per boss lives in `boss.asm` `.rival:2101` etc. — code is audited, *intent* isn't. | Fight rival at each appearance; note whether his lead picks and switches feel deliberate. | pending |
| Champion fight uses ace-timing hook visibly | `BossAI_AceTimingHook:3794` exists but no audit proves the timing reads as intended. | Reach Lance, observe whether his ace switch-in feels paced. | pending |
| Choice-locked boss mon never picks an unlocked move | Audit (`check_boss_ai_trace_invariants.py`) confirms `BossAI_HasAnyKOMove` evaluates only the locked move and that scoring marks non-locked moves unusable, but runtime move selection across a real fight is unverified. | Force a long fight against a boss carrying `CHOICE_BAND` / `CHOICE_SPECS` / `CHOICE_SCARF`. Confirm the boss never switches to a non-locked move once locked, and the boss does not loop on illegal coverage that scoring would otherwise have liked. | pending |
| Boss switches out under its own Perish Song count 1 or 2 | `BossAI_EnemyPerishEscapeUrgent` is statically wired before `BossAI_HasAnyKOMove`, but a real Perish Song fight isn't traced. If it stays in for the KO and dies to the count, the public-emergency exception is broken. | Lead with a Pokemon that knows Perish Song against any mid/late boss. Once the boss's mon is publicly perish-counted at `2`, observe whether it switches before count `0`, even if it has a KO line in. | pending |
| Boss avoids A→B→A switch-loop ping-pong | Static invariants and a synthetic switch-loop fixture (`audit/boss_ai_trace/shared_switch_loop_live.txt`) cover `BossAI_NeedsLoopPenalty`, but real-fight pivoting isn't traced. | Force a boss to switch A → B (e.g., scare it out with a super-effective threat), then on the next turn create conditions where A would be the obvious answer. Confirm the boss does not switch back to A unless a public emergency exception applies (low HP, public revenge, immunity pivot, ace timing). | pending |

### Pokemon balance / role expression

| What | Why | How to test | Last verified |
| --- | --- | --- | --- |
| Each "buffed" Pokemon feels usable in its intended role | Role intent lives in `docs/balance_intent.md` and `docs/buff_backlog.md`; numbers can be audited (`scripts/generate_balance_audit.py`) but feel cannot. | Pick one buffed mon per archetype from the `Resolved In Current Pass` table in `docs/buff_backlog.md` and play it from catch through one boss. Record against the `Follow-Up` column whether the role read in fights. | pending |
| Boss replacement mons read as their intended role | Boss roster audits prove the species/moves/items exist on each leader, but role-feel is design taste. The list of swaps lives in `docs/buff_backlog.md` `Resolved In Current Pass`: Misty (Lanturn replaces Kingdra; Politoed replaces Cloyster), Pryce (Dewgong replaces Starmie), Sabrina (Jynx replaces Starmie/Alakazam), Chuck/Brock (Sudowoodo replaces Onix/Donphan), Janine (Qwilfish replaces Ariados), Brock (Corsola replaces Donphan), Surge (Electrode with Rapid Spin replaces Donphan glue), Bugsy (Ledian as screen passer), Clair (Mantine replaces Donphan). | Fight each listed leader once. For each replacement, record whether the new mon expressed the documented role or felt like a generically-buffed swap. | pending |
| Buffed-mon NPC showcases match `docs/buff_backlog.md` | Trainer roster audits confirm the species exist on the trainer and learn the listed moves, but timing-of-the-move and feel during the actual fight are observation-only. | Fight: Schoolboy Alan on Route 35 (level 17 Yanma should open with Leech Life; rematch level 25 Yanma should have Wing Attack); Bird Keepers Jose and Perry (Farfetch'd should crit with Stick); Pokefan Colin in Silver only (level 32 Delibird with Icy Wind / Aurora Beam / Haze, not just Present); Koga (Ariados should run Spikes / Spider Web / Toxic on its turn-40 trap line). Note any showcase that did not deliver. | pending |
| Wild Route 38 Farfetch'd commonly hold Stick | Wild held items roll at encounter time; the source lists `STICK, STICK` for Farfetch'd, but the actual catch-rate of held items isn't audited. | Catch 5+ wild Farfetch'd on Route 38; record how many came holding Stick. The buff_backlog provisional intent is "commonly", not 100%. | pending |
| Evolution timings still pace early-mid game | `docs/evolution_policy.md` has the design intent. Audits check stats and methods but not pacing. | Note when each starter/early mon hits its first/second evo in normal play. | pending |
| Branching evolution menu shows up at level for multi-level evolvers | New menu in `engine/pokemon/evolve.asm` (`ChooseLevelEvolutionSpecies`) prompts when multiple `EVOLVE_LEVEL` candidates are valid. No audit covers UI rendering or cancel-out behavior. | Level a Tyrogue to 20 (3 candidates: Hitmonchan/Hitmonlee/Hitmontop), a Poliwhirl to 35 (Poliwrath/Politoed), a Gloom to 35 (Vileplume/Bellossom), a Slowpoke to 37 (Slowbro/Slowking), and an Eevee to 32 (5 candidates). For each: confirm the menu appears, all candidates are listed, the choice sticks, and canceling the menu cancels the evolution attempt without forcing a default branch. | pending |
| TM/HM availability matches intended pacing | Audits check that TMs exist and that learnsets reference real moves; they don't check *when* the player gets them. | Track which TMs are accessible by each badge; compare to `docs/balance_intent.md`. | pending |
| TM Tutor unlock cost and voucher economy work end-to-end | `docs/mechanics_changes_from_base.md` §3.1 specifies a `1000`-money one-time unlock and `1` `TM_VOUCHER` → `3` lesson credits. Source flow is audited (item-state restore in TM Tutor); the money/credit accounting and the former-HM (TM51-TM57) move list aren't runtime-tested. | At Day Care: pay 1000 money, confirm `EVENT_TM_TUTOR_UNLOCKED` sticks. Hand in one `TM_VOUCHER`, confirm credits go up by 3. Teach a former-HM move (e.g., Cut, Surf) via the tutor; confirm it does not consume the matching `TM51`-`TM57` from inventory and credits decrement only on a successful learn. | pending |
| Move Reminder includes pre-evolution chain moves at correct level | Per `engine/events/move_reminder.asm`, the candidate list pulls from current species and pre-evolution chain level-up learnsets up to the current level, with already-known moves filtered out. Audit confirms the page-size constant; not the candidate set. | Take a level-30 Crobat (pre-evo Zubat/Golbat) to the Move Reminder; confirm it can relearn Zubat/Golbat-only moves the player skipped. Repeat with a Pokemon that doesn't share its pre-evo learnset (e.g., Espeon/Umbreon split-line moves). | pending |

### QoL features (already audited; need UX confirmation)

| What | Why | How to test | Last verified |
| --- | --- | --- | --- |
| Default text speed reads as `FAST` from a fresh game | Source audited; player perception not. | New game → check Options menu → confirm text crawl speed at default. | pending |
| Move Reminder shows 4 moves per page (not 3) | Audited at compile time; menu rendering not. | Reach Move Reminder NPC → confirm 4 entries fit per page. | pending |
| Goldenrod Bike Shop auto-registers bicycle if Select slot empty | Audited at compile time; UI flow not. | Empty the Select-registered item → enter Bike Shop → confirm bike registers automatically. | pending |
| Repel renewal prompt offers Bag Repel after wear-off | Source flow is audited (`check_release_smoke.py` validates the script's text and item priority `MAX_REPEL` → `SUPER_REPEL` → `REPEL`). Runtime UX — does the prompt fire on the exact step, does declining leave the old wore-off message clean, does accepting consume exactly one item, does it stay silent inside Bug Catching Contest — isn't audited. | With one of each Repel type in the Bag, walk a route until Repel wears off; confirm the prompt fires once, top-priority item is offered first, and accepting consumes one. Repeat with no Repels in Bag (no prompt) and inside Bug Contest (no prompt). | pending |
| Pokemon Center heal still feels right after pause trim | `check_release_smoke.py` pins the post-trim pause counts (`pause 10/5/15/10`), but heal animation, music restart, Pokerus first-detection text, and nurse turn-object sequence are not runtime-validated. | Heal a full party at any Pokemon Center; confirm the heal animation plays, music restarts, the nurse turns correctly, and a fresh Pokerus detection still triggers its discovery dialogue. | pending |

### Maps / events / scripts

| What | Why | How to test | Last verified |
| --- | --- | --- | --- |
| Bug Contest exit flow doesn't softlock | `tools/audit/check_release_smoke.py` validates script shape, not runtime behavior. | Enter Bug Contest, withdraw mid-contest, confirm map state restores. | pending |
| Itemballs deliver the items the audit says they should | Audits check labels and table consistency; runtime delivery is separate. | Pick up itemballs along Route 30 / 31 / Sprout Tower; confirm each gives the audited item. | pending |
| Phone calls don't repeat after a deletion | `tools/audit/check_release_smoke.py` checks the deletion-guard flag; behavior isn't sim'd. | Add an NPC to phone, delete, advance time, confirm they don't re-call. | pending |
| Wild encounter level floor raises with badge progress | New `RaiseWildLevelForProgression` in `engine/overworld/wildmons.asm` raises low wild levels using `GetProgressionLevelCap` (cap-6) and a Mt. Silver floor of 65 once Blue is beaten. No audit covers in-game level distribution. | Step through grass on an early route (e.g., Route 29) at three save points: just after starter, after 4 badges, and after Lance. Record the wild level range at each — should rise visibly with progress. Then walk Mt. Silver after beating Blue and confirm wilds are at level 65+. | pending |
| Mt. Silver fishing upgrades vanilla fish species | `FishFunction` in `engine/events/overworld.asm` (`UpgradeSilverCaveFishEncounter`) replaces wild Magikarp → Gyarados, Poliwag → Poliwhirl, Goldeen → Seaking inside Mt. Silver. Not audited. | After beating Blue, fish in Mt. Silver waters with each rod; confirm fish encounters are the upgraded species and no longer the unevolved baseline. | pending |
| Legacy save HM revisit backfills Sky Pass and Lantern | `check_release_smoke.py` pins the source-side branches (Sage Li's `.CheckLegacyLantern`, Chuck's wife's `.CheckLegacySkyPass`); but a real legacy save (with `EVENT_GOT_HM02_FLY` / `EVENT_GOT_HM05_FLASH` already set, no key item) hasn't been runtime-tested. | Apply `dist/pokegold-data-rebalance.bps` to the baseline ROM; in the resulting save, revisit Sage Li at Sprout Tower 3F and Chuck's wife in Cianwood. Confirm each gives the matching key item (`LANTERN`, `SKY_PASS`) without re-triggering the original speech. | pending |
| Gym TM rewards now grant `TM_VOUCHER`, not direct TM | `docs/mechanics_changes_from_base.md` §3.3 calls out Violet, Azalea, Blackthorn gyms shifting to `TM_VOUCHER` reward. Audit confirms the reward script anchors and removed-stale-text rows; in-game receipt isn't traced. | Beat Falkner (and Bugsy/Clair as you reach them); confirm the post-fight reward is a `TM_VOUCHER`, that taking it to the TM Tutor exchanges for 3 credits, and the gym leader speech does not still claim a TM number. | pending |

### Known sporadic bugs (not yet reproduced)

| What | Why | How to test | Last verified |
| --- | --- | --- | --- |
| Mid-battle blank-textbox softlock / soft-reset during Rival 1 | Observed on 2026-05-01 builds `aa682ffc`/`993c4999` (VBA): during Rival 1 fight, after using Smokescreen the enemy's missed Water Gun produced either an empty textbox-softlock or a full soft-reset (game booted from $0000). Root cause is the `farcall`/`callfar` macro hl-clobber pattern in fail-text plumbing — the printer received a garbage pointer; RNG decided whether it printed harmlessly, hit `@`, or crashed the stack. **Two fixes shipped 2026-05-02:** (a) `engine/battle/type_passive_damage_mods.asm` `FailText_CheckOpponentProtect_Far` switched its inner `farcall GetBattleVar` to plain `call` (GetBattleVar is HOME-banked, so no farcall needed and no hl-clobber — covers the miss-text path through `BattleCommand_FailureText` → `GetFailureResultText_Far`); (b) `engine/battle/effect_commands.asm` `FailText_CheckOpponentProtect` replaced its `farcall` thunk to `_Far` with the same inlined HOME-banked-`call GetBattleVar` body (covers `FailMimic` and `PrintDidntAffect2` — Mimic / Conversion / Magnitude fails plus type-immunity "didn't affect"). | After fixes, replay the rival 1 fight and use Smokescreen at least twice. Confirm: enemy's missed move prints proper miss text (e.g., "Foe's WATER GUN missed!"), no blank textbox, no soft-reset. Bonus check: trigger a Mimic-into-empty-slot fail and confirm "but it failed!" prints normally. Test on the same Cyndaquil-vs-Totodile path that produced the original glitch. | 2026-05-02 both fixes applied; needs playtest verification |
| Inverted-palette world after whiteout in early Johto | One-shot observed on 2026-05-01 (VBA, fresh save): suspected whiteout from sleep-status faint to wild Jigglypuff produced respawned overworld with grossly wrong palettes (route grass pink/purple, mountain row silhouetted). Suggests whiteout / respawn palette reload path corrupts CGB palette state under some condition. | If it recurs: VBA save state at the broken state, do NOT in-game-save (overwrites good save with corrupt state). Soft-reset and reload — note whether colors come back. If they do, bug is volatile (WRAM/VRAM); if not, SRAM was hit. | 2026-05-01 `993c4999` observed; not reproduced |
| Map tiles "jumble" during overworld text scenes (give-item / heal) | Observed on 2026-05-01 (VBA): visible map tiles randomize into garbage while a textbox is open, then snap back to correct when the textbox closes. Confirmed on Nurse Joy heal at a Pokemon Center, picking from a berry tree, and talking to the Berry Master. Does NOT reproduce on plain signs / plain dialogue NPCs. RNG-flavored — same script triggers some attempts and not others. **Symptom shape implies `vBGMap` (on-screen tilemap) is being transiently overwritten while `wTileMap` (RAM source-of-truth) stays correct** — the close-text path's `wTileMap → vBGMap` push restores it. Likely a v-blank-queue race during the give-item-jingle / heal-anim scene; source audit (fork 2026-05-01) found no smoking-gun hl-clobber or stale-queue-pointer pattern in `engine/events/fruit_trees.asm`, `engine/events/heal_machine_anim.asm`, or `engine/overworld/scripting.asm:441` (`GiveItemScript`). | Reproduce: walk to a Pokemon Center, heal repeatedly until garble is observed (likely needs 3-10 attempts). When garble is on-screen: take a phone screenshot of the monitor for the garble pattern. Bonus: open VBA Tools → BG Map Viewer before triggering, pause emulator when garbled, screenshot the viewer window — that pinpoints which tilemap address got the bad write. | 2026-05-01 reported; not reproduced under instrumentation |

### Battle mechanics (late-gen items / rules)

These are runtime behaviors of mechanics added in 80c2d5c6 ("battle: add tactical AI and late-gen mechanics"). Source structure is mostly proven by `check_release_smoke.py` and `check_battle_math_safety.py`; in-battle UX and rule enforcement aren't.

| What | Why | How to test | Last verified |
| --- | --- | --- | --- |
| Choice item locks into the first selected move (player and enemy) | `late_gen_held_items.asm` enforces lock + reset on switch / non-damaging move / item loss. No audit confirms the player's move-select UI actually refuses non-locked moves and that `STRUGGLE` triggers when the locked move is unusable. | Hold `CHOICE_BAND` on a player mon. Pick Move A turn 1; on turn 2 try to pick Move B and confirm it's blocked. Run the locked move out of PP and confirm it falls to `STRUGGLE`. Switch out and back in; confirm lock cleared. | pending |
| Assault Vest blocks status-move selection and forces Struggle if no damaging moves | `docs/mechanics_changes_from_base.md` §1.2 says AV blocks non-damaging move use with explicit allowed exceptions; if no legal move remains, forced `STRUGGLE`. Source flow not audited at the menu layer. | Equip a player mon with `ASSAULT_VEST` and a moveset of three status moves + one damaging move. In battle, confirm the three status moves are blocked / greyed-out / refused. PP-out the damaging move; confirm `STRUGGLE` activates. | pending |
| Pack option is hidden in trainer battles | `docs/mechanics_changes_from_base.md` §1.6: trainer battles show `FIGHT / PKMN / RUN` only. Menu rendering not audited. | Enter any trainer battle (any tier). Confirm the battle menu shows `FIGHT / PKMN / RUN` (no Pack/Bag entry). | 2026-05-01 `993c4999` pass |
| Set battle style is enforced in trainer battles and the Options menu | After a trainer's mon faints, the player should not be offered the "switch?" prompt; the Options menu should show Set without the Shift toggle. Source default and code path not runtime-verified. | KO an opposing trainer mon; confirm no switch prompt appears before their next mon comes in. Open the Options menu; confirm Battle Style reads `SET` and cannot be toggled to `SHIFT`. | 2026-05-01 `993c4999` partial — Options-menu half passes (cannot toggle to Shift); post-KO switch-prompt half still pending. |
| Ditto Imposter auto-Transforms on switch-in | `engine/battle/effect_commands.asm` `TryActivateDittoImposter` runs after hazards. Activation text is not runtime-tested across edge cases (Fly/Dig hidden opponent should suppress; already-transformed Ditto should not retrigger). | Switch a Ditto into a wild battle; confirm the Transform text fires automatically and Ditto becomes the opponent. Repeat into an opponent mid-Fly/Dig (Ditto should not Transform until they reappear). Send Ditto out twice in the same battle; confirm it does not re-Transform after the first. | pending |

### Audio / visual

| What | Why | How to test | Last verified |
| --- | --- | --- | --- |
| Sky Pass Fly animation uses the fixed Pidgey icon | `engine/events/field_moves.asm` `FlyFunction_InitGFX` substitutes `PIDGEY` when the field item is `SKY_PASS`. `check_release_smoke.py` pins the source branch; the rendered icon is not audited. | Use Sky Pass to fly from any Fly destination. Confirm the icon shown above the player is a Pidgey, not whatever the last-selected party-mon icon happened to be. | pending |
| Spike layer animation reflects current layer count | Spikes now supports 3 layers (`docs/mechanics_changes_from_base.md` §1.4); animation is layer-aware in `data/moves/animations.asm`. Animation rendering is not audited. | In a trainer battle, set Spikes once, twice, three times, and a fourth attempt (should fail). Confirm the on-screen animation visually escalates between layers and the fourth attempt shows the fail message. | pending |

## How to add to this file

When you (a coding agent) ship a change that has *gameplay-visible* behavior
no audit can prove, add a row to the right area. Keep the **What** column
specific enough that a player can act on it without re-reading source. If
the change is purely internal (refactor, audit, doc), no row is needed —
this file is for surface that requires human eyes.

When the user reports a manual verification result, update **Last verified**
with date + ROM SHA1 + one-word outcome (`pass`, `fail`, `partial`). Don't
delete the row even after pass — keep the history so future regressions
have a baseline to compare against.

A fresh agent can rebuild or extend this file using the seed prompt at
the bottom of this file.

## Seed prompt for a fresh Claude session

Paste this verbatim into a new Claude Code session in this repo. It tells
the session to read the codebase top-to-bottom and add anything missing
from the table above.

```
Goal: extend `docs/manual_qa_backlog.md` so it covers every gameplay-visible
behavior in this repo that a coding agent cannot verify from source. The
file is for things a *human playing the ROM* needs to confirm, because
audits can't.

Read first (in this order):
  1. `docs/manual_qa_backlog.md` (the file you're extending — match its
     row format and respect its "don't list audited things" rule).
  2. `CLAUDE.md` (workflow + escalation contract; lists known design taste
     calls like the Whitney difficulty case).
  3. `docs/project_context.md` and `docs/project_roadmap.md` (project
     intent and current scope).
  4. `docs/boss_ai_spec.md`, `docs/boss_ai_post_patch_notes.md`,
     `docs/boss_ai_bug_testing_plan.md` (boss AI design + the existing
     per-boss test scenarios — DO reference rather than duplicate).
  5. `docs/balance_intent.md`, `docs/buff_backlog.md`,
     `docs/evolution_policy.md` (Pokemon balance design intent).
  6. `docs/qol_handoff.md` (QoL changes shipped + still-pending).
  7. `docs/smoke_test.md` and `tools/audit/check_release_smoke.py` (what's
     ALREADY audited — don't list any of this in the backlog).
  8. `git log --oneline -50` and `git log --since="6 weeks ago" --stat`
     (what's changed recently that may not be playtested yet).

Then, for every category below, decide whether the existing rows in
`manual_qa_backlog.md` cover the surface area. If a gap exists, add a row.
If a row is too vague ("test Boss AI"), tighten it ("fight Whitney with
a level-18 Geodude and confirm she still wipes you"). Do NOT delete rows
that are already there — only add or sharpen.

Categories to sweep:
  - Save format (any SRAM layout change since last full playthrough).
  - Boss AI fairness per leader / rival / champion.
  - Pokemon balance / role expression for buffed mons.
  - Evolution / TM / HM pacing.
  - QoL features (UX confirmation, not source).
  - Map scripts and event triggers (especially anything in
    `engine/events/` or `maps/` touched in the last 8 weeks).
  - Itemball delivery, mart inventories, phone scripts.
  - Audio / visual (cries, palettes, tilemaps) where source recently moved.
  - Anything in `docs/project_completion_todo.md` not yet marked done.

Hard rules:
  - If `python tools/audit/check_release_smoke.py` (or any other audit in
    `tools/audit/`) already proves the property, do NOT add it. Audits are
    the source of truth for what's verified — this file is only for the
    *unaudited* surface.
  - Each row's "What" column must name a concrete in-game scenario a
    player can act on without re-reading source. If you can't write that
    sentence, you don't understand the test yet — read more before adding.
  - Each row's "Why" column must name the audit gap. If the gap is "no
    audit exists yet", say so; that's a signal someone could write one.
  - Do not add rows for hypothetical features. Only ship behavior.
  - Keep "Last verified" set to `pending` for new rows. The user updates
    that column after they playtest.

Output: a single edit to `docs/manual_qa_backlog.md`. No new files. Don't
narrate; just do the edit and tell the user how many rows you added per
category.

Stop and ask if: more than 30 candidate rows pile up (the file is meant
to be reviewable, not exhaustive — at that point the user should triage
first), or if you find an audit gap so severe that an audit script is
the right answer instead of a manual row.
```
