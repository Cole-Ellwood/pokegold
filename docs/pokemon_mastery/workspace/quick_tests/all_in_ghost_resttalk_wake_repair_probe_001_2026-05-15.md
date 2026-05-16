# All-In Ghost And RestTalk Wake Repair Probe 001 - 2026-05-15

Mode: constructed nonblind policy regression. This is not fresh replay-transfer
evidence and does not count as proof of broad improvement.

Parent artifact:
`workspace/quick_tests/status_receiver_positive_transfer_001_smogtours-gen2ou-919779_2026-05-15.md`

Selected action:
Convert the turn-6 severe hidden-info miss and turn-14 RestTalk wake state miss
from `smogtours-gen2ou-919779` into a four-scenario repair gate.

## Docs Checked

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/workspace/quick_tests/status_receiver_positive_transfer_001_smogtours-gen2ou-919779_2026-05-15.md`

No new web search was needed for this correction probe because the
decision-relevant source is the parent fresh replay plus existing local policy.
Use web search again before selecting another fresh replay or extracting a new
external rule.

## Score Summary

Scenarios: 4.

Correct top action: 4 / 4.

Immunity-owner naming hits: 4 / 4.

Rest/wake timing hits: 4 / 4.

Hidden-information discipline hits: 4 / 4.

Positive-selection: 4 / 4.

Route-converting move chosen: 4 / 4.

Branch-punish chosen: 4 / 4.

Severe blunders: 0.

Hidden-info errors: 0.

State errors: 0.

Mechanics errors: 0.

Measurement status: regression only. The next countable test must be a fresh
unseen replay segment with this cash-out and RestTalk wake gate active.

## Scenario 1 - Parent Failure: Exeggutor Can Boom, Hidden Ghost Is Live

Public state:
Vanilla GSC spectator-public. Our Exeggutor faces a paralyzed Snorlax. Sleep
Powder/Stun Spore pressure has already created value, but Exeggutor is still a
route piece. Opponent has revealed Snorlax and Cloyster; unrevealed team slots
remain. No Ghost has been revealed, but hidden Gengar or Misdreavus is legal
and would blank Explosion. Slow play with a switch, status, Psychic/Giga Drain,
or preservation still exists.

Tempting move:
Explosion because Snorlax is the visible route piece.

Frozen answer:
Top action: preserve or hand off, confidence medium.

Ranked candidates:

1. Switch or preserve Exeggutor while naming the hidden Ghost immunity branch.
2. Psychic/Giga Drain/status only if it improves through the likely next board.
3. Explosion only as a high-risk read that explicitly loses to hidden Ghost
   and only if slow play loses.

Score:
Correct. The hidden Ghost is possible-only, but Explosion depends on it not
existing. Because slow play is available, possible-only must block the all-in
move from being top rather than anchoring a counter-read.

## Scenario 2 - Revealed Ghost Makes The Cash-Out A Branch To Beat

Public state:
Vanilla GSC spectator-public. Our Forretress has Spikes up and faces RestTalk
Snorlax at 48%. Forretress has Explosion and Rapid Spin revealed. Opposing
Gengar is revealed healthy and has already switched into a support piece once.
Our Tyranitar is public and can enter Snorlax while threatening Roar plus
Spikes.

Tempting move:
Explosion into Snorlax.

Frozen answer:
Top action: Tyranitar handoff, confidence medium-high.

Ranked candidates:

1. Switch Tyranitar to own Snorlax and preserve the hazard route through Roar.
2. Rapid Spin only if removing our side's Spikes changes the next board more
   than meeting Snorlax/Gengar now.
3. Explosion only if Gengar is removed, trapped, or the line is explicitly a
   losing-read cash-out.

Score:
Correct. The revealed Ghost is the named branch, so the positive move is the
handoff that beats the Snorlax/Gengar map rather than the all-in active-target
trade.

## Scenario 3 - Explosion Is Allowed When The Immunity Check Is Closed

Public state:
Vanilla GSC spectator-public. Our low Exeggutor faces the final opposing
Snorlax route converter. All remaining opposing Pokemon are revealed: Snorlax,
Cloyster at 12%, and Zapdos at 31%. No Ghost, Rock, or Steel immunity owner is
alive. If Snorlax survives this turn, it Rests or Curses into a winning route.
Our post-trade converter is named: Zapdos cleans once Snorlax is gone.

Tempting overcorrection:
Switch out because Explosion has caused prior hidden-info errors.

Frozen answer:
Top action: Explosion, confidence high.

Ranked candidates:

1. Explosion to remove the exact blocker and open Zapdos.
2. Sleep/status only if it prevents the same Rest/Curse route immediately.
3. Switch only if the incoming owner still beats Snorlax after it moves.

Score:
Correct. The repair rule is not "never boom." It is "boom only after the
immunity owners, target, and post-trade converter are named, and slow play
loses."

## Scenario 4 - RestTalk Wake Timing Before Choosing Into Snorlax

Public state:
Vanilla GSC spectator-public. Opposing Snorlax used Rest, then later used Sleep
Talk twice while asleep. It has revealed Double-Edge, Earthquake, Rest, and
Sleep Talk. Our Tyranitar is at 72% and has Roar and Rock Slide revealed, with
Spikes on the opponent's side. The next turn may be the Snorlax wake turn.

Tempting move:
Treat Snorlax as still asleep and rank only Sleep Talk branches.

Frozen answer:
Top action for Tyranitar: Rock Slide or preserve according to HP, but the
answer must price awake Earthquake before committing. If Tyranitar survives and
the damage clock is converting, Rock Slide is valid; if survival or route job
fails, switch to the Earthquake owner.

Ranked candidates:

1. Rock Slide only if Tyranitar survives awake Earthquake and the damage route
   remains better than phazing.
2. Switch to the Earthquake owner if Tyranitar's post-hit job is lost.
3. Roar if the phaze loop beats both Sleep Talk and awake Earthquake branches.

Score:
Correct. Do not leave Sleep Talk as the only branch after two sleep actions.
The state check is whether Snorlax can wake and choose Earthquake before our
line is safe.

## Repair Checklist

Before making an all-in support cash-out top:

1. Name the target's route job and the post-trade converter.
2. Name revealed immunity, absorber, or low-value sack owners.
3. Name plausible hidden immunity classes in no-Team-Preview.
4. If a plausible hidden immunity blanks the all-in move and slow play exists,
   preserve, pressure, setup, phaze, or hand off instead.
5. If slow play loses and immunity owners are closed, cash out without
   overcorrecting.

Before choosing into RestTalk:

1. Count the public Rest and Sleep Talk turns.
2. Ask whether the target can wake and select a real move this turn.
3. Score the awake move branch before treating Sleep Talk as the only line.
4. Choose damage, phaze, preservation, or handoff based on the next board, not
   on stale sleep status.

Next transfer:
Fresh status-receiver positive-selection transfer. Score ranked top-three
candidates, positive-selection, route conversion, branch punish, top-match,
acceptable-match, state errors, hidden-info errors, mechanics errors, and
severe blunders separately.
