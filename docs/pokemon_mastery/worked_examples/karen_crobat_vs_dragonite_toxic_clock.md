# Worked Example: Karen Crobat vs Dragonite

Source card:
`tools/boss_ai_preference/benchmarks/state_transition_public_cards.json`
`fixture_karen_crobat_vs_dragonite_toxic_clock_001`

Mechanics profile: `romhack_gym_leader_lab`

Purpose: practice status as a concrete route clock, not generic disruption.

## Public State

Karen:

- Active: Crobat level 45, 92%, no status, Leftovers.
- Moves: Confuse Ray, Wing Attack, Toxic.
- Role: fast status pivot that can start a clock before preserving.
- Bench: Gengar, Donphan, Murkrow, Tyranitar, Houndoom.

Player:

- Active: Dragonite level 48, 100%, no status.
- Revealed move: Outrage.
- Plausible hidden moves: Hyper Beam, Thunder, Blizzard.
- Role: locked-damage threat that punishes repeated Crobat turns.

Damage evidence:

- Wing Attack into Dragonite: 12-14%, never decisive.
- Dragonite Outrage into Crobat: 63-74%, Crobat survives from 92%.
- Dragonite Outrage into Tyranitar: 55-65%, Tyranitar survives.
- Future Tyranitar Rock Slide into Dragonite: 39-46%, not an immediate KO.

## Live Advice

Recommendation:

- Use Toxic.

Plan:

- Start a real clock on Dragonite while Crobat can survive the public Outrage
  branch, then re-score into Tyranitar as the anti-Dragon follow-up.

Why this move:

- Wing Attack is only light chip into full-HP Dragonite, and Confuse Ray is
  swingier. Toxic changes the long-term route by making every Outrage, pivot,
  and follow-up turn worse for Dragonite.

Opponent's best route:

- Keep Dragonite unstatused and use Outrage or revealed coverage to remove
  Crobat before Karen establishes clock plus pivot pressure.

Worst plausible branch:

- Crobat lands Toxic but stays in too long afterward; repeated Outrage or
  hidden coverage removes the status pivot before Karen uses Tyranitar.

Key piece:

- Crobat is the current status pivot, but Tyranitar is the visible anti-Dragon
  follow-up. Crobat's job is to start the clock, not solo Dragonite.

What changes the answer:

- If Crobat no longer survives Outrage, switch Tyranitar first.
- If Dragonite is already statused, Toxic loses value.
- If Wing Attack reaches a decisive KO threshold, attack.
- If hidden coverage makes Tyranitar a bad pivot, re-score after Toxic or pivot
  through a different answer.
- If Toxic misses, separate outcome from decision quality and re-score the
  current HP / Outrage-lock state.

Next turn if it works:

- Re-score preservation. Usually pivot Tyranitar if the Dragonite route remains
  live and Crobat risks being removed by another hit or coverage reveal.

## Oracle Check

The hidden oracle labels Toxic as best and Tyranitar as acceptable. Wing Attack
and Confuse Ray are catastrophic in this public state because they fail to
create a reliable clock or route while Dragonite keeps applying pressure.

This example supports the status-clock recipe: status is correct when it changes
the future route and the user survives the immediate punish. It is not a reason
to stay in forever.
