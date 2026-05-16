# Spikes Spin Branch Probe 001 - 2026-05-15

Status: constructed/nonblind regression drill. This does not count as fresh
progress proof.

Parent packet:
`workspace/quick_tests/post_curseboom_repair_transfer_002_smogtours-gen2ou-931584_2026-05-15.md`

Source:
- Smogon GSC Spikes article: the Spikes game revolves around Cloyster,
  Forretress, Starmie, and spinblockers Gengar/Misdreavus; keeping or removing
  Spikes depends on the support and denial map, not just clicking Spin.

Rule being drilled:

```text
Before Rapid Spin, name the spinblocker, pressure owner, or Explosion branch.
Rank Spin only if it converts before that denial branch takes over.
```

## Score

Policy hits: 5/5.

Severe blunders: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

## Prompts And Expected Answers

### 1. Forretress Faces Cloyster Before Either Side Has Spikes

Expected answer: if Cloyster likely uses Spikes, Rapid Spin is a branch punish,
but Spikes or Toxic can be better if the opponent can immediately bring in
Gengar/Zapdos after the Spin turn. Name both the immediate Spikes branch and
the next-owner denial branch.

### 2. Both Sides Have Spikes And Cloyster Can Switch

Expected answer: Rapid Spin is not automatic. Ask whether Cloyster stays,
switches to Gengar/Misdreavus, or goes to Zapdos/Moltres pressure. If the
switch branch is likely, Toxic, Explosion, or owner handoff may be the top
converter.

### 3. Gengar Enters Forretress

Expected answer: classify Gengar as spinblocker plus pressure owner. Forretress
should not click Spin into immunity. Toxic, switch to Pursuit/Dark owner, or
Explosion only if immunity and post-trade owner are priced.

### 4. Low Forretress Faces Cloyster With Spikes Up

Expected answer: if Forretress dies before the loop stabilizes, rank the move
that creates value now: Spin if it clears before death and no blocker enters,
Toxic/Explosion if the blocker or pressure owner is likely, or handoff if a
teammate owns the next board.

### 5. Sleeping Snorlax Gives Cloyster A Free Turn

Expected answer: first classify Snorlax as reset/sleeper and Cloyster as
hazard/reset/cash-out. Switching to Forretress can be correct, but the next
move must still solve Surf, Explosion, Spin, and spinblock branches rather than
assuming a stable spinner mirror.

## Next Fresh Check

Restart fresh replay sampling only with this fail-fast condition:

```text
two blind Rapid Spin rankings without naming spinblock / pressure / Explosion
```
