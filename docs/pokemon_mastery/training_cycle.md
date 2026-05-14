# Training Cycle

Status: active operating plan for the current Pokemon mastery goal.

The next study blocks should be judged by one question: did this make the next
live move recommendation better?

## Current Blind Spots

- Decision compression: choosing one ranked move from a messy board without
  hiding behind commentary.
- Resource identity: knowing which HP, PP, status, hazard, sleep, and role
  resources are actually winning material in this state.
- Branch pricing: weighing the likely opponent action against the worst
  plausible punish.
- Format transfer: separating general Pokemon principles, vanilla GSC
  mechanics, and Gym Leader Lab mechanics.
- Autonomy underuse: staying inside known Pokemon notes when an outside
  imperfect-information or planning framework could attack the repeated error
  more directly.

## Next 20-Hour Shape

| Time | Work | Artifact |
| --- | --- | --- |
| 6h | Study expert sources and unseen tournament replays. | `source_to_policy_ledger.md` entries. |
| 5h | Pause unseen GSC replays turn by turn before reading outcomes. | scored turn-pause run plus `paused_turn_atlas.md` decision points. |
| 3h | Run live-turn drills from constructed and reviewed positions. | `worked_examples/live_turn_drills.md`. |
| 2h | Make boss route cards from local rosters. | `boss_route_maps/` one-page plans. |
| 2h | Check mechanics and breakpoint claims. | fixtures, calculators, or audit notes. |
| 1h | Take a high-variance transfer tangent when a repeated error needs it. | `cross_domain_autonomy_policy.md` artifact: STP, drill, fixture, helper, or reject note. |
| 1h | Maintain the cookbook only where a lesson has become reusable. | small cookbook edits. |

This is a work allocation, not a rigid timer. If a battle review or source
thread is producing strong move-choice lessons, keep reading.

## Replay Turn-Pause Default

When there is no urgent romhack fixture or boss capture, use
`replay_turn_pause_protocol.md`:

- choose an unseen Smogon GSC tournament replay;
- reveal only the current public state;
- predict both players' best move or switch before revealing the turn;
- compare against the actual strong-player choices;
- score agreement and error classes separately from sealed quick tests.

This produces more useful reps than broad note expansion because every turn
forces a concrete recommendation.

## Source-To-Policy Rule

Every expert-source lesson should be compressed into:

- trigger;
- default move class or planning action;
- exceptions;
- worst plausible branch;
- local mechanics status;
- one drill or boss application.

Avoid entries that only say a tactic is good. The entry must help choose a move.

## Stop, Reduce, Quarantine

Stop expanding broad prose when the next step could be a drill, reviewed turn,
or boss route card.

Reduce tooling work unless it catches a real mechanics error, checks a real
damage threshold, or evaluates a real decision policy.

Quarantine romhack conclusions when they depend on unverified type-chart,
passive, hazard, move, item, AI, or damage behavior.

Do not quarantine useful autonomy. If a repeated failure suggests poker AI,
POMDPs, search, chess endgames, fighting-game yomi, or decision theory, take a
small transfer sprint. Keep it only if it produces a Pokemon decision artifact
or a clear reject note.

Before starting a tedious manual study step, do one helper check: would a small
script remove answer leakage, repeated formatting, score bookkeeping, search
friction, or mechanics uncertainty? If yes, build the smallest useful helper.
If no, keep studying.

## Live-Turn Standard

For a serious turn, the advice must include:

- recommended move and confidence;
- one-sentence route reason;
- state read;
- current win condition;
- ranked serious candidates;
- next turn if the move works;
- missing information that would change the answer.

If the recommendation cannot name a route or an answer-changing fact, the
thinking is not finished.
