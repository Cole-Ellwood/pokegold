# External Research Prompts - 2026-05-14

Status: handoff prompts for GPT-5.5 Pro or Deep Research.

Use these only for external help that is likely to improve live Pokemon move
choice or boss AI quality faster than local study. The default answer is still
no: do not spend an expensive external run on generic strategy, local source
facts, exact boss rosters, or anything that would contaminate held-out tests.

## Project Context To Include

We are improving a Pokemon Gold romhack / Gym Leader Lab battle advisor and boss
AI. The setting is Gen 2 based and has no public Team Preview. The advisor may
know source-visible boss trainer data before planned boss fights, but the boss
AI must not know the player's unrevealed team, moves, items, private stats, or
current-turn input except for explicitly quarantined Haki/oracle branches.

Core goal:

```text
Improve practical Pokemon singles move choice under hidden information. The
output should help choose a move in a real turn, update a plan as information is
revealed, and avoid importing modern mechanics into a Gen 2 based romhack.
```

Local constraints:

- No public Team Preview in vanilla GSC or this romhack.
- Boss AI must be public-information-only outside explicit Haki exceptions.
- Vanilla GSC strategy is useful source material, not romhack truth.
- Romhack mechanics must be labeled as locally supplied, runtime verified,
  contradicted, or unknown.
- Do not answer local benchmark fixtures or current Gym Leader Lab holdouts.
- Do not produce broad strategy prose unless it is converted into testable turn
  policy.

Known romhack differences that matter:

- Spikes has three layers in the romhack: 1/8, 1/6, and 1/4 max HP on grounded
  switch-in.
- Rapid Spin clears all Spikes layers.
- Flying-type Pokemon ignore Spikes. There is no Levitate-style ability check.
- Many type/passive changes exist locally, so type and passive claims need local
  verification before being used as romhack fact.

Useful source starting points:

- Smogon G/S resources: https://www.smogon.com/resources/competitive/gs
- GSC Spikes: https://www.smogon.com/gs/articles/gsc_spikes
- GSC Explosion: https://www.smogon.com/gs/articles/guide_to_explosion
- GSC Status: https://www.smogon.com/resources/competitive/gs/status
- Introduction to Competitive GSC:
  https://www.smogon.com/smog/issue28/gsc
- GSC OU statistics and replay resource:
  https://www.smogon.com/forums/threads/your-one-stop-shop-for-gsc-ou-statistics.3780415/
- Pokemon Showdown: https://github.com/smogon/pokemon-showdown

## Run Now 1: GSC Hidden-Information Turn Atlas

Recommended target: Deep Research.

Use this prompt:

```text
You are helping improve a Pokemon battle advisor for a Gen 2 based Pokemon Gold
romhack. Your task is to produce source-grounded training material for no-Team-
Preview singles decision-making.

Important constraints:
- Vanilla GSC and this romhack do not have public Team Preview.
- Treat vanilla GSC strategy as source material, not romhack truth.
- Do not use later-generation Team Preview mechanics, abilities, items, Defog,
  Stealth Rock, Terastallization, Mega Evolution, Z-Moves, Dynamax, or modern
  hazard assumptions except as explicitly labeled non-transferable analogies.
- Do not answer local Gym Leader Lab benchmark fixtures.
- Do not put future-turn spoilers inside public prompts.
- Reconstruct each public state only from information available before the
  decision turn.

Produce a Markdown report and a JSONL block containing 40 expert-play turn
positions from high-quality GSC / Gen 2 singles sources and replays. The
positions should test hidden-information move choice, lead turns, long-term
preservation, Spikes and Rapid Spin, spinblocking, sleep/status, Rest cycles,
Explosion or sacrifice timing, phazing, setup denial, PP, and endgame
conversion.

Coverage requirements:
- At least 8 hazard, Rapid Spin, or spinblock cases.
- At least 8 sleep or status discipline cases.
- At least 6 Explosion, Selfdestruct, or sacrifice-route cases.
- At least 6 preservation, pivot, or defensive-answer identity cases.
- At least 6 setup, phazing, or anti-setup cases.
- At least 6 endgame, Rest cycle, or PP cases.
- A single turn may satisfy multiple categories, but the final set should be
  diverse.

For each position, include:
- source_url
- source_type: article, replay, forum analysis, tournament log, or other
- battle_format
- turn_number if from a replay
- category_tags
- public_state: only facts known before choosing the move
- sealed_hidden_state: facts known from full replay or source but not visible
  to the player at that turn
- candidate_moves_or_switches
- expert_move_or_recommended_line
- why_this_move
- worst_plausible_branch
- irreplaceable_piece_or_resource
- information_that_would_flip_the_answer
- transfer_to_romhack: role/resource lesson only
- do_not_transfer: mechanics or assumptions that should not be imported
- mechanics_status: vanilla_gsc, locally_supplied_romhack_evidence_needed,
  nontransferable_modern, or unknown
- policy_trigger: one sentence in the form "When [trigger], prefer [policy],
  unless [exception]."
- measurement_hook: what a future quiz/test should check

Quality bar:
- Prefer expert replay decisions and high-quality GSC sources over generic
  advice.
- Every lesson must change a move choice, not merely describe Pokemon strategy.
- Call out uncertainty. If the source does not justify a recommendation, mark
  it uncertain instead of inventing authority.
- Avoid Snorlax-only framing unless the lesson is abstracted into anchor,
  defensive glue, Rest cycle, wallbreaker, or route-converter language.
- Cite sources for every entry.

Return format:
1. Brief methodology and source list.
2. Markdown table or sections for all 40 positions.
3. A fenced jsonl block with the same 40 entries.
4. A final section named "Transfer Rules For A GSC-Based Romhack" with 10-15
   concise policies and their non-transferable assumptions.
```

What this fills locally:

- More expert no-preview turn decisions without relying on local boss cards.
- More hidden-information reps for branch pricing and resource identity.
- More replay-grounded examples of Spikes, Rapid Spin, Explosion, Rest, status,
  PP, and preservation.

## Run Now 2: Cheap No-Cheat Boss AI Intelligence Wins

Recommended target: GPT-5.5 Pro.

Use this prompt:

```text
You are helping improve a Pokemon Gold / Gen 2 romhack boss AI. The goal is to
find high-value, low-coding-time intelligence improvements under strict
public-information-only constraints.

Default answer should be no. Only propose a change if it is likely to create a
large player-visible intelligence gain with little implementation risk.

Game and information model:
- No public Team Preview.
- Boss AI does not know the player's unrevealed team, hidden moves, held items,
  private stats, hidden reserve HP, or current-turn input.
- Boss AI may use public active species, level, visible typing if known by game
  rules, visible HP bands/status/boosts, revealed player moves, observed switch
  history, seen player species, public faint/send-out events, legal learnset
  priors, and public battle state.
- Boss AI may use its own full team and moves because those are its authored
  resources.
- Broad current-turn input reading is forbidden except for explicitly
  quarantined Haki/oracle branches that are one-use, traceable, and not part of
  ordinary boss policy.

Existing local boss AI capabilities to assume:
- Boss move scoring already considers KO pressure, deny-KO pressure, tempo,
  setup windows, status value, role bias, and risk.
- It has public plausible-threat masks from active species, level, revealed
  damaging move types, STAB, legal level-up/TM/HM/egg coverage, and Hidden Power
  risk.
- It distinguishes higher-confidence likely threats from possible-only threats.
- It tracks seen player species and visible faint/send-out events.
- It tracks revealed player moves by active species.
- It has public switch prediction from observed switching and active matchup
  pressure.
- It has switch-loop controls and public Perish Song escape.
- It has revealed-move memory policies for Protect/Detect, recovery, Encore,
  Destiny Bond, Counter/Mirror Coat, Haze/phazing, Explosion/Selfdestruct, and
  some utility fail gates.
- It has layer-aware Spikes policy for the romhack's three-layer Spikes.
- It has an approved exact-speed exception only for setup-speed headroom; do
  not generalize exact private stat helpers.
- Runtime memory is constrained. Assume only a few bytes are cheap. Prefer
  behavior that can be implemented with small counters, bitmasks, score biases,
  or existing state.

Task:
Produce a ranked list of 15 proposed boss AI improvements that are cheap,
public-information-only, and likely to make bosses look much smarter. Also
produce 5 anti-proposals that look smart but should be rejected because they are
cheating, brittle, overfit, too expensive, or not testable.

Each proposal must include:
- rank
- proposal name
- intelligence benefit
- public_info_used
- forbidden_info_not_used
- implementation_shape: score bias, gate, counter, bitmask, trace-only audit,
  table, or other
- memory_cost_estimate: 0 bytes, 1 byte, 2-3 bytes, or more
- code_complexity_estimate: tiny, small, medium, or large
- expected_player_visible_effect
- bosses_or_roles_affected
- failure_mode
- no_cheat_risk
- trace_fields_needed
- audit_test_or_fixture
- why this is better than doing nothing
- reject_if: concrete reason to decline implementation

Must address these areas if and only if they produce cheap wins:
- no-Team-Preview uncertainty and Bayesian priors over hidden coverage
- revealed move memory
- hidden moveset priors from public species and level
- near-tie randomization so bosses do not become deterministic scripts
- pattern punishment from observed repeated player switches or protects
- role/value preservation for the boss's own irreplaceable pieces
- hazard retention and Rapid Spin pressure without assuming a hidden spinner
- public speed-order and priority risk without private stat peeking
- anti-loop behavior that avoids dumb switching without forbidding emergency
  escapes
- calibration: when the AI should scout or choose robust progress instead of
  hard-countering a possible-only threat

Hard rejection rules:
- Reject any proposal that reads current-turn player input outside Haki.
- Reject any proposal that reads hidden player party slots, hidden moves, hidden
  items, hidden PP, hidden exact stats, or hidden reserve HP.
- Reject any proposal that requires broad game-tree search or large new memory.
- Reject any proposal that imports modern Team Preview behavior.
- Reject any proposal that cannot be traced or tested.

Return format:
1. Executive summary: the 3 best proposals and why they clear the default-no
   bar.
2. Ranked table of 15 proposals.
3. Five anti-proposals.
4. "Implementation First Picks": the 3 smallest changes you would inspect or
   code first, with exact test ideas.
5. "Questions For Local Source": facts that must be checked in the ROM before
   coding.
```

What this fills locally:

- Independent pressure test of whether there are still obvious cheap boss AI
  wins.
- Candidate improvements phrased in implementation and audit terms.
- Explicit rejection list for tempting but unfair or brittle ideas.

## Do Not Run Now

Do not run a broad "teach me Pokemon" prompt. The local notebook already has too
much structure; the bottleneck is turn judgment and measurement.

Do not ask an external model to answer current local Gym Leader Lab benchmark
fixtures. That contaminates the evaluation set.

Do not run a sealed final exam generator if the complete answer key will be
returned to the studying assistant. That is useful only if the public prompts
and private answer key can be kept separated until after testing.

Do not ask for exact romhack mechanics, trainer rosters, type chart facts, or
damage values unless you supply the local source evidence and ask for an audit
of consistency. Local source, debugger fixtures, and emulator traces are the
authority for those facts.

## Optional Second Wave

Run these only after the two main prompts return and create a concrete gap.

### Moveset-Prior Compression

Ask for an ASM-friendly, public-information-only way to bucket likely hidden
move threats from species, level, STAB, legal learnability, role, recovery,
setup, priority, phazing, hazards, status, and Explosion. Require probability
buckets, not exact usage claims. Require a "romhack firewall" section that says
what must be regenerated from local data.

### Holdout-Safe Measurement Review

Ask for an adversarial review of the existing measurement mini-goal, focused on
leakage, overfitting, weak baselines, false simulator confidence, and how to
keep final exams sealed. Do not ask it to write the actual final exam unless
the answer key can stay hidden.
