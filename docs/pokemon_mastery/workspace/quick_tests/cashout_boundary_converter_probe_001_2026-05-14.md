# Cashout Boundary Converter Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not a fresh replay score
or final-exam evidence.

Purpose: convert `replay_turn_pause_056` into forced choices around the
boundary between low-support preservation and immediate converter-defined
Explosion.

Local docs checked:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_056_immediate_route_trade_converter_smogtours-gen2ou-922569_2026-05-14.md`

Web sources checked in the parent work block:

- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, Explosion in GSC:
  `https://www.smogon.com/forums/threads/explosion-in-gsc-qc-2-2-gp-2-2.3484961/`
- Smogon Forums, Thief:
  `https://www.smogon.com/forums/threads/thief.3543261/`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Classification hits: 4 / 4.

Route-job hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Follow with a fresh replay transfer
before treating this as stable.

## Scenario 1 - Lead Trade Into Exact Route Piece

Public state:

```text
Vanilla GSC. Lead Exeggutor faces Zapdos. Zapdos is the opposing Electric
pressure piece. Your team has a route that benefits heavily from removing
Zapdos early, and Exeggutor's later job is less valuable than that removal.
```

Tempting move: preserve Exeggutor because lead Explosion is high-commitment.

Frozen answer: Explosion is live and can be correct if Zapdos is the exact
route piece and the post-trade structure benefits. Confidence: medium.

Classification: immediate route trade.

Score: pass.

## Scenario 2 - Support Before Cash-Out

Public state:

```text
Vanilla GSC. Forretress enters against Snorlax after the lead trade. No Spikes
are up yet. Snorlax has not boosted yet. Forretress has Spikes and Explosion.
```

Tempting move: Explosion immediately because Snorlax is important.

Frozen answer: set Spikes first if Snorlax cannot immediately sweep and the
layer changes the converter's board. Confidence: high.

Classification: support before route trade.

Score: pass.

## Scenario 3 - Cash Out After Boost And Support

Public state:

```text
Vanilla GSC. Forretress has already set Spikes. Opposing Snorlax used Curse
and is now boosted. Machamp is ready to enter after a trade. Forretress has
Explosion and no better recurring route job.
```

Tempting move: Toxic or preserve Forretress because recent drills punished
automatic Explosion.

Frozen answer: Explosion. Confidence: high.

Classification: converter-defined cash-out. The support job is done, the
target is exact, and Machamp is the named receiver.

Score: pass.

## Scenario 4 - Coverage Into Ghost/Pivot Branch

Public state:

```text
Vanilla GSC. Machamp entered after Forretress Exploded into Snorlax. Opponent
can preserve Snorlax by switching Gengar, but can also pivot again to Marowak
or another branch after absorbing Cross Chop.
```

Tempting move: always Cross Chop because Snorlax is low.

Frozen answer: Cross Chop is top if Snorlax stays; once Gengar is revealed,
coverage such as Hidden Power can be the route move into the Ghost/pivot map.
Confidence: medium.

Classification: converter branch coverage.

Score: pass.

## Resulting Checklist

Before a self-KO trade:

1. Is the target exact or replaceable?
2. Has the support job that enables the receiver already been delivered?
3. Who is the named converter after the trade?
4. Does delay allow Rest, setup, escape, or a better absorber?
5. Is preservation still a real route, or only a reaction to prior over-booms?

## Next Study Target

Fresh replay transfer on the cash-out boundary: low-support preservation versus
immediate converter-defined Explosion.
