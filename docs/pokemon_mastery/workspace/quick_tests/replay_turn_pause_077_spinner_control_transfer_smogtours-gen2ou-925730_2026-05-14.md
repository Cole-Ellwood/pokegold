# Replay Turn-Pause 077 Spinner Control Transfer - smogtours-gen2ou-925730 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-925730`.

Context source:
`https://www.smogon.com/forums/threads/adpl-ix-week-4.3780197/page-2`.

Mode: spectator-public vanilla GSC replay turn-pause. No team sheet was
supplied, and no Team Preview was assumed.

Selected measurable action: transfer
`spinner_removed_hazard_cashout_probe_001` to a fresh no-keyword-screen replay.
The selected replay was pulled from current ADPL IX Week 4 replay links and
checked locally for no prior `925730` use before opening the raw log.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/workspace/quick_tests/spinner_removed_hazard_cashout_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`

Web sources checked:

- Smogon ADPL IX Week 4, page 1 and page 2.
- Replay source `smogtours-gen2ou-925730`.

Contamination control:

- Raw `.log` was downloaded to `tmp/pokemon_mastery_replays/`.
- The replay UI was not watched.
- The replay was not screened for Rapid Spin, Spikes, Explosion, Toxic, or
  other content keywords before selection.
- Turns were revealed only after frozen answers.

## Score Summary

Decisions: 14 side decisions from turns 1-7.

Top-match: 6 / 14.

Acceptable-match: 10 / 14.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Earliest meaningful error: turn 1 p2. I correctly named the expected Zapdos
sleep-absorber switch for p1, but missed Exeggutor using Thief to punish that
branch instead of trying immediate sleep.

Target error: turns 5 and 7. I overcorrected from replay 076's Cloyster
Explosion lesson. This replay showed the opposite boundary: Toxic can control
Starmie while preserving Cloyster, and after Starmie is poisoned the next route
can be a pressure handoff rather than immediate Spikes reset or cash-out.

Stop reason: the same controlled-spinner handoff error appeared twice, so the
run stopped under the replay protocol instead of continuing into unrelated
turns.

## Turn 1

Public state: p1 Snorlax 100% vs p2 Exeggutor 100%.

Frozen p1 answer: switch to the sleep absorber, preferably Zapdos if this is
the revealed route. Confidence: medium. Route reason: preserve Snorlax from
early sleep and let the absorber take the clause. Serious alternative: attack
if no absorber exists. Worst branch: Exeggutor punishes the switch with Thief
or paralysis instead of sleep.

Frozen p2 answer: Sleep Powder. Confidence: high. Serious alternatives: Stun
Spore or Thief if expecting the absorber.

Actual choices: p1 switched Zapdos; p2 used Thief.

Grade: p1 top. p2 miss. Reusable lesson: when the absorber switch is obvious,
the Exeggutor branch-action can be item removal, not only sleep.

## Turn 2

Public state: p1 Zapdos 90% vs p2 Exeggutor 100%, Thief revealed.

Frozen p1 answer: attack Exeggutor, with Hidden Power Ice or the strongest
available attack; Thunder is serious if the switch is likely. Confidence:
medium.

Frozen p2 answer: Sleep Powder. Confidence: medium-high. Serious alternative:
switch to Snorlax or an Electric answer if the Zapdos attack is priced higher
than sleep.

Actual choices: p2 switched Snorlax; p1 used Thunder.

Grade: p1 acceptable, p2 miss. Reusable lesson: after Thief lands, Exeggutor
does not have to finish the sleep job immediately.

## Turn 3

Public state: p1 Zapdos 90% vs p2 Snorlax 77%, Thunder revealed.

Frozen p1 answer: stay and use Thunder. Confidence: medium. Serious
alternative: switch to a physical wall if Snorlax's immediate pressure matters
more than Zapdos damage.

Frozen p2 answer: Lovely Kiss if available; otherwise immediate physical
pressure with Body Slam or Double-Edge. Confidence: medium.

Actual choices: p1 switched Cloyster; p2 used Double-Edge and crit Cloyster.

Grade: p1 acceptable but not top. p2 acceptable. Reusable lesson: p1 valued
preserving Zapdos's route job more than another Thunder into Snorlax.

## Turn 4

Public state: p1 Cloyster 46% vs p2 Snorlax 74%.

Frozen p1 answer: Spikes. Confidence: high. Serious alternatives: Explosion if
Snorlax must be removed now, or Surf/Toxic if a spinner is the expected switch.

Frozen p2 answer: switch to the hazard answer, especially Starmie if available.
Confidence: low-medium. Worst branch: Cloyster Explodes into the switch.

Actual choices: p2 switched Starmie; p1 used Spikes.

Grade: both top. Reusable lesson: the hazard subgame is live as soon as
Starmie enters; p1 must decide whether to control, block, or cash out.

## Turn 5

Public state: p1 Cloyster 52% with Spikes/Toxic unrevealed vs p2 Starmie 100%
with Spikes on p2's side.

Frozen p1 answer: if a confirmed safe spinblocker exists, switch it in;
otherwise Explosion is the direct route cash-out because Starmie can remove
Spikes before Cloyster moves. Do not click generic Toxic unless preserving
Cloyster is the named route. Confidence: medium.

Frozen p2 answer: Rapid Spin. Confidence: high.

Actual choices: p2 used Rapid Spin; p1 used Toxic and missed.

Grade: p1 miss, p2 top. Reusable lesson: this was the opposite boundary from
replay 076. Toxic can be the route move when it controls Starmie while keeping
Cloyster available for later Spikes.

## Turn 6

Public state: p1 Cloyster 56% with Spikes/Toxic vs p2 Starmie 100%, Rapid Spin
and Surf revealed, no hazards up.

Frozen p1 answer: Toxic again. Confidence: medium-high. Route reason: poison
the spinner before trying to make a future Spikes reset stick.

Frozen p2 answer: switch to avoid Toxic, with Surf as a serious stay-in
alternative if the goal is to push Cloyster low. Confidence: low-medium.

Actual choices: p2 used Surf; p1 used Toxic and poisoned Starmie.

Grade: p1 top, p2 acceptable. Reusable lesson: Starmie can accept poison if
Surf pushes Cloyster into a handoff decision.

## Turn 7

Public state: p1 Cloyster 34% with Spikes/Toxic vs p2 poisoned Starmie 100%,
no hazards up.

Frozen p1 answer: Spikes. Confidence: medium. Route reason: Starmie cannot
remove a layer before it is set this turn, and poison makes future spinning
harder.

Frozen p2 answer: Surf. Confidence: medium-high.

Actual choices: p1 switched Zapdos; p2 used Surf.

Grade: p1 miss, p2 top. Reusable lesson: once Starmie is poisoned, Cloyster's
job may be to preserve the future reset while Zapdos applies pressure. Setting
Spikes immediately was active-looking but did not name the next board well.

## Error Classes

- Controlled-spinner handoff: repeated target miss on turns 5 and 7.
- Branch-action after naming: early Exeggutor used Thief, then switched, rather
  than completing the expected sleep script.
- No mechanics, hidden-info, or state errors were scored.

## Policy Update

No new constructed probe is needed. The existing
`statused_spinner_handoff_probe_001` already contains the rule this replay
tested: after the spinner is statused, ask whether pressure handoff or
preservation converts better than another immediate support click.

## Next Rep

Run another fresh no-keyword-screen transfer with
`statused_spinner_handoff_probe_001` and `spinner_removed_hazard_cashout_probe_001`
both loaded. Before any Cloyster/Starmie or support/spinner turn, explicitly
answer:

1. Is the spinner uncontrolled, status-controlled, or safely spinblocked?
2. Does the support piece still have a future entry and route job?
3. Which pressure piece converts the status or hazard state?
4. Is Explosion or immediate Spikes the only route, or just the most active
   move?
