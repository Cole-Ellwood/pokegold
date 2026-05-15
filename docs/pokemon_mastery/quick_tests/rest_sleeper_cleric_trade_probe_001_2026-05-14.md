# Rest Sleeper Cleric Trade Probe 001 - 2026-05-14

Source parent:
`quick_tests/paired_handoff_transfer_001_smogtours-gen2ou-920763_2026-05-14.md`.

Mode: constructed nonblind policy regression. This is not fresh replay proof.
It turns the `920763` misses into four compact decisions before another fresh
transfer.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/policy_cards/support_handoff_after_job.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/quick_tests/paired_handoff_transfer_001_smogtours-gen2ou-920763_2026-05-14.md`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Rest-sleeper handoff hits: 2 / 2.

Support-before-cashout hits: 1 / 1.

Setup-after-handoff-out hits: 1 / 1.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Transfer to a fresh replay before treating
the correction as stable.

## Scenario 1 - Safe Sleep Turn Burn

Public state:

```text
Vanilla GSC spectator-public style. Your Cloyster has just used Rest and is at
high HP asleep. The opposing Cloyster is active, cannot threaten a route loss
this turn with Surf, and your current route still benefits from burning one
sleep turn before handing off.
```

Tempting move: switch immediately because sleeping Pokemon are often saved for
Sleep Clause value.

Frozen answer: stay for the safe sleep turn unless a concrete counter-pivot or
setup branch changes the next board. Confidence: medium.

Classification: Rested support piece should stay one turn.

Score: pass.

## Scenario 2 - Save The Rested Support Piece

Public state:

```text
Vanilla GSC spectator-public style. Your Rested Cloyster has already absorbed
the needed pressure, your side has a clean Raikou entry, and the opposing
Cloyster can keep pressing Surf or reset Spikes. Cloyster still has later
spinner or absorber value.
```

Tempting move: keep burning sleep turns because waking looks close.

Frozen answer: switch the Rested Cloyster out and save it; take the clean
handoff to the piece that owns the next board. Confidence: medium.

Classification: Rested support piece should be preserved after its job is done.

Score: pass.

## Scenario 3 - Hard Answer Creates Support Handoff

Public state:

```text
Vanilla GSC spectator-public style. Your Raikou has forced Cloyster out, and
Steelix entered on Thunder. You can name Steelix as the hard answer. Your team
has Miltank available to perform a cleric or support job, while Raikou's visible
active pressure does not improve the route.
```

Tempting move: look for active coverage or keep attacking because the receiver
has been named.

Frozen answer: hand off to the support piece that owns the Steelix board unless
the active move has confirmed route-changing value. Confidence: medium.

Classification: hard-answer receiver invites support handoff.

Score: pass.

## Scenario 4 - Cleric Before Explosion

Public state:

```text
Vanilla GSC spectator-public style. Your Miltank faces a boosted Steelix. A
saved Rested teammate will matter if it wakes. Steelix can cash out with
Explosion this turn, and Miltank may not survive.
```

Tempting move: Growl, attack, or switch because Steelix is boosted.

Frozen answer: use Heal Bell first if waking the saved teammate changes the
route and Miltank is likely to be removed anyway. Confidence: medium.

Classification: unique support action before incoming cash-out.

Score: pass.

## Resulting Checklist

Before choosing in a Rest-sleeper handoff position:

1. What does one more sleep turn buy?
2. What later job is lost if the sleeper stays too long?
3. Which teammate owns the hard-answer board?
4. If the support piece may die this turn, what unique action must happen first?

## Next Transfer Check

Run a fresh no-keyword-screen replay transfer and score:

- safe sleep-turn burn;
- sleeper preservation handoff;
- support handoff into hard answer;
- support-before-cashout;
- setup after handoff-out.
