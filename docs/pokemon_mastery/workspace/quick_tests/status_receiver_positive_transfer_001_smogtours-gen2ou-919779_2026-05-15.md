# Status Receiver Positive Transfer 001 - smogtours-gen2ou-919779 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-919779`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-919779.log`

Tournament source:
`https://www.smogon.com/forums/threads/smogon-premier-league-xvii-semifinals.3779122/`

Web/current source checked:

- Smogon SPL XVII Semifinals thread, which lists `GSC OU: Zokuru vs Rubyblood`.
- Pokemon Showdown raw replay log for `smogtours-gen2ou-919779`.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/policy_cards/active_pressure_before_status.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/hidden_role_voluntary_entry.md`
- `docs/pokemon_mastery/policy_cards/romhack_mechanics_firewall.md`

Mode: spectator public. No Team Preview. Hidden teammates and unrevealed moves
were treated as revealed, strong-prior, or possible-only.

Contamination control:

- Local `rg` found no prior scored artifact for `919779` before selection.
- Replay was selected from current SPL results without keyword screening for
  Hypnosis, Gengar, Forretress, Explosion, or RestTalk.
- Used only the local turn-pause helper before each reveal.
- Scoring covers turns 1-16. Turn 9 p2 was unscored because full paralysis hid
  the selected move.

Selected action:
Fresh transfer after `cashout_immunity_transfer_001`, checking whether the next
move selection improves through status receivers and named branches instead of
settling for generic status, active-target damage, or all-in support cash-out.

## Score

- Scored decisions: 31
- Top match: 12/31
- Acceptable match: 17/31
- Severe blunders: 1
- State errors: 1
- Hidden-info errors: 1
- Mechanics errors: 0
- Positive-selection: 23/31
- Route-converting move chosen: 13/24 applicable
- Branch-punish chosen: 8/19 applicable
- Earliest meaningful error: turn 1

Interpretation:
This is not progress. The sample did produce several positive route choices
after the midgame settled, especially Tyranitar Roar/Rock Slide into RestTalk
Snorlax, but the severe gate failed on turn 6. I made Explosion the main p1
line from Exeggutor into a no-Team-Preview board where hidden Gengar was a
plausible immunity branch and slow play was still available. That error is both
`hidden_info_error` and `severe_blunder`.

## Turn Notes

| Turn | Side | Frozen ranked candidates | Actual | Grade | Positive-selection tags |
| --- | --- | --- | --- | --- | --- |
| 1 | p1 | 1. Lovely Kiss; 2. Curse; 3. Double-Edge/Body Slam | Double-Edge | miss | none |
| 1 | p2 | 1. Lovely Kiss/stay; 2. Curse; 3. active damage | Cloyster | miss | none |
| 2 | p1 | 1. Double-Edge; 2. switch special answer; 3. Curse | Double-Edge | top-match | positive, route |
| 2 | p2 | 1. Spikes; 2. Toxic; 3. Explosion later | Spikes | top-match | positive, route |
| 3 | p1 | 1. switch to preserve Snorlax; 2. Double-Edge; 3. Curse/Rest | Zapdos | acceptable-match by preservation class | positive |
| 3 | p2 | 1. Explosion; 2. Toxic; 3. switch/preserve Cloyster | Toxic | miss | none |
| 4 | p1 | 1. Thunder; 2. Rest if RestTalk; 3. switch if Electric answer is named | Exeggutor | miss; failed to counter-switch into Snorlax | positive active pressure only |
| 4 | p2 | 1. Snorlax; 2. Electric/Ground answer; 3. Explosion | Snorlax | top-match | positive, branch |
| 5 | p1 | 1. Sleep Powder; 2. Stun Spore; 3. Explosion only if route-critical | Stun Spore | acceptable-match | positive, route |
| 5 | p2 | 1. switch sleep absorber; 2. Double-Edge; 3. Lovely Kiss if faster tie allowed | Double-Edge | miss; over-defended status and missed active pressure | none |
| 6 | p1 | 1. Explosion high-risk; 2. switch/preserve Egg; 3. Psychic/Giga Drain chip | Forretress | severe hidden-info miss; hidden Gengar branch was live | none |
| 6 | p2 | 1. Double-Edge; 2. switch boom absorber; 3. Rest later | Gengar | miss; failed to choose the branch punish | none |
| 7 | p1 | 1. Spikes; 2. switch Snorlax; 3. HP Bug/attack if present | Zapdos | miss | positive, route |
| 7 | p2 | 1. Fire Punch/coverage; 2. Thunder; 3. Hypnosis | Hypnosis | miss | positive active pressure only |
| 8 | p1 | 1. Thunder; 2. switch Snorlax; 3. Rest if RestTalk | Thunder | top-match | positive, route |
| 8 | p2 | 1. Snorlax; 2. Raikou/Electric answer; 3. coverage | Snorlax | top-match | positive, branch |
| 9 | p1 | 1. Thunder; 2. Rest if RestTalk; 3. Forretress hazard route | Forretress | miss; missed Forretress timing into low RestTalk Lax | positive active pressure only |
| 9 | p2 | unscored: full paralysis hid the selected move | full paralysis | unscored | unscored |
| 10 | p1 | 1. Spikes; 2. Rapid Spin later; 3. avoid Explosion into Gengar | Spikes | top-match | positive, route |
| 10 | p2 | 1. Gengar; 2. Rest; 3. Double-Edge | Rest | miss; Rest was named but under-ranked | none |
| 11 | p1 | 1. Rapid Spin; 2. counter-handoff into Gengar; 3. avoid Explosion | Tyranitar | miss; named Gengar branch but did not hand off | none |
| 11 | p2 | 1. Gengar; 2. Sleep Talk if present; 3. stay burn sleep turn | Sleep Talk -> Double-Edge | miss; underpriced RestTalk Lax agency | none |
| 12 | p1 | 1. Roar; 2. Curse/setup; 3. Rock Slide | Roar | top-match | positive, route, branch |
| 12 | p2 | 1. Sleep Talk; 2. Zapdos; 3. Gengar | Zapdos | miss | none |
| 13 | p1 | 1. Roar; 2. Rock Slide; 3. Curse | Rock Slide | acceptable-match; correct owner, softer converter | positive, route |
| 13 | p2 | 1. Sleep Talk; 2. Zapdos; 3. Gengar | Sleep Talk -> Double-Edge | top-match | positive, route |
| 14 | p1 | 1. Rock Slide; 2. Roar; 3. preserve Tyranitar | Rock Slide | top-match | positive, route |
| 14 | p2 | 1. Sleep Talk if still asleep; 2. switch Zapdos; 3. Earthquake if awake | Earthquake | miss plus state error; wake turn under-ranked | none |
| 15 | p1 | 1. Rock Slide; 2. preserve Tyranitar; 3. Roar | Rock Slide | top-match | positive, route |
| 15 | p2 | 1. Earthquake; 2. Rest; 3. switch Gengar/Zapdos | Rest | miss; spent pressure when preserve was better | positive active pressure only |
| 16 | p1 | 1. Roar; 2. Rock Slide; 3. switch preserve | Roar | top-match | positive, route, branch |
| 16 | p2 | 1. Sleep Talk; 2. Zapdos; 3. Gengar | Sleep Talk -> Rest | top-match | positive, route |

## Main Errors

Turn 6 severe hidden-info error:
I made Exeggutor Explosion the main line because it would remove a paralyzed
Snorlax. In no-Team-Preview spectator-public mode, hidden Gengar was only
possible, but it was a direct immunity branch to an all-in move. Since slow
play still existed, the main line had to preserve Exeggutor or hand off before
cash-out. The actual double switch showed exactly that branch.

Turn 11 branch-action miss:
I named the revealed Gengar spinblock/Explosion absorber branch and still put
Rapid Spin first. The actual Tyranitar handoff was the better board owner
against RestTalk Snorlax and the broader p2 structure.

Turn 14 state error:
I did not make the Rest wake counter explicit enough. Sleep Talk stayed on top
when Snorlax could wake and choose Earthquake. Count this as a state error, not
a hidden-info excuse.

## Reusable Lesson

When a support Pokemon can cash out into an active target, first name the
revealed and plausible immunity owners. If a plausible hidden immunity blanks
the trade and slow play still improves the route, Explosion cannot be the main
line. After the branch is named, the top move must either punish that branch or
preserve the correct route piece.

Next rep:
Run one small repair probe for all-in support cash-out against plausible hidden
Ghost plus RestTalk wake timing, then return to a fresh status-receiver
positive-selection transfer.
