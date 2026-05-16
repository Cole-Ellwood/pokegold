# Setup Phaze Support Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/replay_turn_pause_068_support_action_transfer_smogtours-gen2ou-913236_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks whether replay 068's
Reflect, Roar, Curse, and low-support Spikes misses can be restated as forced
choices. It is not fresh replay-transfer evidence.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_068_support_action_transfer_smogtours-gen2ou-913236_2026-05-14.md`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Classification hits: 4 / 4.

Route-job hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Follow with a fresh replay transfer before
treating this support chain as stable.

## Scenario 1 - Nidoking Reflect Before Handoff

Public state:

```text
Vanilla GSC spectator-public state. Your Nidoking leads into opposing Snorlax.
Snorlax can pressure immediately with Double-Edge, Flamethrower, Curse, or
another coverage move. You have Cloyster and Tyranitar available as possible
handoff pieces. Nidoking has Reflect.
```

Tempting move: Lovely Kiss or Earthquake because Nidoking is active and can
force progress now.

Frozen answer: use Reflect if it makes the next handoff to Cloyster or
Tyranitar safer and preserves Nidoking's later role. Attack or sleep is correct
when it immediately creates a route that Reflect does not. Confidence: medium.

Classification: setup support before absorber handoff.

Score: pass.

## Scenario 2 - Tyranitar Roar As Spikes Conversion

Public state:

```text
Vanilla GSC spectator-public state. Your Tyranitar faces opposing Snorlax while
Reflect is still active on your side and Spikes are on the opponent's side.
Tyranitar has Roar. Snorlax can keep pressing with resisted Double-Edge or
coverage, but phazing will drag a receiver through Spikes.
```

Tempting move: Screech, Curse, or Rock Slide to win the active matchup.

Frozen answer: use Roar when the Reflect window and Spikes make phazing the
best conversion. Direct pressure is correct when the dragged receiver map is
worse than keeping the current target in. Confidence: medium.

Classification: phaze support converts hazard state.

Score: pass.

## Scenario 3 - Curse Before Attacking The Receiver

Public state:

```text
Vanilla GSC spectator-public state. Your Tyranitar faces opposing Zapdos with
Spikes on the opponent's side. Zapdos can Protect or switch to a Tyranitar
receiver such as Forretress. Tyranitar has Curse and Rock Slide.
```

Tempting move: Rock Slide because Zapdos is on screen.

Frozen answer: use Curse if Zapdos is likely to scout or leave and the boost
makes the incoming receiver much worse next turn. Rock Slide is correct when
Zapdos staying is the route-relevant branch or when the receiver takes enough
damage without the boost. Confidence: medium.

Classification: setup action changes the receiver map before damage.

Score: pass.

## Scenario 4 - Low Forretress Uses Spikes Before Cash-Out

Public state:

```text
Vanilla GSC spectator-public state. Your Forretress is at 23% against a boosted
Tyranitar and will likely die soon. It has already used Toxic. Your opponent's
side has Spikes, but your side does not. Forretress can set Spikes, explode, or
switch out with little future entry value.
```

Tempting move: Explosion because Forretress is low and has already used one
support move.

Frozen answer: use Spikes if the layer is still the route job and Explosion
does not open a named converter. Cash out only when the trade removes a blocker
or creates a concrete follow-up that the layer cannot. Confidence: medium.

Classification: low support piece still has a route job before cash-out.

Score: pass.

## Resulting Checklist

Before choosing a support/setup branch action:

1. Does a setup move make the next handoff safer?
2. Does phazing convert an existing hazard or screen state better than damage?
3. Does boosting before attacking make the likely receiver worse?
4. Is the low support piece actually done, or is one last support job still
   route-defining?
5. What concrete converter opens if the piece cashes out instead?

## Next Transfer Check

Run a fresh no-keyword-screen replay with
`policy_cards/branch_action_after_naming.md` loaded. Treat Reflect, Roar,
Curse, Toxic, Screech, Spikes, and other support/setup moves as live candidate
actions whenever they change the receiver map or route clock.
