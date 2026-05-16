# SubSpin Named-Absorber Cash-Out Probe 001 - 2026-05-15

Mode: constructed nonblind policy regression after
`item_package_followup_transfer_002_smogtours-gen2ou-935855_2026-05-15.md`.

Purpose:
Test the immediate lesson from the imperfect fresh transfer before starting
another replay: fast SubSpin Starmie must change the hazard-control ranking,
and Exeggutor/Cloyster Explosion must be ranked by named route target rather
than by "low HP" or "preserve by default."

Local docs checked:

- `reviews/subspin_exeggutor_cashout_review_001_2026-05-15.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/branch_action_after_naming.md`
- `replay_turn_pause_protocol.md`

This probe is not fresh evidence. The scenarios were authored after seeing the
miss, so the score is a regression/checklist result only.

## Score Summary

- Scenarios: 4
- Action-policy hits: 4/4
- Branch-bundle hits: 4/4
- Severe blunders: 0
- State errors: 0
- Hidden-info errors: 0
- Mechanics errors: 0

## Scenario 1 - Substitute Blocks Toxic Before Spin

Public state:
Vanilla GSC. Our Cloyster is active at 100% with Spikes / Toxic / Surf /
Explosion revealed. Opposing Starmie is active at 82% behind Substitute with
Substitute revealed. Spikes are on Starmie's side. Our Zapdos is healthy and
can pressure Starmie; no spinblocker is revealed.

Frozen answer:
Switch Zapdos or use Surf to break Substitute if Zapdos cannot enter. Top is
Zapdos handoff when it safely forces Starmie to attack, Recover, or leave.
Do not repeat Toxic: the real target is protected. Do not make Spikes the top
move while Starmie can keep the barrier and spin next turn.

Policy key:
Substitute changed the route from "poison spinner" to "punish the protected
spinner cycle."

Grade: complete.

## Scenario 2 - Reset Only If The Spinner Cannot SubSpin For Free

Public state:
Vanilla GSC. Our Cloyster is active at 94% against opposing Starmie at 76%
behind Substitute. No Spikes are on either side because Starmie has just used
Rapid Spin. Our Zapdos is at 72%; our Snorlax is asleep but has RestTalk
revealed.

Frozen answer:
Switch Zapdos if it can still pressure Starmie through the Substitute. Surf to
break Substitute is the main alternative if Zapdos is too low. Spikes reset is
third: it is correct only if Starmie cannot cheaply keep Substitute and Spin
again. Explosion is a branch only if removing Starmie opens the named endgame.

Policy key:
After Spin, ask whether the active setter can reset, but also ask whether the
spinner's revealed protection makes the reset unstable.

Grade: complete.

## Scenario 3 - Exeggutor Has Drawn The Electric Absorber

Public state:
Vanilla GSC, no Team Preview. Our Exeggutor is active at 78% and confused
after Dynamic Punch. Opposing Zapdos is active at 100% and has Thunder
revealed. Opponent has revealed Tyranitar, Steelix, Forretress, Starmie, and
RestTalk Snorlax; no Ghost has been revealed. Our remaining route needs Zapdos
removed so our own Zapdos or Machamp can convert.

Frozen answer:
Explosion is the top high-risk route trade if Zapdos is expected to attack or
stay. The answer must name the revealed Tyranitar/Steelix/Forretress resist
branches and the post-trade converter. If the opponent is likely to pivot to a
resist, use status or switch instead of booming.

Policy key:
Preservation is not automatically positive selection when the named absorber
is active and the trade opens the route.

Grade: complete.

## Scenario 4 - Do Not Boom Into The Wrong Branch

Public state:
Vanilla GSC, no Team Preview. Our Exeggutor is active at 82% against opposing
Zapdos at 100%. Opponent has revealed Gengar and Steelix. Zapdos has already
used Substitute and is not required for the opponent's defensive route. Our
Exeggutor is the only reliable Machamp and Ground check left.

Frozen answer:
Do not make Explosion top. The revealed Gengar and Steelix branches can blank
or cheapen the trade, Substitute can absorb the target, and Exeggutor still has
a live defensive job. Use Sleep Powder/Stun Spore or switch to the Electric
answer, with Explosion only as an explicitly labeled read if slow play loses.

Policy key:
Named-absorber cash-out does not override the immunity guard or the support
piece's remaining route job.

Grade: complete.

## Resulting Checklist

Before the next fresh replay, use this compact rank:

1. Is a protection state active or revealed?
2. Does status/Explosion affect the real target or only the barrier?
3. Which pressure piece punishes the protected spinner or absorber now?
4. If Explosion is possible, what route opens and what role is lost?
5. Which revealed or possible-only immunity/resist branch makes the trade bad?

Next countable check:
Fresh replay transfer focused on SubSpin shield, named-absorber Explosion, and
volatile-state carry-forward. Keep this probe separate from progress evidence.
