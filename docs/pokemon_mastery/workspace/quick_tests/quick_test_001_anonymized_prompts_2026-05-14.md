# Quick Test 001 Anonymized Prompt Rewrite - 2026-05-14

Purpose: preserve a less-leading version of the Quick Test 001 prompts. This is
not a new scored run and should not replace the original scored artifact. It is
a prompt-design correction for future quick probes.

Anonymization rules used:

- Remove source IDs, atlas IDs, tags, and category labels.
- Remove lesson-wording such as "route-conversion", "status discipline", and
  "chip threshold".
- Avoid candidate names that directly state the intended policy.
- Keep enough public battle state to make the decision answerable.

## Anonymized Prompts

### Scenario 1

Public state: The opposing defensive anchor is asleep. It has previously shown
that being asleep does not necessarily stop it from acting or stabilizing. Your
active Pokemon can either spend the turn boosting, use a move that immediately
changes the board, or switch to reshape the matchup.

Candidate actions:

- boost;
- make immediate board progress;
- switch.

### Scenario 2

Public state: Your attacker expects a durable physical wall to enter. You can
choose maximum immediate damage, a weaker move with a useful secondary effect,
or an aggressive switch to the teammate that benefits most if the wall is
weakened or slowed.

Candidate actions:

- strongest attack;
- secondary-effect attack;
- aggressive switch to the beneficiary.

### Scenario 3

Public state: You have a free-looking status turn, but the opponent has an
obvious bulky status absorber that commonly enters these spots. Your choices
are to click the status move anyway, use a move that also affects the absorber,
or switch to a teammate that punishes the absorber.

Candidate actions:

- direct status;
- absorber-pressure move;
- switch to absorber punisher.

### Scenario 4

Public state: Two support Pokemon can both be configured to punish the same
class of switch-in. One plan repeats the same poison effect from both slots.
Another plan splits the jobs so one slot poisons and the other forces movement.
A third plan drops one support move for coverage.

Candidate actions:

- duplicate poison support;
- split poison and forced-movement support;
- run coverage on one slot.

### Scenario 5

Public state: Your team-status cure user is available. Some current status can
be removed now, but the opponent still has a live way to put a high-value target
to sleep. The cure user is important to the team's long-game recovery plan.

Candidate actions:

- use the team cure now;
- keep the cure user protected;
- tolerate the current status allocation;
- spend another Pokemon to absorb sleep.

### Scenario 6

Public state: One of your Pokemon is asleep. That Pokemon does not currently
matter much against the opponent's remaining structure. Your team-status cure
is still available and may matter later.

Candidate actions:

- cure immediately;
- hold the cure;
- wait to cure after more status has accumulated.

### Scenario 7

Public state: Your hazard setter has successfully drawn in the opposing remover.
Your broader offense needs that remover gone before the residual plan can
matter. The setter can keep attacking, pivot to a trapping/punish line, or spend
its one-time trade move now.

Candidate actions:

- keep attacking;
- pivot to the punisher;
- use the one-time trade.

### Scenario 8

Public state: Your current Pokemon threatens a sleep move. The opponent is
likely to answer with a sleep absorber that is also a major defensive obstacle.
You can attack directly, click sleep, spend a one-time trade immediately, or
use the sleep threat to create the absorber entry and then punish it.

Candidate actions:

- direct attack;
- sleep move;
- immediate one-time trade;
- force absorber, then punish.

### Scenario 9

Public state: Your one-time trade move can hit a bulky opposing pivot, but it is
unclear whether the trade actually removes that pivot. If the pivot survives,
it can recover or stabilize. You can trade now, first create more damage, first
apply a speed/status constraint, or leave the position.

Candidate actions:

- one-time trade now;
- damage first;
- status first;
- pivot out.

### Scenario 10

Public state: An opposing boosted sweeper is one turn from becoming decisive.
Your current Pokemon has a one-time trade available. The alternatives are a
normal attack that may only bluff pressure or a defensive answer that is not
clearly stable.

Candidate actions:

- attack or bluff pressure;
- go to the shaky answer;
- use the one-time trade.

## Future Probe Requirement

Future quick tests should use this style by default:

- no tags;
- no source IDs;
- no "this is the lesson" phrasing;
- public state only;
- candidate actions that are real choices, not policy labels;
- oracle kept sealed until after answers are written.
