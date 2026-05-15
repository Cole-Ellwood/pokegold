# Replay Turn-Pause 017 Sleep Route To Marowak - smogtours-gen2ou-934428 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-934428`.

Mode: spectator public continuation.

Purpose: follow up `replay_turn_pause_016` at the point where I missed Snorlax
Lovely Kiss into a Cloyster absorber. The target question was whether I would
correctly price sleep initiative, Sleep Clause material, absorber preservation,
and the remaining Baton Pass receiver route.

Contamination control:

- Turns 1-11 were already known from `replay_turn_pause_016`.
- Turns 12-24 were unrevealed before each prompt in this continuation.
- The local helper omits passed Baton Pass boosts after the switch, so the
  manual public state kept Marowak's passed `spe+2` for turns 20-23.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/paused_turn_atlas.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_016_baton_pass_resolve_smogtours-gen2ou-934428_2026-05-14.md`

Web sources checked:

- Smogon Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Smogon GSC Exeggutor analysis:
  `https://www.smogon.com/dex/gs/pokemon/exeggutor/`
- Smogon GSC Snorlax analysis:
  `https://www.smogon.com/dex/gs/pokemon/snorlax/`

Source note: GSC sleep is not a one-turn ownership claim. It creates a
temporary route window, but Sleep Clause, switching, absorber preservation,
Sleep Talk, and Explosion can all keep the opponent's route live. A common GSC
branch is to switch the slept Pokemon out immediately and preserve it as Sleep
Clause material instead of burning wake turns in front of the sleep user.

## Score Summary

Turns scored: 12-24.

Decisions scored: 22 side-decisions. p1 turn 15 was excluded after flinch.
p2 turns 20-22 were excluded because the active fainted or was asleep before a
meaningful selected move resolved.

Top-match: 15 / 22.

Acceptable-match: 18 / 22.

Severe blunders: 1.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful error: turn 12.

Severe error: turn 18. I chose ordinary Jolteon damage into Tyranitar and
missed that the only realistic comeback route was Agility into Baton Pass to
the remaining receiver. The exact receiver was not public yet, but the team
archetype and revealed Jolteon Baton Pass made a receiver route material.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 12 | Snorlax 100 vs sleeping Cloyster 94 | p1 Curse, with Double-Edge as pressure alt; p2 stay/asleep or act if wake | p1 Double-Edge; p2 Machamp switch | p1 acceptable, p2 miss | The slept absorber was preserved as Sleep Clause material instead of spending wake turns; p2 used Machamp to punish passive Snorlax setup. |
| 13 | Snorlax 98 vs Machamp 48 | p1 Double-Edge; p2 Cross Chop | p1 Double-Edge; p2 Cross Chop miss | both top | Correctly accepted the Snorlax trade window after Machamp took Spikes and chip. |
| 14 | Snorlax 96 vs Machamp 10 | p1 KO with Double-Edge / no-recoil attack; p2 Cross Chop | p1 Earthquake; p2 Cross Chop | p1 acceptable, p2 top | Use the no-recoil KO when available; low Machamp should spend its last Cross Chop. |
| 15 | Snorlax 37 vs Tyranitar 94 | p1 Earthquake; p2 Rock Slide | p2 Rock Slide flinched Snorlax | p1 excluded, p2 top | Flinch denied the planned Earthquake; Rock Slide was the correct immediate punish. |
| 16 | Snorlax 17 vs Tyranitar 100 | p1 switch Scizor/preserve if possible; p2 Rock Slide or Fire Blast | p1 stayed; p2 Earthquake KO | p1 miss, p2 acceptable | The low Snorlax was more expendable than I treated it; switching Scizor into the punish did not improve the route. |
| 17 | Scizor 37 vs Tyranitar 100 | p1 Hidden Power; p2 Fire Blast | p1 Agility; p2 Fire Blast KO | p1 miss, p2 top | Unboosted Scizor could not rebuild the chain into a Fire Blast Tyranitar. |
| 18 | Jolteon 100 vs Tyranitar 100 | p1 Thunder/chip; p2 Earthquake | p1 Agility; p2 Earthquake | p1 severe miss, p2 top | The live route was not damage. It was Agility plus Baton Pass to the unrevealed receiver. |
| 19 | Jolteon `spe+2` 25 vs Tyranitar 100 | p1 Baton Pass to receiver; p2 switch Exeggutor | p1 Baton Pass to Marowak; p2 Exeggutor | both top | Correct re-solve after Agility: name the receiver route and the opponent's route answer. |
| 20 | Marowak `spe+2` vs Exeggutor 67 | p1 Hidden Power Bug; p2 Giga Drain or Sleep Powder if it lives | p1 Hidden Power KO | p1 top, p2 excluded | Passed Speed made Marowak's coverage route immediate. |
| 21 | Marowak `spe+2` vs Zapdos 37 | p1 Rock Slide | p1 Rock Slide KO | p1 top, p2 excluded | Correct cash-in after the receiver was revealed. |
| 22 | Marowak `spe+2` vs sleeping Cloyster 88 | p1 Earthquake; p2 no action unless wake | p1 Earthquake; p2 asleep | p1 top, p2 excluded | Do not boost greedily into a possible wake; attack the sleeper. |
| 23 | Marowak `spe+2` vs sleeping Cloyster 50 | p1 Earthquake; p2 Explosion if wake | p1 Earthquake; p2 woke and Exploded | both top | Top match still exposed a branch concern: the wake-Explosion trade erased Marowak and left Jolteon losing to Tyranitar. |
| 24 | Jolteon 31 vs Tyranitar 94 | p1 Thunder; p2 Earthquake | p1 Thunder miss; p2 Earthquake KO | both top | Endgame was already nearly forced after Marowak traded with Cloyster. |

## Error Classes

- Sleep Clause material underpricing: turn 12 showed that landing sleep on
  Cloyster did not mean Cloyster should burn sleep turns. It could switch out,
  keep Sleep Clause active, and later trade.
- Sleeping absorber preservation: the slept Cloyster was still a route piece
  because it later threatened wake Explosion.
- Low-piece preservation error: turn 16 showed I over-preserved a 17% Snorlax
  whose remaining jobs were weaker than the switch cost.
- Receiver-route miss: turn 18 was severe. With Scizor gone and Jolteon facing
  Tyranitar, direct damage did not create a real route; Agility plus Baton Pass
  to the remaining receiver did.
- Wake-Explosion branch: turn 23 was a top-match but still a warning. If the
  only winning material is Marowak, price whether switching Jolteon into a
  possible wake Explosion preserves a better endgame than attacking.

## Policy Update

Update sleep policy with: after sleep lands on an absorber, first ask whether
the common branch is to switch it out and preserve Sleep Clause material. Then
price whether the sleeper is later spent as Explosion, Spikes, Spin, a wake
attack, or a controlled sack.

Update Baton Pass policy with: when ordinary damage loses, search for the
remaining receiver route even if the receiver is not public yet; quarantine it
as an inferred archetype route under spectator-public rules.

## Next Study Target

Run a constructed 6-scenario quick probe on "sleeping absorber: preserve,
attack, switch, or trade" with one scenario requiring a sack into the sleeper's
wake Explosion.
