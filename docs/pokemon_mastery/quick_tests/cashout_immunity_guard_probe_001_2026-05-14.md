# Cash-Out Immunity Guard Probe 001 - 2026-05-14

Source parent:
`quick_tests/branch_absorber_transfer_001_smogtours-gen2ou-912287_2026-05-14.md`.

Mode: constructed nonblind policy regression. This is not fresh replay proof.
It isolates the severe turn-13 miss where Explosion was made top without
pricing an opposing Gengar switch in no-Team-Preview GSC.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/quick_tests/branch_absorber_transfer_001_smogtours-gen2ou-912287_2026-05-14.md`

## Score Summary

Scenarios: 4.

Immunity-owner naming hits: 4 / 4.

Cash-out ranking hits: 4 / 4.

Hidden-information discipline hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Follow with a fresh replay transfer before
treating this guard as stable.

## Scenario 1 - Revealed Ghost Blocks The Trade

Public state:

```text
Vanilla GSC spectator-public state. Your low Cloyster faces Snorlax. Explosion
is revealed. Opposing Gengar is revealed in the back and can enter. Snorlax is
valuable, but Cloyster also still has Surf or Toxic as non-all-in pressure.
```

Tempting move:
Explosion because Snorlax is the visible route piece.

Frozen top-three:

1. Surf, Toxic, or switch to a Snorlax owner if the revealed Gengar switch is
   the best-priced branch.
2. Explosion only as a read if slow play loses and the answer states "I lose
   to Gengar switch."
3. Preserve Cloyster if its future Spikes or trade job still matters.

Answer:
Do not make Explosion the default. Confidence: high. The revealed Ghost is a
named owner of the worst branch, so the move that improves through that branch
must be ranked first.

Score: pass.

## Scenario 2 - Hidden Ghost In No-Team-Preview

Public state:

```text
Vanilla GSC spectator-public state. Your Gengar is low and faces a sleeping
RestTalk Snorlax. Snorlax has revealed Sleep Talk and Earthquake. The opponent
has unrevealed team slots. No Ghost has been shown yet.
```

Tempting move:
Explosion because Gengar may die to another Sleep Talk Earthquake.

Frozen top-three:

1. Non-all-in pressure such as Dynamic Punch, Thunder, coverage, or a handoff
   if it preserves Gengar's remaining route value.
2. Explosion only if explicitly marked as a high-risk read that loses to a
   hidden Ghost switch.
3. Switch if the next-board owner safely handles both Sleep Talk and a Ghost
   pivot.

Answer:
Do not make Explosion hard top. Confidence: medium. In no-Team-Preview, a
hidden Ghost is not known, but Explosion still depends on the unrevealed fact
that no Ghost will enter. That needs a fallback before it can be top.

Score: pass.

## Scenario 3 - High-Risk Cash-Out Is Allowed When Slow Play Loses

Public state:

```text
Vanilla GSC spectator-public state. Your low Exeggutor faces the active last
healthy Snorlax route converter. The opponent's Ghost is already revealed
fainted, or all remaining Pokemon are revealed and none are immune to
Explosion. If Snorlax lives this turn, it wins the endgame.
```

Tempting move:
Switch to preserve Exeggutor because Explosion is all-in.

Frozen top-three:

1. Explosion to remove the converter and open the named endgame.
2. Status or damage only if it prevents the same Snorlax route.
3. Switch only if the incoming owner wins after Snorlax acts.

Answer:
Use Explosion. Confidence: high. The immunity owner has been checked and is
not live, and slow play loses to the converter.

Score: pass.

## Scenario 4 - Revealed Immunity Makes Setup Or Phaze Better

Public state:

```text
Vanilla GSC spectator-public state. Your Steelix at 75% faces Zapdos with
Spikes on the opponent's side. Steelix has Earthquake, Roar, and Explosion
revealed. Opposing Gengar is revealed healthy. Zapdos's Hidden Power damages
Steelix, but Roar has been converting through Spikes.
```

Tempting move:
Explosion because Zapdos is active and damaging Steelix.

Frozen top-three:

1. Roar if the hazard-phaze loop still improves the route and covers the
   revealed Gengar switch better than Explosion.
2. Earthquake only if the expected branch is Tyranitar or Steelix, not Zapdos.
3. Explosion only if Zapdos is the converter and the revealed Gengar switch is
   not credible or is explicitly accepted as the losing branch.

Answer:
Roar. Confidence: medium-high. The route converter is the phaze loop, and the
revealed Ghost makes all-in Explosion worse unless the game is already forcing
that read.

Score: pass.

## Resulting Checklist

Before making Explosion, Self-Destruct, Destiny Bond, or a sacrifice the top
line:

1. Name the active target's route job.
2. Name revealed immunity or absorber owners.
3. Name plausible hidden immunity classes in no-Team-Preview.
4. State whether the all-in move spends an irreplaceable route piece.
5. If the worst immunity branch is live, choose pressure, setup, phaze,
   coverage, or handoff unless the line is explicitly marked as a high-risk
   read and slow play loses.

Next transfer:
Fresh replay transfer focused on cash-out immunity obedience. Score whether
all-in trades become top only after immunity owners and fallback lines are
named.
