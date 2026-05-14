# Cross-Domain Autonomy Policy - 2026-05-14

Purpose: make full autonomy useful rather than ornamental. I should pursue
high-variance study, helper programs, and adjacent-domain research when they
can plausibly improve no-Team-Preview Pokemon decisions.

## Core Rule

The default curriculum remains expert Pokemon play and local romhack
verification, but I should deliberately spend some study blocks on adjacent
fields when the current Pokemon reps expose a matching weakness.

Default answer for tooling is still no. The point is not to build systems by
habit; the point is to notice when a small program would remove friction,
contamination, or repeated manual work from the core study loop.

Good autonomy is not "write more notes." Good autonomy is:

- find a useful outside source;
- extract one decision principle;
- translate it into Pokemon terms;
- test it with a replay turn, drill, fixture, or boss-AI audit;
- keep it only if it improves a real move choice or error class.

## Helper Program Check

Occasionally ask:

```text
Is something annoying, repetitive, or contamination-prone enough that a small
helper would create more or cleaner Pokemon reps?
```

Build a helper only when at least one answer is yes:

- it prevents seeing answers before prediction;
- it makes replay/drill reps faster without hiding the decision work;
- it catches mechanics, damage, speed, state, or legality mistakes;
- it generates or audits measurement rows more reliably;
- it makes boss-AI public-information checks easier to verify;
- it replaces repeated manual formatting or searching that is slowing actual
  study.

Do not build a helper when:

- the next obvious action is to answer more turns;
- the tool would need broad speculative design before producing one useful
  artifact;
- it would make the task feel productive without improving move choice;
- it duplicates a local script that already works well enough.

## When To Take A Tangent

Take a tangent when any of these are true:

- the same replay or quick-test error appears twice;
- the next Pokemon-only action would be another generic note pass;
- a known AI/game-theory tool directly matches the failure mode;
- a helper program would reduce contamination, reveal a hidden error, or make
  measurement cheaper;
- a boss-AI cheap win needs a policy idea from imperfect-information play,
  search, planning, game theory, or adversarial evaluation.

## Useful Tangent Domains

| Domain | Pokemon Skill It Can Train |
| --- | --- |
| Poker AI and game theory | Hidden-information discipline, bluff/call structure, mixed strategy, exploitability, subgame re-solving. |
| Chess / Go / shogi endgames | Conversion, tempo, zugzwang-like forced sequences, sacrifice timing. |
| RTS / fighting-game yomi | Conditioning, baiting, option coverage, opponent habit inference. |
| POMDP / belief-state planning | No-Team-Preview uncertainty, posterior updates after reveals. |
| Search and planning algorithms | Candidate pruning, depth-limited branch evaluation, horizon effects. |
| Sports analytics / decision theory | Risk calibration, expected value, timeout/resource management. |
| Human expert commentary | Compact reasoning, heuristics that survive real pressure. |

## Poker AI Transfer Seed

Poker is especially relevant because it is an imperfect-information game with
hidden private state, asymmetric information, deception, and exploitability.
The useful transfer is not "Pokemon is poker." The useful transfer is how to
make decisions when exact opponent resources are unknown.

Initial sources to study:

- DeepStack paper: recursive reasoning, decision-focused decomposition, and
  learned intuition for imperfect information.
  `https://arxiv.org/abs/1701.01724`
- Libratus subgame-solving paper: subgames cannot be solved in isolation from
  the whole strategy; re-solving can improve play as the game progresses.
  `https://arxiv.org/abs/1705.02955`
- Depth-limited imperfect-information solving: at a search cutoff, allow the
  opponent multiple continuation strategies so the chosen line is robust.
  `https://arxiv.org/abs/1805.08195`
- Pluribus / CMU report: strong multiplayer poker AI used mixed strategies and
  found nonstandard lines that strong humans recognized as strategically
  meaningful.
  `https://www.cmu.edu/news/stories/archives/2019/july/cmu-facebook-ai-beats-poker-pros.html`

Pokemon translation targets:

- Treat unrevealed moves and teams as belief states, not certainties.
- Re-solve after every reveal, KO, Rest, Spin, Explosion, phaze, or item clue.
- At a depth limit, judge a line against several plausible opponent
  continuations instead of only the line I hope for.
- Prefer lines with low exploitability when ahead or stable; accept sharper
  exploitative reads only when the slow route is losing.
- For boss AI, use controlled public-information randomness only when it
  prevents repeated exploitation without cheating.

## Artifact Requirement

Every cross-domain tangent must produce one of:

- a source-to-policy entry with a Pokemon transfer section;
- a paused-turn drill built from the transfer;
- a quick-test canary for the related failure mode;
- a helper program or fixture that makes measurement safer;
- a boss-AI proposal with public-information legality notes;
- a short reject note explaining why the tangent did not transfer.

## Incentives

- If two consecutive Pokemon-only blocks produce no new measured error or
  replay score, force one high-variance tangent before the next broad note
  pass.
- If a replay exposes a repeated error class, search outside Pokemon for one
  analogous decision framework before writing another recipe.
- Prefer small experiments over long surveys: one paper, one replay segment,
  one drill, one score.
- A weird tangent is successful if it changes one future move choice, improves
  one score row, or prevents one illegal hidden-information assumption.

## Transfer Firewall

Reject or quarantine a tangent when:

- it imports mechanics that do not exist in GSC or the romhack;
- it encourages reading hidden player data for ordinary boss AI;
- it produces only vocabulary, not a decision rule;
- it cannot be tested on a replay, drill, fixture, or boss-AI trace;
- it competes with obvious Pokemon reps that are already producing measured
  errors.
