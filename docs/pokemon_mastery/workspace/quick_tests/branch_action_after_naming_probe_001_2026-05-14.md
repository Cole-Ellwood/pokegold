# Branch Action After Naming Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/replay_turn_pause_062_active_damage_branch_action_smogtours-gen2ou-911268_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks the replay 062
branch-action failure. It is not fresh replay-transfer evidence.

## Score Summary

Scenarios: 4.

Action policy hits: 4 / 4.

Classification hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

## Scenario 1 - Counter-Switch Beats One More Hit

Prompt:

Vanilla GSC spectator-public state. Your Suicune is active at 96% against an
opposing Forretress at 66%. Spikes are on your side. Surf would damage
Forretress, but you believe the opponent's best branch is switching Snorlax in
to preserve Forretress. You have Golem available and it can immediately
pressure Snorlax or remove Spikes.

Question: Surf again or counter-switch?

Frozen answer:

Counter-switch if the Snorlax branch is the best branch and Golem's entry
changes the next board more than another Surf does. Surf is correct only if
the next hit meaningfully ruins Forretress's future job or if the Snorlax
switch is too uncertain to act on.

Answer key:

Hit. Replay 062 punished naming the Snorlax switch and still taking the active
hit. The correct line was Golem into Snorlax.

## Scenario 2 - One-Turn Utility Before Damage

Prompt:

Vanilla GSC spectator-public state. Your Golem is active at 94% against an
opposing Snorlax at 94%. Spikes are on your side. Golem has Rapid Spin. Snorlax
has not revealed its full set, but Earthquake or Double-Edge can damage Golem.
Golem can also Earthquake Snorlax.

Question: Earthquake or Rapid Spin?

Frozen answer:

Use Rapid Spin if removing Spikes is Golem's one-turn job and Golem may not get
another clean chance. Earthquake is only better if the damage changes a
critical Snorlax route more than clearing the hazard map.

Answer key:

Hit. Replay 062 showed Golem using Rapid Spin before taking Snorlax's
Earthquake. The utility job mattered more than immediate damage.

## Scenario 3 - Hard Answer Over Status

Prompt:

Vanilla GSC spectator-public state. Your Suicune is active at 72% against an
opposing Snorlax at 77% with Spikes on the opponent's side. Snorlax has shown
Earthquake and is applying active physical pressure. Suicune has Toxic, but
you also have Skarmory available as a hard answer.

Question: Toxic or switch Skarmory?

Frozen answer:

Switch Skarmory by default. Toxic is attractive only if it safely forces a Rest
clock without letting Snorlax keep converting damage. When the active attacker
is already pressuring the status user and a hard answer is available, take the
hard answer first.

Answer key:

Hit. Replay 062 used Skarmory, not Toxic. This is the active-pressure boundary
against status over-script.

## Scenario 4 - Keep Attacking When The Hit Changes The Job

Prompt:

Vanilla GSC spectator-public state. Your Suicune is active at 96% against an
opposing Forretress at 100%. Forretress has not yet set Spikes. Surf does
around 40%, and no immediate counter-switch branch has been established.

Question: Surf or pivot?

Frozen answer:

Surf. The hit directly changes Forretress's future support map before it has
done its job. Pivoting is premature unless the opponent has shown a branch that
makes the damage irrelevant or unsafe.

Answer key:

Hit. Replay 062 confirmed Surf into Forretress was correct before the Snorlax
branch became clear.

## Reusable Boundary

After naming a branch, act on it only when its next-board value beats the
active move. The rule is not "always keep attacking" or "always counter-
switch"; it is compare the next hit's route value against the branch action.

## Next Transfer Check

Run a fresh no-keyword-screen replay packet on branch action after naming:
before choosing the move, write the named branch and whether the active move,
counter-switch, utility move, status, phaze, or cash-out wins that branch.
