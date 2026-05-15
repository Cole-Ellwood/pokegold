# Snorlax Set Ambiguity Phaze Cashout Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not a fresh replay score
or final-exam evidence.

Purpose: convert `replay_turn_pause_053` into forced choices around Snorlax
set ambiguity, Toxic into phazer handoff, Starmie hazard-control routing, and
Rest without confirmed Sleep Talk.

Local docs checked:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_053_curselax_phaze_cashout_smogtours-gen2ou-922830_2026-05-14.md`

Web sources checked in the parent work block:

- Smogon Forums, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon Forums, Double-Edge Sucks on Snorlax:
  `https://www.smogon.com/forums/threads/double-edge-sucks-on-snorlax.3560326/`
- Smogon Forums, GSC Introduction to Status:
  `https://www.smogon.com/forums/threads/gsc-introduction-to-status-sleep-paralysis-and-poison-gp-2-2.103998/`

## Score Summary

Scenarios: 5.

Action-policy hits: 5 / 5.

Classification hits: 5 / 5.

Route-job hits: 5 / 5.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Follow with a fresh replay transfer
before treating this as stable.

## Scenario 1 - Lovely Kiss Is Live, Not Default

Public state:

```text
Vanilla GSC. Lead Snorlax faces Cloyster. No moves are revealed. Lovely Kiss
Snorlax is a known current option, but Curse/Rest structures are also common.
Cloyster can set Spikes before Snorlax moves.
```

Tempting move: assume Snorlax must Lovely Kiss because the prior rep featured
Lovely Kiss Snorlax.

Frozen answer: keep both branches live. If the team sheet assigns Lovely Kiss
to Snorlax, sleep is strong; without that evidence, Curse or direct pressure is
also coherent. Confidence: medium.

Classification: set-ambiguity discipline.

Score: pass.

## Scenario 2 - Toxic Before Explosion

Public state:

```text
Vanilla GSC. Cloyster has set Spikes and faces +1 Snorlax. Snorlax has shown
Curse and Body Slam. Steelix is available behind Cloyster and can Roar. Cloyster
has Toxic and Explosion.
```

Tempting move: Explosion immediately because Snorlax is the central route
piece.

Frozen answer: use Toxic first if Snorlax is not immediately sweeping through
the team. Toxic turns Steelix Roar into recurring pressure and preserves
Cloyster's Explosion for a later final gate. Confidence: high.

Classification: support status before cash-out.

Score: pass.

## Scenario 3 - Phazer Handoff After Toxic

Public state:

```text
Vanilla GSC. Snorlax is poisoned, boosted, and attacking Cloyster. Cloyster has
already delivered Spikes and Toxic. Steelix can enter and Roar.
```

Tempting move: keep Cloyster in and cash out now.

Frozen answer: switch Steelix and Roar if Steelix can enter without losing a
larger route. Confidence: high.

Classification: support-to-phazer handoff. The support piece does not need to
spend Explosion once a recurring answer is ready.

Score: pass.

## Scenario 4 - Starmie Reveal Means Hazard Control Route

Public state:

```text
Vanilla GSC. Our side has Spikes. Steelix is repeatedly using Roar. Zapdos is
active into Steelix, but Starmie has just been revealed on the Spikes side.
```

Tempting move: focus only on Zapdos Hidden Power into Steelix.

Frozen answer: include Starmie Rapid Spin or spin-pressure routing in the
branch map. Zapdos coverage is live, but the Starmie reveal says the player may
be trying to remove Spikes rather than win the immediate coverage exchange.
Confidence: medium.

Classification: revealed hazard-control route.

Score: pass.

## Scenario 5 - Rest Is Not Sleep Talk

Public state:

```text
Vanilla GSC. Snorlax has shown Curse, Body Slam, and Rest, then is asleep in
front of opposing Snorlax. Sleep Talk is not revealed. Cloyster is available as
a lower-value Double-Edge absorber and can later Explode.
```

Tempting move: assume Sleep Talk and stay active with Snorlax.

Frozen answer: do not infer Sleep Talk. If Cloyster can absorb Double-Edge and
convert afterward, switch Cloyster and preserve the resting Snorlax. Confidence:
medium-high.

Classification: RestTalk inference boundary.

Score: pass.

## Resulting Checklist

When Snorlax appears early:

1. Which set branches are revealed, and which are only common options?
2. Has the opponent made Curse/Rest, Lovely Kiss, coverage, or Sleep Talk
   public yet?
3. Can support status plus a recurring phazer do more than Explosion now?
4. Does a revealed Starmie change the route from coverage to hazard control?
5. After Rest, is Sleep Talk confirmed, forced by set structure, or merely
   guessed?

## Next Study Target

Fresh replay transfer focused on Snorlax set ambiguity, support status before
cash-out, and RestTalk inference.
