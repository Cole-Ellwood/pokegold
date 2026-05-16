# Three-Check Transfer 001 - gen2ou-2544443857 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/gen2ou-2544443857-5tvdxa7m0m3feng39gb3a5lo7368kwypw`

Context source:
Smogon, `GSC OU Winter Seasonal #8: Round 3 (Loser's Bracket)`:
`https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-3-losers-bracket.3777885/`

Mode: focused fresh replay transfer, spectator-public vanilla GSC. No team
sheet was supplied, no Team Preview was assumed, and replay actual moves are a
weak pro-comparison oracle rather than absolute truth.

Selected action:
Fresh transfer after `low_rest_race_review_001`, with three checks active:
sleep used by side before damage, Substitute/setup into receivers, and
full-health active pressure before Gengar or Explosion cash-out. Same-set
caveat: this is paired with `gen2ou-2544449982`, so it is training-transfer
evidence, not final-exam evidence.

## Sources Checked

Local docs:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/reviews/low_rest_race_review_001_gen2ou-2544449982_2026-05-14.md`

Web/current sources:

- Smogon Winter Seasonal #8 Round 3 thread above.
- Pokemon Showdown replay source above.
- Raw log:
  `https://replay.pokemonshowdown.com/gen2ou-2544443857-5tvdxa7m0m3feng39gb3a5lo7368kwypw.log`

## Contamination Control

Local search found no prior `2544443857` artifact before selection. The raw
log was downloaded to `tmp/pokemon_mastery_replays/`. Future turns were not
inspected; each prompt was generated with
`tools/pokemon_mastery/replay_turn_pause.py` and revealed only after the answer
was frozen.

Stopped after turn 16. Turn 14 p1 and turn 15 p1 are unscored because full
paralysis and a pre-move KO hid the selected action.

## Score Summary

Scorable side decisions: 30.

Top-match: 14 / 30.

Acceptable-match: 22 / 30.

Severe blunders: 0.

State errors: 1.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 20 / 30.

Route-converting move chosen: 12 / 21 target converter decisions.

Branch-punish chosen: 8 / 18 named-branch decisions.

Main result:
The three new checks did not cause a severe overcorrection. The strongest
positive turn was turn 9: I correctly covered Exeggutor's route-defining
Explosion with a lower-value Exeggutor owner while also making Explosion top
for the cashing-out side. This is still not broad progress: top-match missed
the provisional 55% gate, and the biggest gap moved to hazard ownership.

Earliest meaningful error:
Turn 1 p1. I expected Sleep Powder from Exeggutor and missed Thief as the
switch-punishing route action into Zapdos.

## Focused Turn Table

| Turn | Side | Frozen top-three | Actual | Top | Accept | Positive | Note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Sleep Powder; Psychic; Explosion/switch | Thief | 0 | 0 | 0 | Missed Thief as switch-punishing utility. |
| 1 | p2 | Sleep absorber switch; stay for Spikes/pressure; attack | Zapdos switch | 1 | 1 | 1 | Correct sleep-absorber class. |
| 2 | p1 | Sleep Powder; Electric/Snorlax handoff; chip | Raikou switch | 0 | 1 | 1 | Correct handoff only as alternative. |
| 2 | p2 | Hidden Power/coverage; switch sleep absorber; Thunder | Hidden Power | 1 | 1 | 1 | Correct active pressure. |
| 3 | p1 | Thunderbolt; Roar; Rest | Thunderbolt | 1 | 1 | 1 | Correct pressure into active and switch. |
| 3 | p2 | Snorlax switch; Ground if available; stay attack | Snorlax switch | 1 | 1 | 1 | Correct special-wall handoff. |
| 4 | p1 | Switch physical owner; stay Roar/Thunderbolt; sleep absorber | Cloyster switch | 1 | 1 | 1 | Correct by owner class. |
| 4 | p2 | Double-Edge; Curse; Lovely Kiss branch | Double-Edge | 1 | 1 | 1 | Correct active pressure. |
| 5 | p1 | Spikes; Surf; Explosion branch only | Spikes | 1 | 1 | 1 | Correct support before cash-out. |
| 5 | p2 | Double-Edge; switch Cloyster/answer; Curse | Cloyster switch | 0 | 1 | 0 | Accepted branch, but top did not build own hazard route. |
| 6 | p1 | Surf; spinblock/handoff; Explosion branch | Toxic | 0 | 0 | 0 | Missed Toxic as status route on opposing Cloyster. |
| 6 | p2 | Rapid Spin; Spikes; Surf | Spikes | 0 | 1 | 1 | Spikes was ranked, not top. |
| 7 | p1 | Rapid Spin; Surf; spinblock/handoff | Raikou switch | 0 | 0 | 0 | Missed proactive Electric handoff. |
| 7 | p2 | Rapid Spin; Surf; preserve Cloyster | Exeggutor switch | 0 | 0 | 0 | Missed counter-handoff into Raikou. |
| 8 | p1 | Switch sleep/status absorber; attack if hidden coverage; preserve Raikou | Crunch | 0 | 1 | 0 | Overprotected against sleep/status and missed active Crunch. |
| 8 | p2 | Sleep Powder; Explosion; status/attack | Stun Spore | 0 | 1 | 1 | Status route acceptable, exact move missed. |
| 9 | p1 | Switch Exeggutor owner; switch Cloyster; Crunch only if no owner | Exeggutor switch | 1 | 1 | 1 | Correct Explosion owner after support was delivered. |
| 9 | p2 | Explosion; Sleep Powder into switch; preserve | Explosion | 1 | 1 | 1 | Correct route-defining cash-out. |
| 10 | p1 | Earthquake/Rock Slide; preserve; Explosion branch | Rapid Spin | 0 | 0 | 0 | Missed Golem Rapid Spin as route progress. |
| 10 | p2 | Cloyster switch; Zapdos; Snorlax attack | Cloyster switch | 1 | 1 | 1 | Correct Golem answer. |
| 11 | p1 | Switch Cloyster; attack only if safe; preserve Golem | Cloyster switch | 1 | 1 | 1 | Correct preserve-Golem handoff. |
| 11 | p2 | Rapid Spin; Surf; switch | Spikes | 0 | 0 | 0 | State error: after p1 Spin, p2 could reset Spikes. |
| 12 | p1 | Rapid Spin if available; Surf; switch Golem | Surf | 0 | 1 | 1 | Surf punished the Zapdos branch. |
| 12 | p2 | Rapid Spin/Surf; preserve Cloyster; switch | Zapdos switch | 0 | 0 | 0 | Missed Zapdos as Surf receiver. |
| 13 | p1 | Raikou switch; Golem if HP not Ice; Surf | Raikou switch | 1 | 1 | 1 | Correct Zapdos handoff. |
| 13 | p2 | Thunder; Rest; switch | Hidden Power | 0 | 0 | 0 | Failed to pick coverage into the Raikou branch. |
| 14 | p2 | Hidden Power into branch; Thunder; Rest | Thunder | 0 | 1 | 1 | Active pressure acceptable, branch coverage missed. |
| 15 | p2 | Thunder; Hidden Power into Golem; switch | Thunder | 1 | 1 | 1 | Correct finish after Raikou stayed. |
| 16 | p1 | Double-Edge; Curse; Rest/utility | Double-Edge | 1 | 1 | 1 | Correct active pressure. |
| 16 | p2 | Switch Normal resist/owner; Cloyster; Snorlax mirror | Tyranitar switch | 0 | 1 | 1 | Correct class, wrong named owner. |

## Lessons

1. The new Explosion boundary transferred on turn 9. I did not overcall
   full-health cash-out, and I did cover a real support-delivered Explosion.
2. Sleep-by-side was not the main failure here. I overprotected on turn 8, but
   that was an active-damage miss, not hidden-info leakage.
3. Hazard ownership is the new bottleneck. Turn 10 missed Rapid Spin as the
   route-converting action; turn 11 then missed that the opponent could simply
   reset Spikes after the spin.
4. Branch action is still incomplete. Turns 7 and 13 punished naming an
   expected receiver without choosing the action that hits that receiver.
5. Hidden-info discipline held. I did not claim Crunch, Rapid Spin, Tyranitar,
   or hidden coverage as facts before reveal.

## Next Rep

Do a short targeted review of turns 10-13 before another fresh packet:

- Golem Rapid Spin as route progress;
- opponent setter resetting Spikes after Spin;
- Zapdos as Surf receiver;
- coverage into the named Raikou branch.
