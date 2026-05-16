# Cash-Out Immunity Transfer 001 - smogtours-gen2ou-912827 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-912827`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-912827.log`

Tournament source:
`https://www.smogon.com/forums/threads/smogon-premier-league-xvii-week-7.3778180/`

Web/current source checked:

- Smogon SPL XVII Week 7 GSC OU replay post for `smogtours-gen2ou-912827`.
- Pokemon Showdown replay log for `smogtours-gen2ou-912827`.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/workspace/quick_tests/cashout_immunity_guard_probe_001_2026-05-14.md`

Mode: spectator public. No Team Preview. Hidden teammates and unrevealed moves
were treated as revealed, strong-prior, or possible-only.

Contamination control:

- Local `rg` found no prior `912827` use before selection.
- Replay was selected from current SPL results without keyword screening for
  Explosion, Ghost pivots, Jynx, Forretress, or Gengar.
- Used only the local turn-pause helper before each reveal.
- Scoring uses the first 30 side decisions, turns 1-15.

Selected action:
Fresh transfer after `cashout_immunity_guard_probe_001`, checking whether
all-in cash-outs stay blocked unless immunity owners and fallback lines are
named first.

## Score

- Scored decisions: 30
- Top match: 15/30
- Acceptable match: 19/30
- Severe blunders: 0
- State errors: 0
- Hidden-info errors: 0
- Mechanics errors: 0
- Positive-selection: 24/30
- Route-converting move chosen: 12/21 applicable
- Branch-punish chosen: 10/18 applicable
- Earliest meaningful error: turn 1

Interpretation:
The cash-out immunity guard held in this sample: I did not make Explosion or an
all-in trade top into a live revealed or plausible immunity branch. This is not
broad progress because top-match and acceptable-match remain below the
provisional gate. The bigger repeated miss was positive branch pressure from
status-capable Pokemon: Jynx and Gengar needed Thief, Ice Punch, or positioning
into receivers instead of generic sleep or active-target damage.

## Turn Notes - First 30 Scored Side Decisions

| Turn | Side | Frozen top | Actual | Grade |
| --- | --- | --- | --- | --- |
| 1 | p1 | Lovely Kiss | Thief | miss; defaulted to sleep instead of item/absorber pressure |
| 1 | p2 | Switch sleep absorber | Skarmory | top by class |
| 2 | p1 | Lovely Kiss | Gengar | miss; failed to reposition after Skarmory reveal |
| 2 | p2 | Drill Peck | Raikou | miss; actual took Electric-board control |
| 3 | p1 | Switch Electric answer | Steelix | top by class |
| 3 | p2 | Thunderbolt | Thunderbolt | top |
| 4 | p1 | Roar if available | Roar | top |
| 4 | p2 | Switch Skarmory | Forretress | acceptable Ground-answer/support switch |
| 5 | p1 | Switch Water answer | Snorlax | top by class |
| 5 | p2 | Surf or Hydro Pump | Snorlax | miss; missed counter-handoff |
| 6 | p1 | Curse | Double-Edge | acceptable setup, not the sharper active chip |
| 6 | p2 | Curse | Forretress | miss; missed Normal-resist/support handoff |
| 7 | p1 | Switch Gengar | Double-Edge | miss; over-defended Explosion/Toxic before Forretress showed it |
| 7 | p2 | Spikes | Spikes | top |
| 8 | p1 | Switch Gengar | Double-Edge | acceptable into Toxic/Explosion branch, not top |
| 8 | p2 | Toxic | Toxic | top |
| 9 | p1 | Switch Gengar | Gengar | top |
| 9 | p2 | Toxic | Skarmory | miss; failed to cover Gengar entry |
| 10 | p1 | Thunder or Thunderbolt | Ice Punch | miss; missed Raikou receiver coverage |
| 10 | p2 | Switch Raikou | Raikou | top |
| 11 | p1 | Switch Steelix | Snorlax | acceptable pivot, not top |
| 11 | p2 | Hidden Power if available | Forretress | miss; overread Steelix repeat |
| 12 | p1 | Double-Edge | Double-Edge | top |
| 12 | p2 | Toxic | Toxic | top |
| 13 | p1 | Switch Gengar | Rest | miss; missed poison-reset Rest route |
| 13 | p2 | Switch Skarmory | Skarmory | top |
| 14 | p1 | Sleep Talk if present | Sleep Talk -> Rest | top |
| 14 | p2 | Whirlwind | Forretress | miss; missed sleeping-Lax support reset |
| 15 | p1 | Sleep Talk | Sleep Talk -> Earthquake | top |
| 15 | p2 | Switch Skarmory | Skarmory | top |

## Cash-Out Guard Check

The guard held, but the evidence is limited:

- I did not recommend Explosion from Forretress into Snorlax while Gengar was
  revealed and available.
- I did not make Gengar Explosion top after revealing Gengar's Ice Punch route.
- The replay did not force a clean actual Explosion/immunity decision in the
  first 30 side decisions, so this is a low-sample transfer, not proof.

## Main Errors

Turn 1:
Jynx versus Forretress was the same family as the previous branch-absorber
miss. I used Lovely Kiss as the generic status answer; the actual Thief
improved through the Skarmory switch.

Turn 10:
Gengar versus Skarmory invited Raikou. I chose Electric pressure into the
active Skarmory, while the actual Ice Punch punished the Raikou receiver. This
is the clean positive-selection miss in the packet.

Turn 13:
After Snorlax was poisoned, I over-focused on Gengar as the Toxic/Explosion
owner. The actual Rest reset the poison route and kept Snorlax useful.

## Reusable Lesson

For status-capable leads and Ghosts, do not ask only "what beats the active
target?" Ask which revealed or likely receiver is coming and whether Thief,
coverage, Rest, phaze, or a switch improves through that receiver.

Next rep:
Fresh positive-selection transfer: when Jynx, Gengar, or another status-capable
Pokemon faces an obvious receiver, rank item removal, coverage into the
receiver, counter-handoff, setup/phaze, and status before choosing.
