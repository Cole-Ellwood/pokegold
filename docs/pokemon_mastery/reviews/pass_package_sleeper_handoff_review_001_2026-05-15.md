# Pass Package/Sleeper Handoff Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/pass_package_sleeper_handoff_transfer_001_gen2ou-2608087104_2026-05-15.md`

Reason for study:
The fresh transfer was not perfect. It held the severe-blunder gate, but it
missed Rest/Sleep Talk handoffs, Vaporeon/Jynx package conversion, Heal Bell
status-map reset, and the Cloyster coverage-before-cash-out branch.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `policy_cards/support_handoff_after_job.md`
- `reviews/tempo_coverage_sack_review_001_2026-05-15.md`

Current web sources:

- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Jynx GSC OU:
  `https://www.smogon.com/forums/threads/jynx-gsc-ou-qc-2-2-gp-2-2.3667481/`
- Smogon Snorlax GSC OU:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon Zapdos GSC OU:
  `https://www.smogon.com/forums/threads/zapdos-qc-2-2-gp-2-2.3673848/`
- Smogon GSC Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Remembering Our Roots Redux, Vaporeon section:
  `https://www.smogon.com/smog/issue35/remembering-our-roots`

## Confirmed Source Lessons

Blissey and cleric reset:
The GSC threatlist describes Blissey as a special wall that can use Heal Bell,
Toxic, and Flamethrower. Heal Bell means status-map assumptions are temporary:
formerly poisoned Tyranitar or Cloyster cannot be treated as permanent sleep
absorbers after the cleric turn. In the replay, this mattered immediately
around Jynx and later around Tyranitar.

Snorlax Rest/Sleep Talk:
Smogon Snorlax material says Rest lets Snorlax answer Zapdos/Raikou and shrug
off status, while warning that non-Sleep Talk Rest gives the opponent free
turns. The GSC status article lists RestTalk Snorlax as a common Sleep Talk
user and notes that Snorlax handles paralysis unusually well. Once Sleep Talk
was revealed, switching sleeping Snorlax into Blissey's Toxic was a positive
handoff, not passive preservation.

Vaporeon/Jynx package:
The GSC sample-team source explicitly frames Growth + Baton Pass Vaporeon as a
way to power up dangerous special attackers including Jynx, and notes Hydro
Pump plus Ice Beam as useful coverage on that package. The Jynx source says
Substitute mitigates frailty and status weakness while giving extra turns and
safety. In the transfer, dry Baton Pass to Jynx, Substitute before the
Lovely Kiss cycle, and Ice Beam into Zapdos all fit the package plan.

Zapdos as phazer or RestTalker:
Smogon Zapdos material distinguishes RestTalk tank sets from offensive phazer
sets with Whirlwind. Once Whirlwind was revealed, low Zapdos was still a route
piece because it avoided Spikes and could phaze through the hazard clock.
Coverage into that phazer needed a higher rank than a generic safe switch.

Cloyster cash-out:
The GSC threatlist presents Cloyster as more than Spikes: it has Surf/Ice Beam,
Toxic, Rapid Spin, Explosion, and Icy Wind/Clamp support for Explosion. The
transfer reinforced that if Rhydon is the named Explosion absorber, coverage or
setup before the cash-out can be the real branch-punish.

## Policy Corrections

The existing policy-card structure is sufficient, but three cards needed
tighter wording:

- `sleep_absorber_and_set_ambiguity.md`: add the sleeping status-absorber
  handoff and the Heal Bell status-map reset.
- `branch_action_after_naming.md`: add pass/Substitute package resolution after
  Baton Pass, Growth, Substitute, coverage, or phaze is revealed.
- `cashout_boundary.md`: add a named-resist check before Explosion/Self-Destruct
  and rank coverage/setup if it beats that branch.

## Measurement Note

Not progress. The run produced 0 severe, state, hidden-info, and mechanics
errors, but 17/49 top-match and 26/49 route-converting moves are below the
current proof gate. Acceptable and positive-selection were not enough because
the repeated misses were exactly about route conversion rather than only safety.
