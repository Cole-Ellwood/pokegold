# Manual Feel Checks - 2026-04-27

Scope: focused emulator feel pass for `TODO-003` in
`docs/project_completion_todo.md`.

Basis:

- Emulator: PyBoy from `.local/pydeps`, `window="null"`.
- ROM: normal `pokegold.gbc`.
- Save basis: current root `pokegold.sav`, copied into scratch `.gbc.ram`
  sidecars under `.local/tmp/manual_feel_2026_04_27/`.
- Method: scripted button input to reach exact UI moments, then manual screenshot
  review of BMP captures. This is emulator/runtime evidence, not a full
  playthrough.
- Main logs:
  - `.local/tmp/manual_feel_2026_04_27/manual_feel_log_v2.txt`
  - `.local/tmp/manual_feel_2026_04_27/earl_extended_log.txt`
  - `.local/tmp/manual_feel_2026_04_27/manual_feel_log.txt` for the Falkner
    loss branch.

## Repel Renewal Accept/Decline

Setup: Route 29 from the current save, with `wRepelEffect=1` and Bag seeded with
`MAX_REPEL x2`, `SUPER_REPEL x1`, and `REPEL x1` to force the renewal branch on
the next real step.

Evidence:

- Decline:
  - `.local/tmp/manual_feel_2026_04_27/screens_v2/repel_decline_01_wore_off_full.bmp`
  - `.local/tmp/manual_feel_2026_04_27/screens_v2/repel_decline_02_offer_full.bmp`
  - `.local/tmp/manual_feel_2026_04_27/screens_v2/repel_decline_03_declined_closed.bmp`
- Accept:
  - `.local/tmp/manual_feel_2026_04_27/screens_v2/repel_accept_01_wore_off_full.bmp`
  - `.local/tmp/manual_feel_2026_04_27/screens_v2/repel_accept_02_offer_full.bmp`
  - `.local/tmp/manual_feel_2026_04_27/screens_v2/repel_accept_03_used_full.bmp`

Result:

- Decline returned to the map with `wRepelEffect=0`; item counts stayed
  `MAX_REPEL x2`, `SUPER_REPEL x1`, `REPEL x1`.
- Accept chose the highest-priority item, printed `Used MAX REPEL.`, consumed
  exactly one Max Repel, and left `wRepelEffect=250`.
- Feel note: the flow is clear and short. The old wore-off message appears
  first, the Yes/No offer is understandable, decline is quiet, and accept has a
  single confirmation line. No duplicate generic text was observed.

## HM-Tool Acquisition, Use, Backfill

Acquisition setup: Sprout Tower 3F, Sage Li already beaten
(`EVENT_BEAT_SAGE_LI` set), `EVENT_GOT_HM05_FLASH` clear, no `LANTERN` in the
Key Item pocket.

Backfill setup: Sprout Tower 3F, `EVENT_GOT_HM05_FLASH` set, no `LANTERN` in the
Key Item pocket.

Use setup: Cianwood City outdoors, `SKY_PASS` in the Key Item pocket, Storm
Badge bit set, `SKY_PASS` registered to SELECT.

Evidence:

- Acquisition:
  - `.local/tmp/manual_feel_2026_04_27/screens_v2/lantern_acquisition_04.bmp`
  - `.local/tmp/manual_feel_2026_04_27/screens_v2/lantern_acquisition_07.bmp`
  - `.local/tmp/manual_feel_2026_04_27/screens_v2/lantern_acquisition_13.bmp`
- Legacy backfill:
  - `.local/tmp/manual_feel_2026_04_27/screens_v2/lantern_legacy_backfill_01.bmp`
  - `.local/tmp/manual_feel_2026_04_27/screens_v2/lantern_legacy_backfill_04.bmp`
  - `.local/tmp/manual_feel_2026_04_27/screens_v2/lantern_legacy_backfill_07.bmp`
- Registered use:
  - `.local/tmp/manual_feel_2026_04_27/screens_v2/sky_select_01.bmp`
  - `.local/tmp/manual_feel_2026_04_27/screens_v2/sky_select_02.bmp`

Result:

- Sage Li acquisition gave `LANTERN`, placed it in the Key Item pocket, then
  gave the converted Flash disc and explained that `LANTERN` lights dark places.
- Legacy Flash reward state with missing `LANTERN` backfilled the key item on
  revisit and replayed the explanation.
- Registered `SKY_PASS` opened the Fly map through SELECT and successfully
  traveled to New Bark Town.
- Feel note: the key-item half of the HM-tool flow reads correctly in play.
  The converted disc reward still uses generic `TMs` receive/put-away wording;
  that is a small polish rough edge, not a blocker for the tool flow.

Not covered in this focused pass: every HM replacement item, A-button obstacle
use for every tool, Bag-menu use for every tool, near-capacity item pockets, and
field-tool behavior inside unusual maps.

## Earl / Early-Rule Communication Text

Setup: warped to Earl's Pokemon Academy and read the notebook object from the
current normal ROM.

Evidence:

- `.local/tmp/manual_feel_2026_04_27/screens_v2/earl_ext_01.bmp`
- `.local/tmp/manual_feel_2026_04_27/screens_v2/earl_ext_03.bmp`
- `.local/tmp/manual_feel_2026_04_27/screens_v2/earl_ext_06.bmp`
- `.local/tmp/manual_feel_2026_04_27/screens_v2/earl_ext_08.bmp`
- `.local/tmp/manual_feel_2026_04_27/screens_v2/earl_ext_11.bmp`
- `.local/tmp/manual_feel_2026_04_27/screens_v2/earl_ext_13.bmp`
- `.local/tmp/manual_feel_2026_04_27/screens_v2/earl_ext_18.bmp`
- `.local/tmp/manual_feel_2026_04_27/screens_v2/earl_ext_21.bmp`

Result:

- The notebook rendered the Set/no-Pack warning, Gym Leader public-move memory,
  stronger type-habit examples, held-item warning, and final notebook joke
  without visible text overflow.
- Feel note: the text is dense but readable. The best part is that it teaches
  the rules as warnings before the player has to infer them from a loss.

## Real Boss/Trainer Loss Fairness Note

Setup: current save's lone level 11 Totodile was warped into Falkner through the
real Violet Gym map script with no Johto badges, then the battle was advanced
with simple `A` inputs.

Evidence:

- `.local/tmp/manual_feel_2026_04_27/screens/falkner_loss_040.bmp`
- `.local/tmp/manual_feel_2026_04_27/screens/falkner_loss_end_055.bmp`
- `.local/tmp/manual_feel_2026_04_27/manual_feel_log.txt` records
  `falkner_ended loss=True result=01`.

Result:

- The loss was real emulator runtime: Totodile fainted and the game reached the
  player-loss text.
- Fairness note: this is not first-gym curve proof because the state is a
  synthetic underleveled boss entry. As a loss-feel sample, the reason for
  losing was legible: a lone level 11 starter into Falkner's level 19 Pidgeotto
  is visibly outmatched. Nothing in the observed loss felt like hidden
  clairvoyance or arbitrary punishment.
- Double-check caveat: the scratch log's species-name decoder is unreliable for
  this branch; use the screenshot, not the log's decoded enemy species label, to
  identify Pidgeotto.

## Double-Check Status

Double-checked after writing: this note was reread against
`manual_feel_log_v2.txt`, `earl_extended_log.txt`, `manual_feel_log.txt`, and
the named screenshots. It claims only the focused checks above, not broad
playthrough proof or exhaustive HM-tool coverage.
