# Replay Turn-Pause 051 Support Entry Explosion Absorber - smogtours-gen2ou-923748 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-923748`.

Mode: spectator-public vanilla GSC replay practice.

Selected measurable action: fresh transfer after
`replay_turn_pause_050_lead_trade_support_coverage_smogtours-gen2ou-924499_2026-05-14.md`.
The target was clean-answer plus coverage-reveal practice with the added
support-mirror classification:

```text
coverage damage into support piece
```

The replay instead produced a compact support-entry and Explosion-absorber
test, so it was stopped after turn 4.

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs and contaminated `934420`.
- Screening printed only replay ID, selected start turn, total turns, route
  move count, and file size.
- The selected replay was `smogtours-gen2ou-923748`.
- The selected start was turn 2. Turns 2-4 were answered before reveal.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_050_lead_trade_support_coverage_smogtours-gen2ou-924499_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/coverage_reveal_absorber_probe_001_2026-05-14.md`

Web sources checked:

- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, Forretress OU Revamp:
  `https://www.smogon.com/forums/threads/forretress-ou-revamp-done.3647111/`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC forum index:
  `https://www.smogon.com/forums/forums/gsc/`

Source note: the Cloyster source says Spikes enable offensive pressure and
Explosion trades after the layer. The Forretress source is useful here because
it makes the support-move menu explicit: Toxic, Giga Drain, Hidden Power,
Explosion, and Spin can all be the support move depending on the opposing
support piece and team plan. This replay adds the defensive mirror: once
Cloyster has set Spikes and is low, Explosion is live, but a side-known Ghost
absorber can blank the cash-out.

## Score Summary

Scored decisions: 6 side decisions.

Top-match: 4 / 6.

Acceptable-match: 5 / 6.

Classification hits: 4 / 6.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 2 p2. I expected the obvious Exeggutor hard
answer to Machamp, but the actual line used Cloyster as the support-seat entry.

Main improvement:

- Turn 4 correctly identified that Cloyster's Explosion was live after Spikes
  and heavy damage.

Main errors:

- Turn 2 p2: missed Cloyster entering before Exeggutor to claim the support
  seat against Machamp.
- Turn 4 p1: identified the Explosion branch but did not map the side-known
  Gengar absorber. In spectator-public mode the Gengar switch was not known,
  so this is a player-side information-set miss rather than a public-state
  overclaim.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Classification |
|---|---|---|---|---|---|
| 2 | Machamp 100 vs Steelix 100; Exeggutor seen | p1 Hidden Power into Exeggutor branch; p2 switch Exeggutor | p2 switched Cloyster; p1 Hidden Power | p1 top, p2 miss | Coverage into pivot; support-seat entry missed. |
| 3 | Machamp 100 vs Cloyster 93 | p1 Cross Chop; p2 Spikes | p2 Spikes; p1 Cross Chop | both top | Support before cash-out. |
| 4 | Machamp 100 vs Cloyster 40 after Spikes | p1 stay / attack if no absorber; p2 Explosion | p1 switched Gengar; p2 Explosion immune | p1 acceptable, p2 top | Side-known Explosion absorber. |

## Reusable Lessons

Hard answer is not always the first response. Cloyster can enter before the
obvious Exeggutor hard answer when its support job changes the route and it
can still threaten a one-time trade afterward.

Once support is delivered and Cloyster is low, Explosion is live, but the
defending side must first ask whether a side-known Ghost absorber exists. In
spectator-public replay practice, mark that distinction explicitly: public
state can name Explosion as live, while player-side advice should switch the
Ghost if available and not needed more elsewhere.

## Next Rep

Construct a compact regression:

- Machamp threatens Steelix and Exeggutor is seen: Cloyster support-seat entry
  is live, not only the hard answer.
- Cloyster sets Spikes and drops low: Explosion is live.
- If side-known Gengar exists and is not irreplaceable, absorb the Explosion
  rather than attacking.
