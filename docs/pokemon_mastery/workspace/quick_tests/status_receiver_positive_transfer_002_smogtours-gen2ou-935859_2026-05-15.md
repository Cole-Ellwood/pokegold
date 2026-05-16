# Status Receiver Positive Transfer 002 - smogtours-gen2ou-935859 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935859`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935859.log`

Replay search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou`

Web/current source checked:

- Pokemon Showdown public replay search API for current Gen 2 OU replays.
- Pokemon Showdown raw replay log for `smogtours-gen2ou-935859`.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/workspace/quick_tests/all_in_ghost_resttalk_wake_repair_probe_001_2026-05-15.md`

Mode: spectator public. No Team Preview. No Smogon team-paste or matchup
preview was used. Hidden teammates and unrevealed moves were treated as
revealed, strong-prior, or possible-only.

Contamination control:

- Local `rg` found no prior `935859` use before selection.
- Replay was selected from the current Showdown Gen 2 OU search API without
  keyword screening for Smeargle, Destiny Bond, Snorlax, Self-Destruct, Rest,
  Zapdos, or Hidden Power.
- Used only the local turn-pause helper before each reveal.
- Scoring covers turns 1-15, exactly 30 side decisions.

Selected action:
Fresh transfer after `all_in_ghost_resttalk_wake_repair_probe_001`, with the
all-in Ghost-immunity and RestTalk wake gates active. The replay naturally
tested Smeargle support sequencing, Destiny Bond avoidance, CurseLax route
conversion, one-time Self-Destruct timing, and Zapdos coverage/Rest selection.

## Score

- Scored decisions: 30
- Top match: 13/30
- Acceptable match: 24/30
- Severe blunders: 0
- State errors: 0
- Hidden-info errors: 0
- Mechanics errors: 0
- Positive-selection: 25/30
- Route-converting move chosen: 14/22 applicable
- Branch-punish chosen: 10/18 applicable
- Earliest meaningful error: turn 1

Interpretation:
Mixed result, not broad progress. The severe/hidden-info gate held after the
repair probe, and acceptable-match was above the provisional gate. Top-match
was still below target, and the sample did not strongly test the intended
status-receiver branch beyond Smeargle's support threat. The biggest positive
miss was p2 turn 11: I preserved with a Rest-prior line instead of recognizing
Self-Destruct as the immediate route-converting answer to boosted Snorlax.

## Turn Notes

| Turn | Side | Frozen ranked candidates | Actual | Grade | Positive-selection tags |
| --- | --- | --- | --- | --- | --- |
| 1 | p1 | 1. stay and attack/absorb with Snorlax; 2. switch sleep absorber; 3. phazer/faster support | Double-Edge | top-match | positive, route |
| 1 | p2 | 1. Spore as strong prior; 2. Spikes; 3. Baton Pass/support | Spikes | miss; under-ranked hazard-first support | positive active support only |
| 2 | p1 | 1. switch designated sleep absorber; 2. Double-Edge if Snorlax is absorber; 3. phazer/faster support | Sleep Talk | miss; missed Sleep Talk as Spore/DBond cover | none |
| 2 | p2 | 1. Spore; 2. Destiny Bond; 3. preserve Smeargle | Destiny Bond | miss; under-ranked active trade denial | none |
| 3 | p1 | 1. Sleep Talk to cover Spore/DBond; 2. switch Zapdos or other absorber; 3. attack only if DBond is cleared | Zapdos | acceptable-match by avoid-DBond class | positive, branch |
| 3 | p2 | 1. Spore; 2. Destiny Bond; 3. switch preserve | Destiny Bond | miss; DBond was named but under-ranked | none |
| 4 | p1 | 1. switch/pivot to clear DBond; 2. non-damaging support if present; 3. attack only if DBond cleared | Snorlax | top-match by class | positive, branch |
| 4 | p2 | 1. Destiny Bond; 2. Spore; 3. switch Snorlax/preserve Smeargle | Snorlax | acceptable-match; preservation branch named | positive |
| 5 | p1 | 1. Double-Edge; 2. Curse; 3. switch phazer/answer if known | Curse | acceptable-match | positive, route |
| 5 | p2 | 1. Double-Edge; 2. Curse; 3. Lovely Kiss if available | Curse | acceptable-match | positive, route |
| 6 | p1 | 1. Double-Edge; 2. Curse; 3. switch phazer/answer if known | Curse | acceptable-match; setup route continued | positive, route |
| 6 | p2 | 1. Double-Edge; 2. Curse; 3. switch phazer/answer if known | Curse | acceptable-match | positive, route |
| 7 | p1 | 1. Double-Edge; 2. Curse; 3. Rest if damage forces it | Curse | acceptable-match; I attacked one turn early | positive, route |
| 7 | p2 | 1. Double-Edge/Body Slam; 2. Curse; 3. Rest if forced | Body Slam | top-match by class | positive, route |
| 8 | p1 | 1. Double-Edge; 2. Curse; 3. Rest if forced | Curse | acceptable-match; setup route continued | positive, route |
| 8 | p2 | 1. Curse; 2. Body Slam; 3. Rest if forced | Curse | top-match | positive, route |
| 9 | p1 | 1. Double-Edge; 2. Curse; 3. Rest if forced | Curse | acceptable-match; setup route continued | positive, route |
| 9 | p2 | 1. Curse; 2. Body Slam; 3. Rest if forced | Curse | top-match | positive, route |
| 10 | p1 | 1. Curse to max; 2. Double-Edge; 3. Rest if forced | Double-Edge | acceptable-match; right route, wrong order | positive, route |
| 10 | p2 | 1. Curse; 2. Body Slam; 3. Rest if forced | Curse | top-match | positive, route |
| 11 | p1 | 1. Double-Edge; 2. Rest if needed; 3. Curse only if not punished | Double-Edge | top-match | positive, route |
| 11 | p2 | 1. Rest as strong prior; 2. Body Slam; 3. Curse | Self-Destruct | miss; failed to cash out into boosted Snorlax | none |
| 12 | p1 | 1. Thunder; 2. switch Electric answer if known; 3. Rest if needed | Thunder | top-match | positive, route |
| 12 | p2 | 1. Thunder; 2. switch Electric answer if known; 3. Rest if needed | Thunder | top-match | positive, route |
| 13 | p1 | 1. Thunder; 2. switch Electric answer if known; 3. Rest if needed | Thunder | top-match | positive, route |
| 13 | p2 | 1. Thunder; 2. switch Electric answer if known; 3. Rest if needed | Thunder | top-match | positive, route |
| 14 | p1 | 1. Thunder; 2. switch Electric answer if known; 3. Rest if needed | Thunder | top-match | positive, route |
| 14 | p2 | 1. Thunder; 2. switch Electric answer if known; 3. Rest if needed | Thunder | top-match | positive, route |
| 15 | p1 | 1. switch Electric answer if available; 2. Rest; 3. Thunder if no owner | Rest | acceptable-match; correct preserve class, not exact top | positive |
| 15 | p2 | 1. Thunder; 2. Hidden Power coverage if revealed/available; 3. Rest if forced | Hidden Power | acceptable-match by active coverage class | positive, route |

## Main Errors

Turn 1-3 Smeargle sequencing:
I over-weighted the strong Smeargle Spore prior and under-ranked the revealed
support package: Spikes first, then Destiny Bond to deny the immediate KO. The
correct adjustment after turn 2 was to treat Destiny Bond as the active branch
to clear before choosing damage.

Turn 10 CurseLax timing:
I finally overcorrected from attacking too early and ranked one more Curse when
underlying chose Double-Edge. The useful rule is not "always max first"; it is
"attack once the next hit forces the opponent into Rest, boom, or a losing
trade before they can equalize cleanly."

Turn 11 Self-Destruct miss:
The p2 Snorlax had a concrete route-converting cash-out: remove the boosted
opposing Snorlax immediately. I named Rest as a strong prior but did not ask
whether preserving Snorlax was worse than spending it to stop the converter.
This is a positive-selection miss, not a severe error.

## Reusable Lesson

When the opponent has already used Destiny Bond, do not treat the position as a
generic sleep lead. First rank: clear DBond with a switch or non-damaging move,
attack only after the bond is cleared, and preserve the low support piece if it
still threatens a one-time denial.

For CurseLax mirrors, decide the spend/preserve point by route pressure: keep
boosting while it changes the exchange, then attack when the hit forces Rest,
Self-Destruct, or a losing trade. If the opponent is the one under converter
pressure, price Self-Destruct before defaulting to Rest.

Next rep:
Fresh replay transfer or expert review focused on one-time trade timing after
setup pressure. Keep scoring positive-selection, route conversion, branch
punish, top-match, acceptable-match, hidden-info errors, state errors,
mechanics errors, and severe blunders separately.
