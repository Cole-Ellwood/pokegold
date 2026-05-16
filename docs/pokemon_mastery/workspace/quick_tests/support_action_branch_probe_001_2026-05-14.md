# Support Action Branch Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/replay_turn_pause_067_hidden_role_transfer_smogtours-gen2ou-912841_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks whether replay 067's
support-action branch misses can be restated as forced choices. It is not fresh
replay-transfer evidence.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_067_hidden_role_transfer_smogtours-gen2ou-912841_2026-05-14.md`

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
treating this support-action branch boundary as stable.

## Scenario 1 - Toxic Before Spikes In The Cloyster Mirror

Public state:

```text
Vanilla GSC spectator-public state. Your Cloyster is active against opposing
Cloyster. Spikes are on your side only. The opposing Cloyster has already set
Spikes and can continue support work, Surf, switch, or cash out. Your Cloyster
has Spikes and Toxic.
```

Tempting move: set Spikes immediately to equalize the layer count.

Frozen answer: use Toxic if poisoning opposing Cloyster changes its future
Spikes, Spin, Surf, and Explosion map more than immediately equalizing hazards.
Spikes is correct when the layer itself is the route gate; here the opposing
support piece's future job is the gate. Confidence: medium.

Classification: support action before layer equality.

Score: pass.

## Scenario 2 - Screech Into The Snorlax Receiver

Public state:

```text
Vanilla GSC spectator-public state. Your Tyranitar is active against opposing
Zapdos. Zapdos is likely to leave to Snorlax. Tyranitar has Screech and Rock
Slide revealed or strongly represented by set context.
```

Tempting move: Rock Slide because Zapdos is on screen and weak to Rock.

Frozen answer: use Screech if Snorlax is the named best receiver and lowering
its Defense changes the next board. Rock Slide is correct if Zapdos staying is
the best branch or the receiver chip matters more than the Defense drop.
Confidence: medium.

Classification: support action beats named receiver.

Score: pass.

## Scenario 3 - Stay To Screech Despite Earthquake

Public state:

```text
Vanilla GSC spectator-public state. Your Tyranitar is healthy against opposing
Snorlax. Snorlax has Earthquake or is highly likely to carry it. Tyranitar can
survive one Earthquake, and Screech will make Snorlax immediately punishable or
force a reset switch.
```

Tempting move: switch because Earthquake is super effective.

Frozen answer: stay and Screech if the Defense drop changes the route more than
the Earthquake damage costs. Switch when Tyranitar cannot survive, when the drop
does not create a converter, or when a hard answer preserves more route value.
Confidence: medium.

Classification: setup/support action changes the next board.

Score: pass.

## Scenario 4 - Coverage After Screech Changes The Receiver Map

Public state:

```text
Vanilla GSC spectator-public state. Tyranitar's Screech has already forced
Snorlax to respect Defense drops. The opponent brings in Golem as a reset or
pressure piece. Golem can Earthquake, but Snorlax may also switch back in to
catch a Rock move or reset the sequence. Tyranitar has Earthquake.
```

Tempting move: switch out because Golem threatens Earthquake.

Frozen answer: use Earthquake if it punishes Golem staying and still gets real
damage into Snorlax returning. Switching is correct if Tyranitar no longer
survives the active punish or if the receiver branch is covered better by a
different teammate. Confidence: medium.

Classification: coverage move after support action changes receiver incentives.

Score: pass.

## Resulting Checklist

When the branch-beating move may be support/setup rather than damage:

1. What receiver is being named?
2. Does Toxic, Screech, Reflect, Curse, or another support move make that
   receiver worse next turn?
3. Can the current Pokemon survive the active punish long enough for the support
   action to matter?
4. If the opponent resets with a new receiver, which coverage move punishes both
   stay and switch branches?
5. Is the support action changing a route, or just delaying an inevitable loss?

## Next Transfer Check

Run a fresh no-keyword-screen replay with
`policy_cards/branch_action_after_naming.md` loaded. Before every likely switch
or support branch, include support/setup moves in the candidate branch-beating
actions, not only attacks and switches.
