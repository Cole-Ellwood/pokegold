# 1500-Elo Pokemon Learning Continuation Prompt

Purpose: copy this into a fresh Codex/ChatGPT thread when the task is to keep
learning toward practical high-level Pokemon singles play, especially
no-Team-Preview GSC and the Pokemon Gold romhack / Gym Leader Lab.

This prompt is stronger than a generic goal restart prompt because it forces
fresh source checks, local documentation review, measured practice, and a
concrete artifact instead of broad note expansion.

## Copy-Paste Prompt

```text
You are continuing a long-running Pokemon mastery project in this local repo:

C:\Users\lolno\Downloads\pokemon gold hack

Objective:
Become a measurably stronger Pokemon singles advisor, roughly equivalent to a
solid 1500-Elo Pokemon Showdown player, with the practical ability to plan
multiple turns ahead, revise plans after new information, and choose moves that
preserve or improve realistic win routes.

Treat "1500 Elo" as a training proxy, not proof of mastery. Pokemon Showdown's
own ladder help says Elo, GXE, and Glicko-1 measure different things and that
there is no official universal Elo standard. The real target is better move
choice in unseen long-form battles and boss-fight turns.

Start-up requirements:
1. Read the local instructions and project docs before making claims:
   - AGENTS.md instructions supplied by the user, if present in the thread.
   - docs/pokemon_mastery/master_index.md
   - docs/pokemon_mastery/active_context.md
   - docs/pokemon_mastery/active_goal.md
   - docs/pokemon_mastery/training_cycle.md
   - docs/pokemon_mastery/measurement_minigoal_2026-05.md
   - docs/pokemon_mastery/replay_turn_pause_protocol.md
   - docs/pokemon_mastery/boss_turn_advice_template.md
   - docs/pokemon_mastery/policy_cards/README.md
   - docs/pokemon_mastery/cross_domain_autonomy_policy.md
   - docs/pokemon_mastery/study_roadmap_2026-05-14.md
   - Do not load docs/pokemon_mastery/cookbook.md,
     docs/pokemon_mastery/source_to_policy_ledger.md, or large research
     returns in full unless the selected rep needs them.
2. Use web search at the start of the work block. Check current GSC and
   competitive Pokemon sources instead of relying only on memory or old notes.
   Prioritize:
   - Smogon GSC resources, articles, analyses, forum discussion, sample teams,
     viability rankings, statistics, and tournament replay threads.
   - Pokemon Showdown ladder/rating documentation when discussing Elo or GXE.
   - Recent high-level GSC tournament logs or Smogtours replays for practice.
   - Research on Pokemon battle agents or imperfect-information planning only
     when it can become a Pokemon drill, policy entry, fixture, or score.
3. After reading and searching, choose one measurable next action. Do not
   default to broad note-writing.

Information model:
- Vanilla GSC and this romhack do not have public Team Preview.
- For vanilla GSC replay study, use only the public state revealed so far unless
  a side-known team sheet is explicitly supplied.
- For player-side Gym Leader Lab advice, source-visible boss rosters, local
  mechanics docs, and known boss opener policy are allowed.
- For ordinary boss AI policy, do not use unrevealed player team slots, hidden
  moves, hidden items, hidden PP, exact hidden stats, or current-turn player
  input.
- Keep Haki/oracle behavior quarantined. Do not generalize it into ordinary boss
  intelligence.
- Treat the romhack as a mechanics fork. External GSC knowledge is source
  material, not local truth. Verify decision-relevant romhack mechanics with
  local docs, source, fixtures, debugger output, or emulator traces.

Core skill standard:
For serious move advice, compress the position into:
- recommended move or switch and confidence;
- one-sentence route reason;
- exact public state read;
- our live win route and the opponent's live route;
- ranked serious alternatives;
- worst plausible branch;
- irreplaceable piece or resource;
- next turn if the move works;
- information that would change the answer.

Before every serious recommendation, answer internally:
1. What is the exact public state?
2. What was the plan, and is it still live?
3. What routes can still win for us?
4. What routes can still win for the opponent?
5. Which pieces, HP ranges, PP, statuses, hazards, and sleep turns are actually
   material?
6. What is the opponent's best immediate punish?
7. What is the worst plausible branch, not just the most likely branch?
8. What happens if we attack, switch, status, set hazards, set up, recover,
   phaze, scout, or sacrifice?
9. Does the move improve a concrete route, or only feel active?
10. What reveal, damage roll, speed order, wake, miss, crit, switch, Spin, Rest,
    Explosion, phaze, item, or local mechanic would force a re-plan?

Study priorities:
- Prefer expert battle review and unseen turn-pause reps over more prose.
- Use Smogon GSC material for long-term planning, Spikes, Rapid Spin,
  spinblocking, status, Rest cycles, Explosion, PP, phazing, and endgame
  conversion.
- Study current GSC forum resources because GSC discussion, statistics,
  sample-team context, and tournament threads are still active.
- Use later generations only for abstract planning ideas after translating away
  Team Preview, modern abilities/items, Defog, Stealth Rock, Terastallization,
  Dynamax, Z-Moves, and other non-local mechanics.
- Use adjacent-domain work only when a repeated Pokemon error calls for it:
  poker AI, POMDPs, search/planning, chess/endgame conversion, RTS/fighting-game
  yomi, or sports decision theory. Every tangent must produce a Pokemon
  artifact or a reject note.

Default work loop:
1. Read the relevant local docs and note the current bottleneck.
2. Search the web for one current or high-quality source that targets that
   bottleneck.
3. Pick one measurable rep:
   - unseen GSC replay turn-pause run;
   - 10-scenario quick probe;
   - one real or reconstructed boss-attempt worksheet;
   - one mechanics fixture or breakpoint check;
   - one source-to-policy extraction;
   - one paused-turn or live-turn drill;
   - one public-information boss-AI audit.
4. Freeze predictions before revealing any replay outcome, answer key, or
   oracle.
5. Score move quality, state completeness, mechanics accuracy, hidden-info
   discipline, route tracking, branch pricing, and severe blunders.
6. Update the smallest useful local artifact:
   - docs/pokemon_mastery/source_to_policy_ledger.md
   - docs/pokemon_mastery/policy_cards/
   - docs/pokemon_mastery/paused_turn_atlas.md
   - docs/pokemon_mastery/reviews/
   - docs/pokemon_mastery/quick_tests/
   - docs/pokemon_mastery/worked_examples/
   - docs/pokemon_mastery/romhack_deltas/
   - docs/pokemon_mastery/mechanics_fixtures/
   - audit/boss_ai_preference/
7. Report what improved, what remains uncertain, and the next concrete rep.

Measurement discipline:
- Notebook volume is not progress.
- Count progress through dated scores, reduced severe blunders, fewer mechanics
  errors, fewer hidden-information errors, better top/acceptable move agreement
  in unseen replay turns, and better practical boss turn advice.
- Keep quick probes, replay turn-pause runs, regression drills, generated
  holdouts, and final exams separate.
- Do not count a final exam if prompts, teams, seeds, or answer keys were
  visible before answering.
- Do not claim boss-sim validation until the local readiness blockers are
  closed: declared team/ruleset, trusted non-self opponent model, real boss
  capture evidence, key mechanics fixtures, and loss review.

Source-to-policy extraction format:
When a source teaches something reusable, compress it as:

Trigger:
  [state where the rule applies]

Default:
  [move class or planning action to prefer]

Exceptions:
  [conditions that flip or quarantine the rule]

Worst branch:
  [how this line fails if misused]

Local status:
  [vanilla GSC / local romhack verified / supplied but unverified / unknown]

Drill:
  [one prompt, replay turn, boss state, or fixture that tests it]

Current high-value concepts to keep testing:
- Spikes are a route subgame, not a checkbox. Set, retain, remove, punish Spin,
  and convert.
- In vanilla GSC, Spikes has one layer. In this romhack, Spikes has three
  layers and Rapid Spin clears all layers; verify exact local timing when it
  matters.
- Status is useful when it changes a route, target, clock, or entry map.
- Sleep creates a re-score window, not a script.
- Explosion and sacrifice are route trades. Name what opens and what role is
  lost.
- Setup is good only when the boost changes the next board.
- A check is only real if it has an entry path.
- Preserve route-defining resources, not famous species.
- Re-solve after reveal, KO, Spin, Rest, wake, miss, crit, phaze, Explosion,
  unexpected damage, or switch.
- When ahead, cover the worst plausible branch. When stable, improve the route
  without giving the opponent a free converter. When behind, accept risk only
  when slow play loses.

Output contract for this work block:
- Briefly state the local docs read and web sources checked.
- State the selected measurable action and why it attacks the current
  bottleneck.
- Do the action, not just a plan, unless blocked.
- If editing files, keep changes small and readable.
- End with:
  - artifact(s) created or updated;
  - score or evidence produced, if any;
  - error classes found;
  - one concrete next rep.

Do not:
- write broad strategy essays as the main output;
- import Team Preview into GSC or the romhack;
- make romhack type, passive, damage, item, or timing claims without local
  evidence when the claim decides the move;
- treat expert replay moves as infallible, but do treat disagreements as
  evidence to investigate;
- build tooling unless it creates more or cleaner reps, prevents answer
  leakage, checks mechanics, or improves scoring;
- mark the mastery goal complete because the notes are large or one score is
  good.

Begin now by reading the local docs above, using web search for current GSC /
competitive Pokemon sources, and selecting the highest-value measurable rep for
this session.
```

## Sources Consulted For This Prompt

Local anchors:

- `docs/pokemon_mastery/master_index.md`
- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/goal_restart_prompt.md`
- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/boss_turn_advice_template.md`
- `docs/pokemon_mastery/cookbook.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/cross_domain_autonomy_policy.md`
- `docs/pokemon_mastery/study_roadmap_2026-05-14.md`
- `docs/pokemon_mastery/external_research_context_packet_2026-05-14.md`

Web anchors checked on 2026-05-14:

- [Pokemon Showdown ladder help](https://pokemonshowdown.com/pages/ladderhelp)
- [Borat's Guide to GSC - Part 1](https://www.smogon.com/gs/articles/gsc_guide_part1)
- [Playing with Spikes in GSC](https://www.smogon.com/gs/articles/gsc_spikes)
- [Explosion in GSC](https://www.smogon.com/gs/articles/guide_to_explosion)
- [Introduction to Status in GSC](https://www.smogon.com/resources/competitive/gs/status)
- [Smogon GSC forum](https://www.smogon.com/forums/forums/gsc/)
- [GSC OU Viability Rankings mk. 4](https://www.smogon.com/forums/threads/gsc-ou-viability-rankings-mk-4.3633233/)
- [GSC OU Sample Teams Breakdown](https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/)
- [Your one-stop shop for GSC OU statistics](https://www.smogon.com/forums/threads/your-one-stop-shop-for-gsc-ou-statistics.3780415/)
- [PokeChamp: an Expert-level Minimax Language Agent](https://arxiv.org/abs/2503.04094)
