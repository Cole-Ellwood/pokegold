Treat this as a mechanics firewall.

The agent is not allowed to “know” that a move is super effective, resisted, immune, or neutral. It is only allowed to emit that claim after a mechanics evaluator has produced an evidence trace for the exact environment, attacker, defender, move, and battle state.

For vanilla GSC, the evaluator can use a locked Gen 2 chart fixture. Public references agree that the Gen 2–5 chart applies to Pokémon Gold/Silver/Crystal, with 0, ½, 1, and 2 as the chart outcomes; dual-type matchups multiply the two defending-type modifiers. ([Pokémon Database][1]) For GSC move categories, pre-Gen IV damaging move category is determined by type, not by individual move, and status moves are a separate category with their own exception rules. ([Bulbapedia][2])

For the romhack, the source hierarchy should be:

`local damage debugger trace > local source code > source-extracted fixtures > local docs > notebook facts > vanilla Gen 2 chart > generic Pokémon memory`

Generic Pokémon memory has zero authority. It may suggest what to check, but it may not fill in the answer.

## 1. Turn-level checklist before any type-effectiveness claim

Before the agent says “super effective,” “resisted,” “immune,” “neutral,” “x2,” “x4,” “no effect,” or “not very effective,” it must complete this checklist.

| Step | Required check                                                                                                                              | Failure behavior                                                                                                                                                                                     |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | Bind the ruleset: `vanilla_gsc` or `gll_romhack`.                                                                                           | If unknown, say “type result unverified for this ruleset.”                                                                                                                                           |
| 2    | Resolve attacker species and current type(s) from the battle state or fixture.                                                              | Do not infer from memory.                                                                                                                                                                            |
| 3    | Resolve defender species and current type(s) from the battle state or fixture.                                                              | If hidden, transformed, custom-form, or uncertain, branch the analysis.                                                                                                                              |
| 4    | Resolve the move’s actual type, category, contact flag, status/damaging class, and special exceptions.                                      | Do not infer from move name alone. Hidden Power, Struggle, custom moves, and fork edits are danger cases.                                                                                            |
| 5    | Compute the base Gen 2 chart result from the locked vanilla fixture.                                                                        | No prose claim yet. This is only layer one.                                                                                                                                                          |
| 6    | If defender is dual-typed, multiply both defending-type results.                                                                            | Immunity is not “overridden” by the other type unless local rules explicitly say so.                                                                                                                 |
| 7    | For romhack only: check the local type-chart delta fixture.                                                                                 | If unchecked, result is `base_gen2_only_unverified_local`.                                                                                                                                           |
| 8    | Check move-specific exceptions.                                                                                                             | Examples: typeless damage, immunity-bypass logic, custom move behavior, status exceptions.                                                                                                           |
| 9    | Check passive type abilities.                                                                                                               | Examples from your notebook: Dark status shield, Dragon’s Majesty, Dragon Imperial Scales, Poison contact poison, Psychic zero-damage branch, Steel recoil reduction, Grass healing, Electric speed. |
| 10   | Check item/status/field modifiers.                                                                                                          | This includes status shields, current status, weather/field, hazards, side effects, and any custom held item behavior.                                                                               |
| 11   | If the claim affects a move label, KO/survival claim, benchmark, or battle review, require source-derived or debugger-derived final result. | Shallow chart result is not enough for “best,” “catastrophic,” “guaranteed KO,” or “safe switch.”                                                                                                    |
| 12   | Emit the claim only through an evidence trace.                                                                                              | Otherwise write “unverified,” not a guessed type label.                                                                                                                                              |

The key rule: chart result, local effectiveness, final damage, and strategic value are different things. “Water is resisted by Dragon” is a chart claim. “Surf is a bad move here” is a state-transition claim. The second one needs more evidence.

## 2. Benchmark-position schema for type evidence

Use one evidence object per attacker/defender/move/battle-state interaction. Benchmarks should point to these objects by ID.

```yaml
type_evidence:
  evidence_id: "gll_romhack@commit_hash:bench_042:t17:attacker_move_defender"
  environment:
    name: "gll_romhack"              # or "vanilla_gsc"
    version: "commit_hash_or_fixture_version"
    mechanics_profile: "mechanics/gll/profile.yaml"
    source_hierarchy_applied: true

  battle_state:
    turn: 17
    state_hash: "..."
    known_information: "revealed_only"  # revealed_only | full_fixture | debugger_state
    hidden_info_assumptions:
      - field: "opponent_move_4"
        assumption: "unknown"
        impact: "cannot claim coverage safety"

  attacker:
    species: "Dragonite"
    current_types: ["Dragon", "Flying"]
    type_source:
      kind: "team_fixture"
      reference: "fixtures/gll/species_types.yaml:Dragonite"
    relevant_passives:
      - name: "Dragon's Majesty"
        present: true
        source: "local_docs/type_passives.md#dragons-majesty"

  defender:
    species: "Rhydon"
    current_types: ["Ground", "Rock"]
    type_source:
      kind: "team_fixture"
      reference: "fixtures/gll/species_types.yaml:Rhydon"
    relevant_passives:
      - name: "none_checked"
        present: false

  move:
    name: "Thunderbolt"
    resolved_type: "Electric"
    category: "Special"
    class: "damaging"                 # damaging | status | fixed_damage | typeless | custom
    contact: false
    move_source:
      kind: "move_fixture"
      reference: "fixtures/gll/moves.yaml:Thunderbolt"
    move_specific_exceptions:
      - name: "none_checked"
        applies: false

  base_gen2_chart_result:
    per_defender_type:
      Ground: 0
      Rock: 1
    aggregate: 0
    label: "immune"
    source:
      kind: "vanilla_gsc_type_chart_fixture"
      reference: "mechanics/vanilla_gsc/type_chart.yaml:Electric"

  romhack_chart_delta:
    status: "checked_no_delta"         # checked_no_delta | changed | unchecked
    local_result: 0
    source:
      kind: "source_extracted_fixture"
      reference: "mechanics/gll/type_chart_delta.yaml:Electric"

  passive_type_ability_interactions:
    - passive: "Dragon's Majesty"
      applies: true
      effect_claim: "damaging moves from Dragon attackers may treat immunities as resistances"
      source:
        kind: "local_source"
        reference: "engine/passives/dragon.asm:lines_or_symbol"
      resulting_effectiveness_after_passive: 0.5
      requires_debugger_confirmation: true

  item_status_field_modifiers:
    attacker_item: null
    defender_item: null
    attacker_status: "none"
    defender_status: "none"
    field:
      spikes_layers_attacker_side: 0
      spikes_layers_defender_side: 2
    relevant_modifiers:
      - name: "none_for_damage"
        applies: false

  final_local_damage_or_effectiveness_result:
    status: "debugger_verified"        # debugger_verified | source_derived | fixture_only | unavailable
    effectiveness_label: "resisted_after_dragon_majesty"
    damage_range: [18, 22]
    hit_result: "damaging_hit"
    secondary_effects:
      - "none"
    debugger_reference:
      command: "damage_debug --state bench_042_t17 --move Thunderbolt"
      output_hash: "sha256:..."
      log_reference: "debugger_logs/bench_042_t17_thunderbolt.txt"

  source_references:
    - kind: "vanilla_fixture"
      reference: "mechanics/vanilla_gsc/type_chart.yaml"
    - kind: "local_source"
      reference: "engine/passives/dragon.asm"
    - kind: "debugger"
      reference: "debugger_logs/bench_042_t17_thunderbolt.txt"

  confidence:
    level: "debugger_verified"
    allowed_claims:
      - "Base Gen 2 chart says Electric into Ground/Rock is immune."
      - "In this local romhack state, Dragon's Majesty makes this damaging hit nonzero and resisted."
      - "Debugger range is 18-22 HP."
    forbidden_claims:
      - "Ground is a hard immunity to this Dragon attack."
      - "Thunderbolt is neutral."
      - "This is safe without checking Dragon's Majesty."

  strategic_implication:
    summary: "Ground switch-in is not a hard stop against this Dragon attacker; at low HP it may still be picked off."
    benchmark_label_impact:
      move_label: "acceptable"
      catastrophe_branch: "Ground pivot at <=22 HP dies despite assumed immunity"
```

Confidence should be mechanical, not vibes:

| Confidence                        | Meaning                                                           | Allowed use                                                   |
| --------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------- |
| `debugger_verified`               | Exact local state was run through debugger.                       | Full benchmark labels, KO claims, battle review claims.       |
| `source_verified`                 | Local source says the mechanic applies, but exact damage not run. | Mechanics explanation, not precise damage.                    |
| `fixture_verified`                | Extracted chart/passive fixture checked against source.           | Chart/passive claim, not full strategic claim.                |
| `base_verified_vanilla`           | Vanilla GSC fixture only.                                         | Vanilla GSC analysis only.                                    |
| `base_gen2_only_unverified_local` | Base chart checked, local romhack not checked.                    | Must say “base Gen 2 says…” and mark local result unverified. |
| `unverified`                      | No admissible evidence.                                           | No type-effectiveness wording.                                |

## 3. Taxonomy of type-related mistakes

| Mistake type                            | Example                                                                   | What went wrong                                                 | Catch mechanism                                                                                                                                  |
| --------------------------------------- | ------------------------------------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Base chart error                        | “Water is neutral into Dragon.”                                           | Agent used memory instead of Gen 2 chart.                       | Unit test: `Water -> Dragon = 0.5`.                                                                                                              |
| Romhack delta error                     | “GLL uses vanilla chart here” without checking.                           | Agent skipped local chart delta layer.                          | Romhack benchmarks fail unless `romhack_chart_delta.status != unchecked`.                                                                        |
| Passive interaction error               | “Toxic this Dark type” despite Dark status shield.                        | Chart result was checked, but passive status layer was ignored. | Passive registry required for every type-bearing defender.                                                                                       |
| Immunity/resistance confusion           | “Ground is resisted by Flying.”                                           | 0 was treated as ½.                                             | Linter distinguishes `immune` from `resisted`.                                                                                                   |
| Dual-type aggregation error             | “Ground hits Rock/Flying super effectively because Rock is weak.”         | Agent looked at only one defender type.                         | Aggregation test: `Ground -> Rock/Flying = 0`.                                                                                                   |
| Move-type/category confusion            | “Shadow Ball is special in GSC” or “Bite is Normal in Gen 2.”             | Modern category or Gen 1 memory leaked in.                      | Move fixture must include generation-local type and category.                                                                                    |
| Damage-vs-type-effectiveness conflation | “It is super effective, so it KOs.”                                       | Type multiplier was confused with final damage.                 | KO claims require damage-debugger or source-derived range.                                                                                       |
| Hidden-info type assumption             | “This coverage is safe” when Hidden Power type or custom form is unknown. | Agent filled hidden info from expectation.                      | Unknown move/type branches must remain branches.                                                                                                 |
| Outdated-generation knowledge leak      | “Steel does not resist Ghost/Dark” in GSC.                                | Modern Gen VI+ chart leaked into Gen 2.                         | GSC fixture tests Steel resisting Ghost/Dark. In Gen II–V Steel resisted Ghost and Dark; those resistances were removed later. ([Bulbapedia][3]) |
| Source hierarchy violation              | Using Pokémon Showdown or memory over local GLL source/debugger.          | Wrong authority.                                                | Evidence object records source rank; lower-rank contradiction cannot override higher-rank result.                                                |

## 4. Corrected reasoning examples for tricky base cases

These are vanilla GSC chart claims. They are not automatically romhack claims unless the romhack evidence object says the chart and local layers match.

| Case                      |                                     Correct vanilla GSC result | Operational note                                                                                                              |
| ------------------------- | -------------------------------------------------------------: | ----------------------------------------------------------------------------------------------------------------------------- |
| Water into Dragon         |                                                              ½ | Dragon resists Water. The earlier “neutral” claim is a critical base-chart failure.                                           |
| Fire into Dragon          |                                                              ½ | Dragon resists Fire.                                                                                                          |
| Grass into Dragon         |                                                              ½ | Dragon resists Grass.                                                                                                         |
| Electric into Dragon      |                                                              ½ | Dragon resists Electric.                                                                                                      |
| Ground into Flying        |                                                              0 | Flying is immune to Ground. Do not call this “resisted.”                                                                      |
| Electric into Ground      |                                                              0 | Ground is immune to Electric.                                                                                                 |
| Normal into Ghost         |                                                              0 | Normal damaging moves do not affect Ghost.                                                                                    |
| Ghost into Normal         |                                                              0 | Ghost damaging moves do not affect Normal.                                                                                    |
| Ghost into Psychic, Gen 2 |                                                              2 | In Gen 2, Ghost is super effective into Psychic; this differs from the Gen 1 bug/behavior.                                    |
| Psychic into Dark, Gen 2  |                                                              0 | Dark is immune to Psychic. Dark was introduced in Gen 2, and its defensive chart includes Psychic immunity. ([Bulbapedia][4]) |
| Steel defender in GSC     | Resists many types, including Ghost and Dark; immune to Poison | Steel resisting Ghost/Dark is GSC-correct. Modern “Steel no longer resists Ghost/Dark” is not GSC-correct. ([Bulbapedia][3])  |

Dual-type aggregation examples:

| Attack type | Defender type(s) | Calculation | Correct result             |
| ----------- | ---------------- | ----------: | -------------------------- |
| Water       | Dragon/Flying    |       ½ × 1 | ½, resisted                |
| Ice         | Dragon/Flying    |       2 × 2 | 4×, double super effective |
| Electric    | Water/Flying     |       2 × 2 | 4×, double super effective |
| Electric    | Dragon/Flying    |       ½ × 2 | 1×, neutral                |
| Ground      | Rock/Flying      |       2 × 0 | 0, immune                  |
| Grass       | Water/Flying     |       2 × ½ | 1×, neutral                |
| Fire        | Steel/Ground     |       2 × 1 | 2×, super effective        |
| Electric    | Water/Ground     |       2 × 0 | 0, immune                  |

This table should become tests, not just documentation.

## 5. Romhack-specific examples

Using only the local facts you gave, some examples can be stated directly. Actual chart-delta examples cannot be asserted from the provided context because you have not supplied a verified GLL chart edit. So the system should handle that bucket explicitly: if no chart deltas are verified, the chart-delta suite is either empty-but-checked or blocked as `unchecked`; it should never silently pass.

### A. Base chart intuition remains correct

Example: non-Dragon attacker uses Earthquake into a Flying-type defender.

Evidence path:

```yaml
base_gen2_chart_result:
  Ground_vs_Flying: 0
romhack_chart_delta:
  status: "checked_no_delta"
move_specific_exceptions:
  applies: false
passive_type_ability_interactions:
  Dragon's Majesty:
    applies: false # attacker is not Dragon, or passive absent
final_result:
  effectiveness_label: "immune"
```

Allowed wording: “In this verified GLL state, Ground is still immune into Flying.”

Forbidden wording: “Ground is always useless into Flying in GLL.” Dragon’s Majesty may create exceptions for Dragon attackers, so “always” is too strong.

### B. Base chart intuition is wrong because the romhack changes the chart

Do not invent this. Instead, require one fixture for every actual chart delta found in local source.

Template:

```yaml
romhack_chart_delta_example:
  status: "changed"
  base_gen2:
    attack_type: "TYPE_A"
    defender_type: "TYPE_B"
    multiplier: 0.5
  gll_local:
    multiplier: 1
    source: "engine/type_chart.asm:symbol_or_line"
  regression:
    name: "gll_type_chart_delta_TYPE_A_into_TYPE_B"
    assertion: "type_eval(gll, TYPE_A, [TYPE_B]) == 1"
```

If the extracted GLL type chart has no differences from Gen 2, that should also be a source-derived fact:

```yaml
romhack_chart_delta:
  status: "checked_no_delta_global"
  source: "generated/type_chart_diff_report.txt"
  implication: "Romhack differences must come from passives, move exceptions, items, status, or field, not chart edits."
```

### C. Chart unchanged, but passive changes damage, status reliability, immunity behavior, or strategic value

Dark status shield:

Base chart may say a status move is type-legal, but GLL Dark can block the first eligible incoming status if full Dark, and half Dark has a 50% block chance. Therefore “status this Dark type” is not a type-effectiveness claim; it is a status-reliability claim requiring the Dark shield state.

Dragon’s Majesty:

Base chart may say Electric into Ground is immune or Ground into Flying is immune. If the attacker is Dragon and Dragon’s Majesty applies, a damaging move may treat immunities as resistances. Therefore “Ground is a hard Electric immunity” is not safe against a Dragon attacker until this passive layer is checked.

Dragon defender Imperial Scales:

Base chart may say Water into Dragon is resisted. GLL can add an additional reduction for non-super-effective hits into Dragon. So the shallow chart claim “resisted” is technically true but strategically incomplete. The benchmark should record both: `base_chart = 0.5`, `imperial_scales_applies = true`, `final_damage_range = debugger result`.

Poison defender contact poison:

A contact move can have good chart effectiveness but be strategically worse because the Poison defender may poison the contact attacker unless immunity/status/item rules block it. The type claim and the contact-risk claim should be separate fields.

Psychic defender zero-damage branch:

A move can “hit” and still deal 0 damage because of the Psychic defender passive. That is not an immunity unless the source/debugger says it is. The battle review should say “0-damage hit branch,” not “immune.”

Steel recoil reduction:

A recoil move’s chart result may be unchanged, but a Steel user reducing or removing recoil can make the move strategically better than the chart alone suggests.

Grass healing:

A hit that is technically super effective may fail to cross an important HP threshold if the Grass type heals between turns when not statused and not full HP. This belongs in final state-transition testing.

Flying and Spikes:

Flying-types ignore Spikes in your local facts. Spikes has 1/8, 1/6, 1/4 damage at one, two, three layers; fourth click fails; Rapid Spin clears all layers. These are not ordinary attack type-effectiveness claims, but they are type-dependent field mechanics and should be included in the same reliability system.

### D. Damage debugger overrides shallow chart conclusion

Example pattern:

```yaml
shallow_claim:
  text: "Surf is resisted into Dragon, so it is probably okay chip."
  evidence_level: "base_gen2_only"

local_debugger_result:
  base_chart: 0.5
  passive: "Imperial Scales applies"
  damage_range: [low, high]
  threshold_result: "not_a_3HKO_after_grass_heal_or_leftovers_if_applicable"
  source: "debugger_logs/..."

corrected_policy:
  text: "Do not choose Surf for progress into this Dragon unless the debugger range crosses the benchmark threshold. Prefer verified super-effective coverage, status after shield checks, hazards, or pivoting."
```

This is the important shift: the debugger does not merely decorate the explanation. It decides whether the benchmark label is legal.

## 6. Integration into benchmark and policy work

Every benchmark that uses type reasoning should contain these required fields:

```yaml
benchmark:
  id: "bench_042"
  environment: "vanilla_gsc" # or gll_romhack
  mechanics_profile_version: "..."
  battle_state_hash: "..."
  win_condition: "..."
  irreplaceable_pieces:
    - species: "..."
      reason: "..."
  opponent_top_responses:
    - move_or_switch: "..."
      evidence_required: true
  candidate_moves:
    - move: "Ice Beam"
      type_evidence_id: "..."
      state_transition_id: "..."
      label: "best"
    - move: "Surf"
      type_evidence_id: "..."
      state_transition_id: "..."
      label: "catastrophic"
  catastrophe_branches:
    - premise: "wrong_type_claim"
      branch: "clicks Surf into Dragon/Flying instead of Ice Beam"
      consequence: "misses KO / loses tempo / allows setup"
  information_that_changes_answer:
    - "Hidden Power type"
    - "Dark shield already consumed"
    - "Dragon's Majesty active"
    - "Spikes layers and Flying status"
  source_references:
    - "mechanics/vanilla_gsc/type_chart.yaml"
    - "mechanics/gll/type_passives.yaml"
    - "debugger_logs/bench_042/*.txt"
```

Promotion gates for heuristics involving type effectiveness:

1. A heuristic must be scoped to an environment: `vanilla_gsc`, `gll_romhack`, or explicitly both. No cross-environment rule by default.

2. A heuristic may not contain type words unless every example has a `type_evidence_id`.

3. A romhack heuristic may not be promoted if any relevant local layer is `unchecked`: chart delta, passive, move exception, item/status/field modifier.

4. A “best move” or “catastrophic move” label requires state-transition evidence, not just type evidence.

5. At least one regression must cover the exact failure mode the heuristic is supposed to avoid.

6. If the heuristic generalizes across dual types, it needs dual-type tests.

7. If the heuristic mentions immunities, it needs an immunity test and at least one romhack exception test, especially Dragon’s Majesty.

8. If the heuristic mentions status reliability, it needs Dark shield, type immunity, statused target, item, and already-statused target branches where applicable.

9. Policy explanations should be generated from evidence objects, not handwritten from model memory.

Regression tests that should fail on wrong type claims:

```python
def test_water_into_dragon_is_resisted_gsc():
    assert type_eval("vanilla_gsc", "Water", ["Dragon"]).aggregate == 0.5

def test_agent_cannot_emit_type_word_without_evidence_id():
    text = agent_explain(...)
    assert no_type_keywords_without_evidence_id(text)

def test_gll_type_claim_blocked_when_delta_unchecked():
    result = type_eval("gll_romhack", "Water", ["Dragon"], local_delta_status="unchecked")
    assert result.allowed_claim_label == "base_gen2_only_unverified_local"
    assert "resisted in GLL" not in result.allowed_text

def test_ground_into_rock_flying_is_immune_not_super_effective():
    assert type_eval("vanilla_gsc", "Ground", ["Rock", "Flying"]).aggregate == 0

def test_dragon_majesty_prevents_hard_immunity_claim():
    state = make_gll_state(attacker_type="Dragon", move_type="Electric", defender_types=["Ground"])
    result = type_eval("gll_romhack", state=state)
    assert result.forbidden_claims.includes("hard immunity")
```

How to label uncertainty:

| Evidence state                             | Required wording                                                               |
| ------------------------------------------ | ------------------------------------------------------------------------------ |
| Base Gen 2 checked, romhack unchecked      | “Base Gen 2 says X; GLL local result is unverified.”                           |
| Chart checked, passive unchecked           | “Chart result is X, but local passive impact is unverified.”                   |
| Passive source checked, no damage debugger | “Source indicates the passive applies; exact damage/range unverified.”         |
| Debugger checked                           | “Debugger shows X in this exact state.”                                        |
| Hidden info unresolved                     | “Under revealed information, this branches; no single type claim is licensed.” |

## 7. Minimal regression suite

### Vanilla GSC smoke tests

These should run before trusting any vanilla GSC analysis.

| Test                        | Expected |
| --------------------------- | -------: |
| `Water -> Dragon`           |      0.5 |
| `Fire -> Dragon`            |      0.5 |
| `Grass -> Dragon`           |      0.5 |
| `Electric -> Dragon`        |      0.5 |
| `Ground -> Flying`          |        0 |
| `Electric -> Ground`        |        0 |
| `Normal -> Ghost`           |        0 |
| `Ghost -> Normal`           |        0 |
| `Ghost -> Psychic`          |        2 |
| `Psychic -> Dark`           |        0 |
| `Dark -> Psychic`           |        2 |
| `Ghost -> Steel`            |      0.5 |
| `Dark -> Steel`             |      0.5 |
| `Poison -> Steel`           |        0 |
| `Fire -> Steel`             |        2 |
| `Fighting -> Steel`         |        2 |
| `Ground -> Steel`           |        2 |
| `Water -> Steel`            |        1 |
| `Electric -> Steel`         |        1 |
| `Water -> Dragon/Flying`    |      0.5 |
| `Ice -> Dragon/Flying`      |        4 |
| `Electric -> Water/Flying`  |        4 |
| `Electric -> Dragon/Flying` |        1 |
| `Ground -> Rock/Flying`     |        0 |
| `Grass -> Water/Flying`     |        1 |

Move metadata tests for GSC:

| Test                   | Expected                                                                 |
| ---------------------- | ------------------------------------------------------------------------ |
| `Ice Beam`             | Ice, Special, damaging                                                   |
| `Thunderbolt`          | Electric, Special, damaging                                              |
| `Earthquake`           | Ground, Physical, damaging                                               |
| `Shadow Ball`          | Ghost, Physical, damaging                                                |
| `Bite` in Gen 2        | Dark, Special, damaging                                                  |
| `Thunder Wave`         | Status move; do not evaluate as ordinary damaging Electric effectiveness |
| `Status move category` | Separate from damaging type-effectiveness                                |

### Romhack-local smoke tests

These must be generated from local source/docs/debugger. From your known facts, the minimum suite should include:

| Test                                    | Expected                                                                                                                         |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `gll_chart_diff_report_exists`          | Type chart delta checked against Gen 2.                                                                                          |
| `gll_chart_delta_fixtures_match_source` | Every delta has source reference; if none, report `checked_no_delta_global`.                                                     |
| `Spikes layer 1`                        | Max HP / 8.                                                                                                                      |
| `Spikes layer 2`                        | Max HP / 6.                                                                                                                      |
| `Spikes layer 3`                        | Max HP / 4.                                                                                                                      |
| `Spikes layer 4 click`                  | Fails.                                                                                                                           |
| `Flying ignores Spikes`                 | No Spikes damage.                                                                                                                |
| `Rapid Spin clears Spikes`              | All layers cleared.                                                                                                              |
| `Dark full status shield`               | First eligible incoming status blocked.                                                                                          |
| `Dark half status shield`               | 50% block chance under seeded RNG.                                                                                               |
| `Dragon's Majesty immunity case`        | Dragon attacker’s damaging move into a chart immunity does not allow “hard immunity” wording; exact result from source/debugger. |
| `Imperial Scales non-SE hit`            | Non-super-effective hit into Dragon reduced.                                                                                     |
| `Imperial Scales SE hit`                | Super-effective hit not reduced, unless source says otherwise.                                                                   |
| `Electric speed passive`                | Electric type speed multiplier applied.                                                                                          |
| `Grass heal eligible`                   | Heals between turns if not statused and not full HP.                                                                             |
| `Grass heal blocked by status`          | No heal.                                                                                                                         |
| `Poison contact punishment`             | Contact attacker can be poisoned unless blocked by immunity/status/item.                                                         |
| `Psychic zero-damage branch`            | 0 damage possible while hit still registers.                                                                                     |
| `Steel recoil reduction`                | Recoil reduced or removed for Steel user on recoil move.                                                                         |
| `type_claim_linter_gll`                 | No romhack type wording without local evidence trace.                                                                            |

## 8. Examples where best move changes because the type premise was wrong

### Example 1: Water into Dragon/Flying

Mistaken premise: “Water is neutral into Dragon, so Surf is fine.”

Corrected evidence: In vanilla GSC, Water into Dragon is ½. Into Dragon/Flying, Water is `½ × 1 = ½`. Ice into Dragon/Flying is `2 × 2 = 4`.

Why previous move fails: Surf is not neutral coverage; it is resisted. Against Dragon/Flying, Ice Beam is massively stronger even without STAB in many cases.

Better policy: When attacking Dragon/Flying, prefer verified Ice coverage over Water unless debugger damage says otherwise.

Regression to add:

```yaml
name: "dragon_flying_water_vs_ice_choice"
assertions:
  - type_eval(vanilla_gsc, Water, [Dragon, Flying]) == 0.5
  - type_eval(vanilla_gsc, Ice, [Dragon, Flying]) == 4
  - benchmark_label(Ice_Beam) > benchmark_label(Surf) unless damage_debugger_overrides
```

### Example 2: Ground into Rock/Flying

Mistaken premise: “Rock is weak to Ground, so Earthquake is super effective.”

Corrected evidence: Ground into Rock/Flying is `2 × 0 = 0`.

Why previous move fails: Earthquake does no damage. The move choice can lose the turn outright.

Better policy: Against Rock/Flying, use a move that actually hits, such as Rock, Ice, Water, or Electric coverage depending on the position.

Regression to add:

```yaml
name: "ground_into_rock_flying_immunity"
assertion: "Ground -> Rock/Flying == 0"
catastrophic_label: "Earthquake into Rock/Flying when damaging hit required"
```

### Example 3: Electric into Dragon/Flying

Mistaken premise: “Flying is weak to Electric, so Thunderbolt is super effective into Dragonite.”

Corrected evidence: Electric into Dragon/Flying is `½ × 2 = 1`.

Why previous move fails: The move is neutral, not super effective. If the plan needs a KO or heavy damage, the premise is false.

Better policy: Prefer Ice coverage into Dragon/Flying when available; treat Electric as neutral chip unless debugger says the damage threshold is still met.

Regression to add:

```yaml
name: "electric_into_dragon_flying_neutral"
assertion: "Electric -> Dragon/Flying == 1"
```

### Example 4: Psychic into Dark

Mistaken premise: “Psychic is strong neutral damage into Umbreon.”

Corrected evidence: In vanilla GSC, Psychic into Dark is 0.

Why previous move fails: The move has no effect. It gives the opponent a free turn.

Better policy: Use non-Psychic coverage, switch, set up, or pursue a state plan that is legal against Dark. In GLL, also check Dark’s status shield before assuming status is the fallback.

Regression to add:

```yaml
name: "psychic_into_dark_no_effect_gsc"
assertion: "Psychic -> Dark == 0"
```

### Example 5: Modern Steel knowledge leaking into GSC

Mistaken premise: “Steel does not resist Ghost or Dark.”

Corrected evidence: In Gen II–V, Steel resisted Ghost and Dark. ([Bulbapedia][3])

Why previous move fails: Crunch, Pursuit, or Shadow Ball damage may be overestimated into Steel defenders. In GSC specifically, move category also matters: Ghost is physical and Dark is special by type category.

Better policy: Into Steel, look for Fire, Fighting, or Ground pressure first; Water and Electric may be neutral depending on the secondary type; never import modern Steel assumptions into GSC.

Regression to add:

```yaml
name: "gsc_steel_resists_ghost_dark"
assertions:
  - "Ghost -> Steel == 0.5"
  - "Dark -> Steel == 0.5"
```

### Example 6: GLL Dark status shield

Mistaken premise: “The chart does not block this status, so status is reliable.”

Corrected local evidence: Full Dark blocks the first eligible incoming status; half Dark has a 50% block chance.

Why previous move fails: A sleep, poison, paralysis, or other status plan can burn a turn and merely consume or test the shield.

Better policy: Benchmark status moves against Dark as probabilistic or shield-consuming actions. Sometimes attacking, setting hazards, or forcing the shield first is better.

Regression to add:

```yaml
name: "gll_dark_status_shield_blocks_first_status"
state:
  defender_type: "Dark"
  dark_shield: "full"
assertion: "incoming_eligible_status_result == blocked"
```

### Example 7: GLL Dragon’s Majesty and false hard immunities

Mistaken premise: “Ground is immune to Electric, so switching Ground into this Dragon attacker is always safe.”

Corrected local evidence: Dragon’s Majesty can make damaging moves from Dragon attackers treat immunities as resistances.

Why previous move fails: The supposed hard immunity may become nonzero resisted damage. At low HP, that changes the switch from safe to losing.

Better policy: Against Dragon attackers, do not label immunity pivots as hard stops until Dragon’s Majesty is checked and the debugger range is known.

Regression to add:

```yaml
name: "gll_dragon_majesty_immunity_to_resistance"
state:
  attacker_type: "Dragon"
  move_type: "Electric"
  defender_type: "Ground"
assertion: "hard_immunity_claim_forbidden"
requires_debugger: true
```

### Example 8: GLL Imperial Scales and neutral/reduced damage

Mistaken premise: “Neutral coverage into Dragon is acceptable chip.”

Corrected local evidence: Dragon defenders have Imperial Scales; non-super-effective hits into Dragon are reduced.

Why previous move fails: The agent may choose a move that looks neutral or merely resisted by chart but fails every important damage threshold.

Better policy: Prefer verified super-effective coverage, status plans whose reliability is checked, hazards, or pivoting. For benchmarks, label non-SE attacks into Dragon only after final local damage range.

Regression to add:

```yaml
name: "gll_imperial_scales_reduces_non_se_into_dragon"
assertions:
  - "non_super_effective_hit_into_dragon_has_extra_reduction"
  - "benchmark_damage_label_requires_debugger"
```

### Example 9: GLL Psychic zero-damage branch

Mistaken premise: “This super-effective hit always breaks through.”

Corrected local evidence: Psychic defenders have a small chance to take 0 damage while still registering a hit.

Why previous move fails: A “guaranteed KO” or “guaranteed chip” line may not be guaranteed.

Better policy: Mark exact-KO lines into Psychic defenders as probabilistic unless the debugger branch excludes zero damage. If losing on the zero-damage branch is catastrophic, the move cannot be labeled safely best.

Regression to add:

```yaml
name: "gll_psychic_zero_damage_hit_branch"
assertions:
  - "hit_can_register_with_zero_damage"
  - "guaranteed_KO_claim_forbidden_if_zero_damage_branch_alive"
```

## 9. Recommended wording rules for the agent

The agent may say “super effective,” “resisted,” “immune,” or “neutral” only when all of these are true:

1. The environment is bound.
2. The attacker, defender, and move are resolved.
3. The relevant chart lookup is complete.
4. Dual-type aggregation is complete.
5. For romhack, chart deltas, passives, move exceptions, item/status/field modifiers have been checked or explicitly ruled irrelevant.
6. The sentence is backed by an evidence ID.

Preferred wording:

“**In vanilla GSC**, Ice is 4× into Dragon/Flying.”

“**Base Gen 2 chart says** Water is resisted into Dragon/Flying; **GLL local passive impact is not checked**, so I will not label the final damage.”

“**The GLL debugger shows** Thunderbolt from this Dragon attacker deals nonzero resisted damage into this Ground defender because Dragon’s Majesty applies.”

“**Chart result:** resisted. **Final damage result:** below 3HKO after Imperial Scales. Therefore the move is not acceptable for this benchmark.”

Forbidden wording:

“Water is neutral into Dragon.”

“Ground walls Electric here,” when the attacker is Dragon and Dragon’s Majesty has not been checked.

“This is super effective so it KOs.”

“Psychic is useless into Dark in the romhack,” unless the local chart/passive/status behavior has been checked. Say “Base Gen 2 Psychic into Dark is immune; GLL local result unverified” instead.

“Status should work because type chart does not block it.” Status reliability is not ordinary damaging type effectiveness.

For uncertainty, the agent should use exact phrases:

“Unverified for this ruleset.”

“Base Gen 2 only; local romhack result unchecked.”

“Chart checked, passive layer unchecked.”

“Source says the passive applies; exact damage debugger not run.”

“Debugger verified in this exact state.”

The sharp implementation point is this: make the evidence trace the only way prose can get type words. The model can reason, but it cannot author mechanics facts from memory. If a type premise is wrong, the failure should happen in a unit test or benchmark gate, not in a heuristic, policy label, or battle review.

[1]: https://pokemondb.net/type/old "Generation 1 & 2-5 type chart | Pokémon Database"
[2]: https://bulbapedia.bulbagarden.net/wiki/Damage_category "Damage category - Bulbapedia, the community-driven Pokémon encyclopedia"
[3]: https://bulbapedia.bulbagarden.net/wiki/Steel_%28type%29 "Steel (type) - Bulbapedia, the community-driven Pokémon encyclopedia"
[4]: https://bulbapedia.bulbagarden.net/wiki/Dark_%28type%29 "Dark (type) - Bulbapedia, the community-driven Pokémon encyclopedia"
