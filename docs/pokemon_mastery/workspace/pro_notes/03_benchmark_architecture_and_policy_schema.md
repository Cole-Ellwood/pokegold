Your instinct is right: the unit of learning should not be “Cloyster sets Spikes” or “Explosion opens holes.” The unit should be:

> In this exact visible state, under this mechanics profile, choose the transition that improves a named winning route while not opening a worse plausible opponent route.

That is the whole project.

I am not going to pretend I know the private details of the Gym Leader Lab fork beyond what you named. Treat it as a mechanics fork with explicit deltas: three-layer Spikes, passive type abilities, and any other romhack-specific rules must live in a delta register and be tested before vanilla GSC principles are promoted into that layer.

For vanilla GSC, a few mechanics have to be treated as hard truth, not strategy flavor. Spikes has one layer and deals 1/8 HP on grounded switch-ins; Sleep Talk can call Rest in GSC, causing the user to heal and reset Rest sleep; Roar and Whirlwind must be the last action in the turn to work; Explosion and Self-Destruct halve the target’s Defense; and GSC sleep is less absolute than RBY because Pokémon can attack on the turn they wake and Sleep Talk users are a major countermeasure. ([Smogon][1])

## 1. The architecture: benchmark cards become transition tests, not answer memorization

Build the policy loop as a staged pipeline:

```text
visible battle state
  -> mechanics resolver
  -> legal/effective action enumerator
  -> state feature extractor
  -> opponent belief / branch generator
  -> candidate transition evaluator
  -> dominance-rule arbitrator
  -> ranked policy answer
  -> turn ledger update
  -> mistake mining
  -> new regression benchmark
```

The key separation is this:

```text
public benchmark card:
  visible state, mechanics profile, candidate move space, required output fields

hidden oracle:
  best / acceptable / catastrophic labels
  catastrophe branches
  expert rationale
  answer-changing information
  mutation family
```

The policy generator should never see `best`, `acceptable`, or `catastrophic`. The evaluator should. The agent should output a structured answer, not just a move. That answer should say: “I choose X because it advances route A, avoids catastrophe B, preserves piece C, and would flip to Y if hidden info Z were confirmed.”

That prevents answer-key memorization better than prose tests do, because the model has to bind its answer to state variables. A move-only benchmark teaches mimicry. A transition benchmark teaches policy.

A good policy runner should do this every turn:

```python
def choose_action(state, mechanics, policy_rules, opponent_model):
    legal_actions = mechanics.enumerate_legal_actions(state)

    candidates = []
    for action in legal_actions:
        transition = mechanics.project_own_action(state, action)
        opp_branches = opponent_model.enumerate_responses(state, action)

        features = extract_transition_features(
            state=state,
            action=action,
            transition=transition,
            opp_branches=opp_branches,
            mechanics=mechanics,
        )

        hard_flags = apply_hard_filters(features)
        route_score = score_routes(features)
        dominance = arbitrate(features, hard_flags, route_score)

        candidates.append({
            "action": action,
            "features": features,
            "hard_flags": hard_flags,
            "route_score": route_score,
            "dominance": dominance,
        })

    return rank_candidates(candidates)
```

The baseline should be deterministic and transparent first. Do not start with a learned preference model. Do not start with deep search. First build the boring thing that catches mechanics errors, state errors, obvious catastrophes, preservation failures, and no-op moves. That will teach you more than a clever but opaque model.

## 2. State representation for long-form GSC-style singles

The state should not be a transcript. It should be a compact, canonical, machine-readable battle position.

Mandatory fields:

```json
{
  "mechanics_profile": "vanilla_gsc",
  "turn": 37,
  "side_to_move_context": "simultaneous_choice",

  "our_active": "Cloyster",
  "opp_active": "Snorlax",

  "our_side": {
    "spikes_layers": 0,
    "screens": {"reflect": 0, "light_screen": 0},
    "sleep_clause_used": false
  },

  "opp_side": {
    "spikes_layers": 1,
    "screens": {"reflect": 0, "light_screen": 0},
    "sleep_clause_used": true
  },

  "our_team": [],
  "opp_team_visible": [],

  "active_state": {
    "our_hp_pct": 42,
    "opp_hp_pct": 68,
    "our_status": "none",
    "opp_status": "none",
    "our_boosts": {"atk": 0, "def": 0, "spe": 0, "spa": 0, "spd": 0},
    "opp_boosts": {"atk": 1, "def": 1, "spe": -1, "spa": 0, "spd": 0}
  },

  "known_moves": {
    "our_active": ["Spikes", "Surf", "Toxic", "Explosion"],
    "opp_active": ["Curse", "Rest", "Double-Edge"]
  },

  "pp": {
    "our_active": {"Spikes": 31, "Surf": 13, "Toxic": 10, "Explosion": 1},
    "opp_active": {"Curse": 13, "Rest": 8, "Double-Edge": 10}
  },

  "speed_relation": {
    "our_active_vs_opp_active": "slower"
  },

  "damage_bands": {
    "Explosion_vs_opp_active": {"min_pct": 54, "max_pct": 64, "ko_chance": 0},
    "opp_DoubleEdge_vs_our_active": {"min_pct": 39, "max_pct": 46, "ko_chance": 0}
  },

  "visible_roles": {
    "our_irreplaceables": [],
    "opp_win_conditions": [],
    "our_win_conditions": []
  }
}
```

Mandatory means the policy cannot make a serious move choice without it. In GSC-style singles, the must-have state is:

Active Pokémon, bench Pokémon, HP, status, sleep source and counters where known, boosts, known moves, possible moves, PP for critical moves, side conditions, Spikes layers, groundedness, speed relation, damage thresholds, remaining defensive answers, current win conditions, sleep clause status, mechanics profile, and revealed hidden information.

Useful later:

Exact PP for every move, damage range confidence, inferred EV/DV assumptions, opponent set priors, opponent incentive model, previous switch patterns, Rest-cycle counters, phazing PP, spinner/spinblocker status, route objects, state hash, and a log-derived summary of why the current state exists.

Tempting but unnecessary:

Full raw battle log in the policy input, long natural-language “strategic context,” species slogans, huge unconstrained possible-set lists, uncalibrated “momentum” scores, and exact simulator rollouts for every action before the state validator is reliable.

The most dangerous useless field is prose like “Cloyster is the Spiker.” That is not a state fact. A better field is:

```json
{
  "pokemon": "Cloyster",
  "current_roles": [
    {
      "role": "spikes_setter",
      "viable_now": false,
      "reason": "opponent side already has max layers"
    },
    {
      "role": "physical_emergency_explosion",
      "viable_now": true,
      "target": "Snorlax"
    }
  ]
}
```

Species is identity. Role is state-dependent.

## 3. Benchmark position schema

A benchmark should have two layers: public state and hidden oracle.

Public card:

```json
{
  "id": "gsc-spikes-max-004",
  "version": 1,
  "mechanics_profile": "romhack_gym_leader_lab",
  "tags": [
    "three_layer_spikes",
    "maxed_spikes",
    "state_legality",
    "fourth_click_failure"
  ],

  "position_snapshot": {
    "turn": 22,
    "our_active": "Forretress",
    "opp_active": "Snorlax",
    "our_side": {"spikes_layers": 1},
    "opp_side": {"spikes_layers": 3, "max_spikes_layers": 3},
    "our_active_hp_pct": 58,
    "opp_active_hp_pct": 71,
    "opp_boosts": {"atk": 1, "def": 1, "spe": -1},
    "our_moves": ["Spikes", "Rapid Spin", "Hidden Power Bug", "Explosion"],
    "known_opp_moves": ["Curse", "Rest", "Double-Edge"],
    "speed_relation": "our_active_slower"
  },

  "candidate_moves_public": [
    "Spikes",
    "Rapid Spin",
    "Hidden Power Bug",
    "Explosion",
    "switch:Skarmory",
    "switch:Misdreavus"
  ],

  "required_answer_fields": [
    "chosen_action",
    "candidate_ranking",
    "current_win_conditions",
    "irreplaceable_pieces",
    "catastrophe_branch",
    "answer_changing_information",
    "rules_fired"
  ],

  "hidden_info_visible_to_policy": {
    "opp_fourth_move": "unknown",
    "opp_bench": "partially_revealed"
  }
}
```

Hidden oracle:

```json
{
  "id": "gsc-spikes-max-004",
  "oracle": {
    "best": ["Explosion"],
    "acceptable": ["switch:Skarmory"],
    "catastrophic": ["Spikes"],

    "why_best": {
      "Explosion": "Removes or cripples the active Curse Snorlax route while Forretress has no further Spikes value because opponent side is already at max layers."
    },

    "why_catastrophic": {
      "Spikes": "Fourth Spikes click fails / gives no state progress, while +1 Snorlax can continue its route."
    },

    "catastrophe_branches": [
      {
        "move": "Spikes",
        "branch": "Spikes fails; Snorlax Curses again; Skarmory no longer safely contains the route after prior chip."
      }
    ],

    "answer_changing_information": [
      {
        "field": "opp_has_protect_or_ghost_switch",
        "current": "not confirmed",
        "if_changed": "Explosion becomes worse; switch or attack may become preferred."
      }
    ],

    "heuristic_arbitration": [
      {
        "losing_heuristic": "set Spikes",
        "dominant_rule": "state legality / max layer no-op"
      },
      {
        "losing_heuristic": "preserve Forretress",
        "dominant_rule": "Forretress no longer provides hazard progress; Snorlax route is immediate."
      }
    ]
  }
}
```

A benchmark should force the agent to answer “so what?” after the move. If the answer is “it’s generally good,” the benchmark failed.

## 4. One-turn cards versus multi-turn branch trees

Use both.

One-turn cards test the current decision. They should be sharp, minimal, and adversarial. They test legality, immediate catastrophe, role preservation, hidden-info handling, and heuristic arbitration.

Branch trees test whether the agent can re-score after the world changes. These are essential for sleep, Explosion, Rest cycles, phazing, and hidden coverage.

Example branch card:

```json
{
  "id": "gsc-sleep-setup-branch-002",
  "root_decision": {
    "our_active": "Jynx",
    "opp_active": "Raikou",
    "our_candidate_moves": ["Lovely Kiss", "Ice Beam", "switch:Snorlax"],
    "expected_best": "Lovely Kiss"
  },

  "branches": [
    {
      "event": "Lovely Kiss misses",
      "new_state": {
        "our_active_hp_pct": 41,
        "opp_active": "Raikou",
        "opp_last_move": "Thunderbolt"
      },
      "required_rescore": true,
      "expected_policy_shift": "do not continue setup script; preserve Jynx or switch to special sponge"
    },
    {
      "event": "Lovely Kiss hits; opponent switches sleeping Raikou out to Sleep Talk Snorlax",
      "required_rescore": true,
      "expected_policy_shift": "do not assume free setup; evaluate Sleep Talk / Curse / Rest lines"
    },
    {
      "event": "Raikou wakes early and Roars",
      "required_rescore": true,
      "expected_policy_shift": "route lost; re-evaluate with revealed wake"
    }
  ]
}
```

One-turn cards teach choice. Branch trees teach adaptation. You need both because bad LLM-like play often looks good on turn one and then keeps following the same script after the state has invalidated it.

## 5. Candidate move ranking: use a hybrid

The best architecture is not pure hard rules, not pure weighted scoring, not pure search, and not pure learned preference. Use a hybrid:

First, hard filters:

```text
1. Is the move legal?
2. Does the move have any effect under this mechanics profile?
3. Is it blocked by clause, type immunity, status, max layers, Protect, Ghost, Substitute, or full-HP Rest failure?
4. Does it immediately lose to a revealed or high-plausibility punish?
```

Then dominance checks:

```text
1. Does this expose an irreplaceable piece?
2. Does it allow an immediate opposing win route?
3. Does it close our only concrete win route?
4. Does it spend a one-time resource without naming the route it opens?
```

Then route scoring:

```text
1. Which of our win routes improves?
2. Which opponent route is denied?
3. What resource changes? HP, PP, status, hazards, sleep clause, Explosion, phazer health.
4. What hidden information is gained?
5. What future move becomes forced or easier?
```

Then shallow explicit search for branch-heavy turns:

```text
- sleep hit / miss / wake / switch
- Explosion connects / Ghost / Protect / target switch
- Rest now / punished by setup / wakes into phaze
- Spikes set / spinner enters / spinblocker available
- phaze works / fails / reveals new threat
```

A learned preference model can come later, but only as a tie-breaker or candidate ordering model. It must never override mechanics legality or catastrophe filters.

The ranking vector should be lexicographic before it is numeric:

```json
{
  "action": "Explosion",
  "rank_key": {
    "legal_and_effective": true,
    "immediate_catastrophe": false,
    "preserves_required_answers": true,
    "denies_opp_primary_route": true,
    "advances_our_route": true,
    "resource_cost_justified": true,
    "expected_value_score": 0.74
  }
}
```

Damage is late in the ordering. Route comes before damage. Damage only matters because it changes a route.

## 6. Arbitration between true heuristics

Most bad Pokémon agents fail because they treat heuristics as independent advice. They need precedence.

Use policy rules with triggers, exceptions, and catastrophe branches.

Example:

```yaml
policy_rule:
  id: spikes_set_when_live
  heuristic: set_spikes
  trigger:
    - opponent_side.spikes_layers < mechanics.max_spikes_layers
    - active_has_move: Spikes
    - setter_survives_worst_plausible_branch: true
    - grounded_opp_remaining_count >= 2
    - immediate_opp_win_route_if_no_action: false
  exceptions:
    - opponent_side.spikes_layers == mechanics.max_spikes_layers
    - active_is_irreplaceable_defensive_answer: true
    - opponent_can_spin_for_free_next_turn_and_spinblock_plan_absent: true
    - current_turn_has_route_conversion_move: true
    - opponent_active_can_setup_to_uncontainable_state: true
  catastrophe:
    - clicking_spikes_at_max_layers
    - letting_curse_lax_get_unchecked_extra_boost
```

For the heuristics you listed:

“Set Spikes” loses to state legality, immediate loss, irreplaceable setter preservation, and free spin if you cannot contest removal.

“Preserve the Spiker” loses when the Spiker has already completed its hazard job and Explosion or sacrifice opens a concrete route.

“Attack now” wins when it prevents Rest, setup, spin, phaze, or a KO threshold that matters. It loses when damage does not alter a route and preservation or hazards do.

“Use sleep” wins when sleep clause is open, the target is not already statused, the miss branch is tolerable, and the target meaningfully blocks a route. It loses when the target is a Sleep Talk absorber, already statused, behind a sleep-blocking condition, or when a miss immediately loses.

“Set up” wins only if the opponent’s next plausible turn cannot remove the setup, phaze it, Explode on it, wake and punish, or reveal coverage that flips the matchup.

“Switch to preserve a defensive answer” wins when the active is needed for a future live threat and the switch-in is not being asked to absorb an impossible load.

“Explosion converts” wins only when the Explosion user is now less valuable than the route opened by removing the target. It loses if the opponent has a plausible Ghost/Protect/pivot branch, or if the exploding Pokémon is the only answer to a remaining threat.

“Rest now” wins when delaying Rest makes the piece unable to perform its role. It loses if Rest is full-HP/no-op, if sleep turns give the opponent a decisive setup route, or if the piece is no longer needed.

“Phaze now” wins when boost accumulation is the actual threat and the phazer can make the move work under GSC timing. Roar and Whirlwind are not generic panic buttons in GSC because they must be the last action in the turn. ([Smogon][1])

“Scout hidden coverage” wins when the information changes a future forced decision and the cost of scouting is lower than the cost of being wrong. It loses when scouting hands the opponent the route you are trying to avoid.

## 7. Dominance rules for GSC-style singles

Use these as hard policy ordering:

1. Mechanics truth dominates strategy slogans. A move that fails, is illegal, is maxed out, is blocked, or cannot affect the target cannot be rescued by “good strategic intent.”

2. Immediate catastrophe dominates long-term value. Do not set hazards, scout, or preserve something if the opponent’s next plausible turn creates an unanswerable route.

3. Irreplaceable-answer preservation dominates chip damage. If a Pokémon is the only remaining answer to a live opposing route, its HP is a strategic resource, not a number to trade casually.

4. Route conversion dominates generic preservation. A sacrifice or Explosion is good only if it opens a named route that survives the remaining opposing pieces.

5. State-dependent role dominates species role. “Skarmory walls physical attackers” is not a policy. “This 43% Skarmory with 3 Spikes layers on our side still checks non-Fire Blast Snorlax once but cannot switch twice” is a policy fact.

6. Sleep is temporary opportunity, not ownership of the game. Miss, wake, Sleep Talk, switch, phaze, and new coverage all require re-scoring.

7. Hazards are route multipliers, not intrinsic progress. Spikes matter when they change switch costs, Rest cycles, KO bands, phazing value, or Explosion ranges.

8. PP can become the win condition. In long GSC-style games, wasting a scarce PP move can be worse than losing HP.

9. Damage only matters if it changes the route. Random chip is weak. Chip that forces Rest, blocks a switch, creates a 2HKO after Spikes, or enables Explosion is strong.

10. Hidden-info plausibility beats wishful thinking. “They have not revealed Fire coverage” does not mean “they cannot have Fire coverage.”

11. The worst plausible branch matters more than the average branch when the loss is irreversible and avoidable.

12. Result quality and decision quality are separate. A good move can miss. A bad move can crit. The review should grade the decision from pre-turn information.

## 8. Opponent modeling tiers

Your four-tier decomposition is good. I would keep it.

Tier 1: immediate punish.

This includes revealed or highly plausible actions that punish your move immediately: KO, setup, Rest, phaze, spin, Explosion, Ghost switch into Explosion, Protect, sleep absorber, status immunity, or coverage reveal.

Tier 2: role-aware preservation.

The opponent does not randomly throw away their only Snorlax answer, spinner, phazer, special wall, win condition, or sleep absorber unless doing so opens a better route. This tier stops the agent from assuming the opponent will let your plan happen.

Tier 3: incentive-compatible response.

The opponent chooses actions that advance their route. They may switch, double, Rest, phaze, attack, preserve, or sack according to incentives. This is not omniscient mind-reading. It is “what would a competent opponent want from this state?”

Tier 4: hidden-info belief state.

This tracks what sets, coverage, PP, speed, and passive abilities are confirmed, likely, plausible, impossible, or unknown.

Use this structure:

```json
{
  "opponent_model": {
    "tier": "hidden_info_belief_state",
    "immediate_punishes": [
      {
        "action": "Fire Blast",
        "holder": "Snorlax",
        "status": "plausible",
        "severity": "kills_only_forretress",
        "evidence": ["fourth move unrevealed", "Forretress invited"]
      }
    ],
    "role_preservation": [
      {
        "piece": "Raikou",
        "role": "special_wall_and_phazer",
        "likely_to_preserve": true
      }
    ],
    "incentives": [
      {
        "if_we_click": "Spikes",
        "opp_best_response_family": ["Curse", "Fire coverage", "switch_to_spinner"],
        "why": "Spikes either fails or gives free setup depending layer count"
      }
    ],
    "hidden_beliefs": []
  }
}
```

## 9. Hidden information without cheating

Represent hidden information with explicit epistemic status:

```json
{
  "hidden_info": {
    "opp_Snorlax_fourth_move": {
      "status": "unknown",
      "possible": ["Earthquake", "Fire Blast", "Lovely Kiss", "Sleep Talk", "Self-Destruct"],
      "impossible": ["Spikes"],
      "likely": ["Earthquake", "Fire Blast"],
      "evidence": [
        "Curse/Rest/Double-Edge revealed",
        "no fourth move revealed after 18 turns"
      ],
      "policy_relevance": "Fire Blast changes whether Forretress can stay in"
    }
  }
}
```

Use these labels:

`confirmed`: directly observed or mechanically implied.

`likely`: supported by set structure, play pattern, or damage.

`plausible`: legal, strategically coherent, and not contradicted.

`thin_plausible`: legal but low-prior or awkward.

`impossible`: illegal under mechanics, contradicted by four revealed moves, contradicted by damage/speed, or impossible under romhack rules.

`unknown`: no responsible inference yet.

The policy must not read hidden oracle fields. In benchmark mode, the public card should include only visible and inferable information. The hidden oracle can contain “actual fourth move,” but the policy never sees it.

Common hidden-info mistakes for an LLM-like agent:

It assumes standard sets as facts.

It treats unrevealed coverage as absent.

It forgets that a revealed three-move set still has a fourth move.

It uses benchmark labels as if they were battle information.

It fails to update after damage reveals a move, item, passive ability, or stat assumption.

It assumes the opponent will preserve or sacrifice pieces according to your plan rather than their incentives.

It treats romhack passives as flavor instead of battle-state modifiers.

It continues a setup script after a miss, wake, switch, or reveal.

It uses species slogans: “Skarmory walls,” “Cloyster Spikes,” “Gengar sleeps,” “Snorlax wins.”

## 10. Worst plausible branch versus average expected branch

Use a risk rule:

```text
Play around a punish when:
  severity is irreversible,
  probability is non-trivial,
  opponent is incentivized to choose it,
  it is legal and consistent with revealed info,
  and the cost of playing around it is acceptable.

Do not play around it when:
  it is low-plausibility,
  inconsistent with prior play or revealed moves,
  the counterplay gives up your own only route,
  or you are already forced to accept risk.
```

A good scoring form is:

```json
{
  "branch_policy": {
    "average_branch_score": 0.62,
    "worst_plausible_branch_score": -0.90,
    "risk_class": "unacceptable_if_avoidable",
    "decision": "reject_move"
  }
}
```

This matters a lot for Explosion. If Explosion wins the average branch but loses instantly to a plausible Ghost switch that the opponent is heavily incentivized to make, it is not automatically a good move. If the Ghost is dead, unrevealed, impossible, or too costly for the opponent to risk, Explosion may become correct.

## 11. Sleep/setup benchmark design

The lesson should be:

> Sleep creates a temporary opportunity, not a script.

Sleep benchmarks should always include at least one re-score trigger: miss, wake, Sleep Talk, switch, phaze, target already statused, sleep clause occupied, or new threat reveal.

Hard sleep/setup variations to create:

1. Sleep clause already used: sleep move becomes no-op or illegal under clause.

2. Target already statused: sleep move fails to create the intended state.

3. Target is likely Sleep Talk user: sleeping it may help less than attacking or switching.

4. Sleep move miss loses tempo: Lovely Kiss / Hypnosis / Sleep Powder miss branch must be priced.

5. Sleep hits but opponent switches: setup line changes because the active target is no longer asleep.

6. Sleep hits but target wakes before second setup turn: agent must stop greed.

7. Sleep Talk calls Rest: the sleeping target heals and resets Rest sleep in GSC. ([Smogon][2])

8. Sleep Talk calls phazing move: if Roar/Whirlwind timing permits, setup may be disrupted.

9. Sleep Talk calls attack: setup sweeper may be damaged into revenge range.

10. Sleeping the wrong target: the true blocker remains awake.

11. Sleeping a Pokémon that wanted Rest anyway: you have not created as much value as the agent thinks.

12. Sleep into Substitute or status-blocking condition.

13. Sleep move PP low: wasting it changes future route.

14. Setup after sleep but opponent has Explosion.

15. Setup after sleep but opponent has healthy phazer.

16. Setup after sleep but Spikes damage changes switch-in math.

17. Sleep target is forced to stay versus can freely switch.

18. Sleep hit creates one-turn attack opportunity, not setup opportunity.

19. Sleep absorber switch is predictable; best move is attack the absorber instead.

20. Miss branch reveals that the sleeper is now too low to keep its role.

The catastrophic pattern is “I slept something, therefore I get to execute my plan.” That is GPT-shaped play. Real play says: “I slept something; now what changed, and what branches remain?”

## 12. Spikes benchmarks: vanilla GSC versus three-layer romhack

Vanilla GSC Spikes policy:

```text
Set Spikes when:
  opponent side has 0 layers,
  the setter has a real opportunity,
  the opponent has grounded switch traffic,
  the setter is not more valuable for another immediate route,
  and you have a plan for Rapid Spin / spinblock / pressure.
```

Vanilla GSC has only one layer. Re-clicking Spikes after that is not “being persistent”; it is a state error. ([Smogon][1])

Romhack three-layer Spikes policy:

```text
Set another layer when:
  current_layers < max_layers,
  the marginal layer changes route value,
  setter survival / opportunity cost is acceptable,
  grounded targets remain,
  removal pressure is understood,
  and the opponent cannot punish the turn harder than the layer is worth.
```

The romhack needs this in mechanics truth:

```json
{
  "mechanics_profile": "romhack_gym_leader_lab",
  "hazards": {
    "spikes": {
      "max_layers": 3,
      "damage_by_layer": {
        "1": "ROMHACK_DEFINED",
        "2": "ROMHACK_DEFINED",
        "3": "ROMHACK_DEFINED"
      },
      "on_side_restart_at_max": "fails_or_no_effect",
      "affected_targets": "grounded_only_unless_delta_says_otherwise"
    }
  }
}
```

Do not hardcode ADV/RSE assumptions unless the romhack actually uses them. Put the damage table in the mechanics profile.

Spikes is not one heuristic. It is a family:

```json
{
  "spikes_policy_features": {
    "current_layers": 2,
    "max_layers": 3,
    "grounded_opp_alive": 4,
    "grounded_opp_forced_switch_frequency": "high",
    "opp_spinner_status": "revealed_alive",
    "our_spinblocker_status": "alive_but_low",
    "setter_survival_after_turn": "survives_common_attack",
    "opportunity_cost": "medium",
    "phazing_support": "Raikou Roar alive",
    "rest_cycle_value": "layer_3_turns_3HKO_into_2HKO",
    "catastrophe_if_click": "opponent can boost to +2"
  }
}
```

Maxed Spikes / fourth-click failure should be a required benchmark class. The benchmark must explicitly show `current_layers == max_layers`, and the policy must classify Spikes as no-effect before considering strategic value.

## 13. Explosion benchmarks

Explosion is not “my Pokémon is low, so boom.” Explosion is a route trade.

A good Explosion removes a piece whose absence opens a route that is more valuable than the user’s remaining role. A bad Explosion removes a replaceable target, gets blocked, sacrifices the only defensive answer, or opens the opponent’s route harder than yours.

GSC Explosion is especially important because Explosion/Self-Destruct halve the target’s Defense, and several relevant Pokémon use Explosion or Self-Destruct to change the course of a game. Smogon’s GSC materials specifically note Forretress’s compression of Spikes, Rapid Spin, and Explosion, while Cloyster cannot legally run Rapid Spin plus Explosion in vanilla GSC. ([Smogon][1])

Explosion benchmark required fields:

```json
{
  "explosion_context": {
    "exploder": "Forretress",
    "exploder_current_roles": [
      {
        "role": "spiker",
        "still_needed": false,
        "reason": "opponent side already has max layers"
      },
      {
        "role": "spinner",
        "still_needed": true,
        "reason": "our side has 1 layer and Zapdos/Marowak route suffers"
      }
    ],
    "target": "Raikou",
    "target_current_roles": [
      {
        "role": "special_wall_and_phazer",
        "blocks_our_route": "Zapdos endgame"
      }
    ],
    "route_opened_by_explosion": {
      "route_id": "zapdos_tbolt_endgame",
      "required_after_boom": [
        "Raikou removed or below 20%",
        "Snorlax kept out of Rest loop",
        "our Zapdos above revenge range"
      ]
    },
    "route_closed_by_explosion": {
      "lost_role": "Rapid Spin access",
      "impact": "acceptable because opponent grounded core now loses to Zapdos pressure"
    },
    "blocked_by": [
      {
        "branch": "Gengar switch",
        "status": "plausible",
        "severity": "catastrophic"
      },
      {
        "branch": "Protect",
        "status": "unknown_romhack_delta",
        "severity": "catastrophic"
      }
    ]
  }
}
```

Explosion is good when the answer contains both:

```text
route opened: what becomes winnable?
route closed: what defensive resource did we give up?
```

If the answer cannot name both, it should not be allowed to call Explosion “good.”

## 14. Defensive-answer preservation

A piece is irreplaceable in a specific state when no other remaining piece can perform its required job under current HP, status, PP, hazards, speed, and hidden-info risk.

Represent it structurally:

```json
{
  "irreplaceable_pieces": [
    {
      "piece": "Skarmory",
      "role": "only_non_explosion_answer_to_curse_snorlax",
      "covered_threats": ["Snorlax"],
      "substitutes": [],
      "minimum_hp_pct_for_role": 37,
      "current_hp_pct": 42,
      "critical_pp": {"Whirlwind": 7, "Rest": 3},
      "hazard_sensitivity": "cannot switch twice through 3-layer Spikes",
      "death_consequence": "Snorlax can Curse/Rest to endgame unless Machamp crit route remains",
      "expendable_if": [
        "Snorlax is removed",
        "Explosion route removes Snorlax",
        "Machamp preserved above Double-Edge range"
      ]
    }
  ]
}
```

A low-HP Pokémon can still be essential if it:

Can switch in once to stop a sweep.

Can revenge kill a specific threat.

Can phaze once.

Can absorb sleep or status.

Can block Rapid Spin.

Can Explode on the one target that matters.

Can force Rest.

Can preserve PP by taking one hit.

Can deny an opponent setup turn by threatening damage.

The agent should never decide expendability from HP alone. Use:

```text
expendable = no live role + no unique route contribution + no needed sack value
```

Not:

```text
expendable = low HP
```

## 15. Rest-cycle reasoning

Rest-cycle benchmarks should test timing, PP, Sleep Talk, wake turns, and punish windows.

Hard cases:

Rest now versus attack now before being forced below range.

Rest too early, giving a setup sweeper two turns.

Rest too late, losing the piece before it can perform its role.

Rest at full HP, which fails under Gen 2 mechanics as implemented in Pokémon Showdown’s Gen 2 data. ([GitHub][3])

Sleep Talk selects Rest and resets sleep.

Sleep Talk selects the wrong move.

Sleep Talk phazing depends on GSC timing.

Sleeping Pokémon can wake and attack on the wake turn in GSC. ([Smogon][2])

Rest PP exhaustion.

Sleep Talk PP exhaustion.

Phazer PP versus setup PP.

Recovery PP versus attacking PP.

Resting into Spikes pressure: the Pokémon wakes but cannot afford the next switch.

Resting a piece that is no longer needed versus preserving a piece that still is.

A Rest benchmark should include:

```json
{
  "rest_cycle": {
    "status": "awake",
    "current_hp_pct": 39,
    "rest_pp": 3,
    "sleep_talk_pp": 8,
    "turns_until_forced_ko_if_no_rest": 1,
    "opponent_setup_punish_if_rest": "Curse to +2",
    "phazer_available_after_rest": false,
    "role_if_rest_succeeds": "continues walling Zapdos",
    "role_if_rest_delayed": "dies to next Thunderbolt"
  }
}
```

## 16. Phazing benchmarks

Phazing benchmarks should test more than “Roar stops setup.”

They should test:

GSC timing: Roar/Whirlwind must go last.

Speed relation: slower phazer may be better under Gen 2 phazing mechanics.

Sleep Talk calling Roar/Whirlwind.

Phazing with Spikes to generate route damage.

Phazing to reveal hidden team members.

Phazing to reset boosts versus attacking to force Rest.

Phazing PP as a finite win condition.

Phazer preservation.

Phazing into a worse threat.

Phazing when the opponent has only one remaining Pokémon, if relevant to the mechanics profile.

Phazing as a way to deny Baton Pass or trap routes.

A good phazing benchmark asks:

```text
Does phaze work mechanically?
Does it deny a live route?
Does it improve our route through hazards/reveal/PP?
What happens if the phazer is chipped or loses PP?
Is attack better because it prevents Rest or KO?
```

## 17. Endgame benchmarks

Endgame cards should be exact. No vibes.

2v2 cards should test forced lines:

```text
Can I win by Rest cycling?
Can I force the last opposing Rest?
Does Explosion trade into the only remaining answer?
Does Spikes on switch decide the endgame?
Is my low-HP piece still required?
```

3v3 cards should test sacrifice legality:

```text
Can I sack A to bring B in safely?
Does sacking A lose the only answer to C?
Does phazing create enough Spikes damage?
Does PP favor me if I avoid unnecessary attacks?
```

4v4 cards should test route selection:

```text
Which of my two win conditions is real?
Which opponent win condition is more urgent?
Can I trade Explosion now?
Do I need to preserve spinner / spinblocker / phazer?
```

Endgame benchmark schema should include:

```json
{
  "endgame_routes": [
    {
      "route_id": "zapdos_clean_after_raikou_removed",
      "owner": "us",
      "required_conditions": [
        "Raikou below 20 or fainted",
        "Snorlax asleep or below 35",
        "Zapdos above Rock Slide range"
      ],
      "blockers": ["Raikou", "healthy Snorlax"],
      "next_required_action": "Explosion on Raikou"
    },
    {
      "route_id": "opp_curselax_endgame",
      "owner": "opponent",
      "required_conditions": [
        "Skarmory below 35",
        "Machamp asleep",
        "Forretress cannot Explode"
      ],
      "blockers": ["Skarmory", "Machamp", "Explosion Forretress"]
    }
  ]
}
```

A simple text field is not enough for win conditions. Use structured route objects, plus an optional human-readable summary.

## 18. Long-game battle ledger

Every turn should produce a ledger entry like this:

```json
{
  "battle_id": "gsc-review-2026-05-13-001",
  "turn": 31,
  "pre_state_hash": "sha256:...",
  "mechanics_profile": "vanilla_gsc",

  "visible_state_summary": {
    "our_active": "Cloyster",
    "opp_active": "Raikou",
    "our_spikes": 1,
    "opp_spikes": 0,
    "key_status": ["opp_Snorlax_asleep", "our_Skarmory_42"]
  },

  "our_routes_before": [],
  "opp_routes_before": [],

  "irreplaceables_before": [],

  "candidate_ranking": [
    {
      "action": "Spikes",
      "rank": 1,
      "reason": "first layer, Raikou likely switches, grounded core high"
    },
    {
      "action": "Explosion",
      "rank": 2,
      "reason": "possible route but premature while Cloyster still needed"
    }
  ],

  "chosen_action": "Spikes",
  "opponent_action": "switch:Starmie",
  "observations": [
    "Starmie revealed as spinner candidate"
  ],

  "posterior_updates": [
    {
      "field": "opp_spinner",
      "old": "unknown",
      "new": "confirmed_alive"
    }
  ],

  "route_delta": {
    "our_route_improved": ["spikes_pressure"],
    "opp_route_improved": ["spin_removal_access"]
  },

  "review_flags": []
}
```

The ledger is how you prevent final-turn blame. A 30-turn loss should be reviewed from the earliest turn where the agent reduced its winning routes or allowed an opponent route that was avoidable with known information.

Review method:

1. Reconstruct the visible state before every turn.

2. Freeze hidden info to what was actually knowable then.

3. Recompute legal/effective actions.

4. Identify route deltas.

5. Find the first turn where the chosen move created an avoidable severe route loss.

6. Ignore later forced losses unless the earlier route loss was unavoidable.

The final losing move is often just the bill coming due.

## 19. Mistake taxonomy

Use labels that point to new tests.

```json
{
  "mistake_labels": {
    "STATE_TRACKING_ERROR": "Forgot or misread HP, status, boosts, hazards, sleep clause, PP, active/bench state.",
    "MECHANICS_ERROR": "Misapplied game rules: Spikes layers, Roar timing, Explosion immunity, Rest failure, Sleep Talk behavior.",
    "HIDDEN_INFO_ERROR": "Assumed unknown info as fact or failed to represent plausible coverage/set/ability.",
    "WIN_CONDITION_ERROR": "Could not name the real route or pursued a route that was already dead.",
    "SACRIFICE_ERROR": "Sacked a piece without proving the remaining route.",
    "OVERFITTED_SCRIPT_ERROR": "Continued a plan after state changed.",
    "SIMULATOR_OVERFIT_ERROR": "Trusted simulator output beyond validated mechanics or assumptions.",
    "RESULT_BASED_REVIEW": "Judged decision by outcome rather than pre-turn information.",
    "PRESERVATION_FAILURE": "Lost or chipped an irreplaceable answer unnecessarily.",
    "ROUTE_CONVERSION_FAILURE": "Had a one-time conversion resource but failed to use it when it opened the route.",
    "PP_ERROR": "Wasted or miscounted critical PP.",
    "DAMAGE_RANGE_ERROR": "Ignored KO/survival range that changed the decision.",
    "ROMHACK_DELTA_ERROR": "Imported vanilla reasoning into a changed mechanics profile."
  }
}
```

Every mistake becomes a regression benchmark like this:

```text
mistake -> extract pre-error state -> hide outcome -> write oracle -> add catastrophe branch -> add one boundary mutation -> add to validation if new family, training if known family
```

Do not write “play more carefully.” Write a card.

## 20. Training, validation, holdout, and anti-overfitting

Split by benchmark family, not by individual card.

Bad split:

```text
train has gsc-spikes-max-001
holdout has gsc-spikes-max-002 with same state and different names
```

Good split:

```text
train has vanilla one-layer Spikes no-op
validation has romhack max-layer no-op
holdout has phaze-plus-max-layer with a different setter and opponent route
```

Workflow:

```text
author benchmark
  -> public card goes to policy
  -> hidden oracle goes to evaluator
  -> policy writes structured answer JSON
  -> evaluator scores move and explanation separately
  -> human reviews failures
  -> failures become new regression cards
  -> mutations generate boundary tests
  -> holdout remains sealed
```

Labels should be hidden from the policy generator and visible only to the evaluator. That is non-negotiable if you care about generalization.

Prevent overfitting by:

Using state mutations where the correct move flips.

Removing benchmark IDs from policy prompts.

Banning rules that reference card IDs.

Testing on species-swapped equivalents.

Testing on mechanic-swapped equivalents.

Testing on boundary states, not just archetypal states.

Scoring explanations for grounded state references.

Keeping a sealed holdout.

Using expert disagreement records instead of flattening every close call into one brittle answer.

## 21. Policy answer schema

The policy answer should include confidence, chosen move, candidate ranking, rejected catastrophic moves, explanation fields, current routes, irreplaceables, and answer-changing info.

Ideal JSON:

```json
{
  "benchmark_id": "gsc-spikes-max-004",
  "policy_version": "baseline_0.3.1",
  "mechanics_profile_seen": "romhack_gym_leader_lab",
  "state_hash": "sha256:public_state_only",

  "decision_status": "action",
  "chosen_action": "Explosion",
  "confidence": 0.78,

  "candidate_ranking": [
    {
      "action": "Explosion",
      "rank": 1,
      "classification": "best",
      "score": 0.78,
      "route_delta": [
        {
          "route_id": "deny_opp_curselax",
          "delta": "major_positive"
        }
      ],
      "risk": [
        {
          "branch": "Ghost switch",
          "status": "low_plausibility_from_visible_state",
          "severity": "high"
        }
      ],
      "reason": "Opponent side already has max Spikes layers, so Forretress no longer advances hazard state. Active +1 Snorlax is the immediate route threat."
    },
    {
      "action": "switch:Skarmory",
      "rank": 2,
      "classification": "acceptable",
      "score": 0.61,
      "reason": "Preserves Forretress but allows Snorlax to continue Rest/Curse pressure."
    },
    {
      "action": "Spikes",
      "rank": 6,
      "classification": "catastrophic",
      "score": -1.0,
      "reason": "Opponent side already has 3/3 layers; fourth click has no useful effect and gives Snorlax a free turn."
    }
  ],

  "current_win_conditions": [
    {
      "route_id": "deny_curselax_then_zapdos_pressure",
      "owner": "us",
      "next_step": "remove_or_cripple_Snorlax",
      "blockers": ["healthy Snorlax"]
    }
  ],

  "irreplaceable_pieces": [
    {
      "piece": "Skarmory",
      "role": "backup Snorlax containment",
      "preserve": true
    }
  ],

  "catastrophe_branches": [
    {
      "action": "Spikes",
      "branch": "Spikes fails; Snorlax Curses again; Skarmory no longer contains safely.",
      "avoidability": "avoidable"
    }
  ],

  "answer_changing_information": [
    {
      "field": "opponent_has_healthy_Ghost_switch",
      "if_true": "Explosion becomes risky; switch or attack may rise.",
      "needed": false,
      "why": "visible state does not show a strong Ghost incentive, but branch is high severity"
    }
  ],

  "rules_fired": [
    "MAX_HAZARD_LAYER_NOOP",
    "IMMEDIATE_SETUP_ROUTE_DENIAL",
    "EXPLOSION_ROUTE_CONVERSION",
    "PRESERVE_BACKUP_SNORLAX_ANSWER"
  ]
}
```

For live play, the agent can output only a move. For training and review, it should always output the structured answer.

## 22. Grading rubric

Score move and explanation separately.

Move score:

```text
best:          1.00
acceptable:    0.70
needs_review:  0.40
wrong:         0.00
catastrophic: -2.00 or automatic severe-fail
missing:       0.00
unknown move:  mechanics fail
```

I would count `acceptable` as a pass for move legality but not as full credit. It should trigger review if the gap between best and acceptable reveals a missing principle.

Explanation score, 10 points:

```text
2 mechanics accuracy
2 route / win-condition clarity
2 catastrophe branch identified
1 hidden-info handling
1 preservation / expendability reasoning
1 answer-changing information
1 groundedness and concision
```

Caps:

If the chosen move is mechanically impossible, explanation score caps at 3.

If it omits an immediate catastrophe branch, score caps at 5.

If it uses hidden oracle information, score is invalid.

If it cannot name a route, score caps at 6 even if the move is right.

`needs_context` is not the same as `acceptable`.

`acceptable` means: “With the provided state, this move is a valid policy choice.”

`needs_context` means: “The public card is missing mandatory information required to choose responsibly.”

A valid `needs_context` answer must name the missing field and the decision flip it controls:

```json
{
  "decision_status": "needs_context",
  "missing": [
    {
      "field": "opp_side.max_spikes_layers",
      "why_required": "Spikes choice differs between 2/3 and 3/3 layers"
    }
  ]
}
```

Do not let `needs_context` become a coward button. If the information is present or the worst plausible branch is already enough to choose, `needs_context` should fail.

## 23. Bad move / good outcome versus good move / bad outcome

Grade from pre-turn visible information.

A good move with a bad outcome:

```text
Sleep Powder was correct because hit branch opened the only route, miss branch was survivable, and alternatives lost to the same threat. It missed. Decision good, outcome bad.
```

A bad move with a good outcome:

```text
Explosion into a plausible Ghost switch was unjustified because the Ghost was revealed and incentivized. Opponent stayed and died. Outcome good, decision bad.
```

The ledger should store:

```json
{
  "decision_quality": "bad",
  "outcome_quality": "good",
  "reason": "opponent failed to take immediate punish"
}
```

That one field prevents result-based learning rot.

## 24. Simulations: useful, but dangerous

Simulations can prove mechanics transitions inside a validated simulator:

```text
At max layers, Spikes produces no new layer.
This damage range has this distribution under these stat assumptions.
This Rest/Sleep Talk interaction occurs in this engine.
```

Simulations can support strategic claims:

```text
With these assumptions, setting layer 2 improves win rate over attacking.
With this branch model, Explosion is positive EV.
```

Simulations cannot prove the best move in real hidden-info play unless the opponent model, mechanics, information state, and route valuation are all correct. That is almost never fully true.

Useful toy simulations:

Spikes marginal value by grounded target count.

Three-layer Spikes versus one-layer Spikes in Rest-cycle pressure.

Sleep hit/miss/wake/setup timing.

Explosion route trade with Ghost/Protect branches.

PP stall endgames.

Phazing loops with hazards.

RestTalk move selection and wake windows.

Spinner/spinblocker hazard retention.

Simulator mismatch ledger:

```json
{
  "mismatch_id": "sim-mismatch-012",
  "mechanics_profile": "romhack_gym_leader_lab",
  "simulator": "custom_gll_sim",
  "version": "0.2.4",
  "observed_in_game": "Fourth Spikes click failed without consuming PP",
  "simulator_result": "Fourth Spikes consumed PP and printed success",
  "impact": "invalidates max_spikes benchmarks",
  "severity": "high",
  "status": "quarantined",
  "fix_required": "update hazard side restart behavior",
  "affected_benchmarks": ["gll-spikes-max-*"]
}
```

## 25. Vanilla GSC to romhack transfer

Do not transfer heuristics. Transfer tested invariants.

A vanilla heuristic can be promoted into the romhack layer only if:

The mechanic it relies on is unchanged or explicitly adapted.

The trigger conditions still exist.

The exception cases have been retested.

At least one romhack benchmark validates it.

At least one boundary mutation flips or preserves the answer as expected.

The delta register says no unresolved conflict.

Quarantine the heuristic as unverified if:

It depends on Spikes layer count or damage.

It depends on type immunities modified by passive abilities.

It depends on Rest, Sleep Talk, Roar, Explosion, Protect, or status behavior that the romhack changes.

It depends on damage thresholds changed by base stats, movepools, items, abilities, or type passives.

It depends on AI/opponent behavior unique to emulator traces.

Dangerous romhack deltas:

Three-layer Spikes.

Passive type abilities.

Changed type chart or type immunities.

Modern abilities inserted into GSC-like pacing.

Changed Explosion behavior.

Changed Sleep Talk / Rest / sleep counter behavior.

Changed Roar/Whirlwind timing.

Changed Rapid Spin behavior.

Changed Protect behavior.

Changed PP.

Changed recovery distribution.

Changed damage formula.

Changed move legality.

Changed hazard groundedness.

Passive type abilities should be represented as first-class mechanics:

```json
{
  "passive_type_ability": {
    "id": "fire_passive_example",
    "holder": "opp_active",
    "visibility": "confirmed",
    "trigger": "on_incoming_move",
    "condition": "move.type == Fire",
    "effect": {
      "damage_multiplier": 0.5,
      "secondary_effect": "none"
    },
    "order": "before_damage_calc",
    "duration": "while_holder_active",
    "policy_relevance": [
      "changes KO range",
      "changes safe switch",
      "changes Explosion route if type-based"
    ]
  }
}
```

Do not bury passives in prose.

## 26. Damage ranges without shallow damage maximization

Damage should appear as thresholds:

```json
{
  "damage_relevance": [
    {
      "move": "Surf",
      "target": "Rhydon",
      "range": "72-85",
      "matters_because": "forces Rest / KO after Spikes"
    },
    {
      "move": "Double-Edge",
      "target": "Skarmory",
      "range": "18-22",
      "matters_because": "does not change Skarmory role this turn"
    }
  ]
}
```

The policy should ask:

Does this damage KO?

Does it force Rest?

Does it put target into Spikes range?

Does it prevent setup?

Does it make Explosion unnecessary?

Does it make a sacrifice legal?

Does it change PP or recovery pressure?

Damage that answers none of those is just noise.

## 27. PP as a win condition

PP should be modeled as route material.

```json
{
  "pp_win_condition": {
    "route_id": "outlast_raikou_roar",
    "owner": "us",
    "critical_pp": [
      {"piece": "Raikou", "move": "Roar", "remaining": 3, "owner": "opponent"},
      {"piece": "Snorlax", "move": "Rest", "remaining": 2, "owner": "opponent"},
      {"piece": "Skarmory", "move": "Whirlwind", "remaining": 5, "owner": "us"}
    ],
    "policy": "avoid unnecessary phaze; force opponent Rest before spending final attack PP"
  }
}
```

PP benchmarks should punish:

Wasting phazing PP.

Wasting recovery PP.

Using low-PP coverage into obvious resist/immunity.

Failing to force Rest when Rest PP is low.

Forgetting that Sleep Talk and Rest interact with PP and sleep timing.

Treating a long endgame as an HP race when it is actually a PP race.

## 28. “So what?” after every move

Every answer should pass this test:

```text
After this move, what concrete route is better?
```

Valid answers:

“Spikes layer 2 makes their Snorlax take enough on future phaze cycles that Zapdos Thunderbolt becomes a 2HKO after Rest.”

“Explosion removes Raikou, the only special wall, so Zapdos becomes the primary route. Forretress’s lost spin role is acceptable because our grounded core is no longer required to switch.”

“Switching preserves Skarmory because it is the only remaining non-crit answer to Curse Snorlax.”

Invalid answers:

“Spikes are good.”

“Explosion creates momentum.”

“Sleep gives free turns.”

“Preserve your walls.”

“Scout to be safe.”

“Attack for damage.”

Those are not policies. Rewrite vague heuristics as:

```yaml
id: use_sleep_to_remove_route_blocker
trigger:
  - sleep_clause_available
  - target_not_statused
  - target_blocks_named_route
  - miss_branch_not_terminal
exceptions:
  - target_likely_sleep_talk_absorber
  - opponent_can_switch_to_sleep_absorber_and_gain
  - immediate_attack_forces_better_state
catastrophe:
  - miss_allows_unanswerable_setup
tests:
  - gsc-sleep-setup-001
  - gsc-sleep-setup-branch-002
```

## 29. Checklists

Before every move, keep it short:

```text
1. Does my intended move work mechanically?
2. What is the opponent’s immediate punish?
3. What are my current winning routes?
4. What opposing route must be denied now?
5. What piece is irreplaceable this turn?
6. Which candidate improves a route, not just a slogan?
7. What new info would flip the answer?
```

After every turn:

```text
1. Update HP, status, boosts, hazards, PP, sleep, screens.
2. Record revealed moves, speed, damage, passives, switches.
3. Update roles: who is now irreplaceable or expendable?
4. Update win routes for both sides.
5. Mark any surprise as hidden-info or mechanics evidence.
6. If the plan changed, re-score. Do not continue script.
```

After every battle:

```text
1. Find the earliest meaningful error.
2. Separate decision quality from outcome quality.
3. Classify the mistake.
4. Extract the pre-error state.
5. Create a regression benchmark.
6. Create one boundary mutation where the answer flips.
7. Update policy rule or mechanics truth.
8. Re-run validation and holdout.
```

## 30. Notebook and artifact structure

The Markdown notebook should stop being a strategy essay. Keep it as an index and policy registry.

Worth keeping:

Mechanics truth summaries.

Policy rule index.

Benchmark taxonomy.

Current mastery gates.

Open questions.

Romhack delta register.

Expert principle notes, clearly marked as hypotheses.

Replace broad prose with:

Benchmark reports.

Mistake ledgers.

Regression cards.

Policy tests.

Simulator mismatch reports.

Battle reviews.

Artifact structure:

```text
project/
  mechanics_truth/
    vanilla_gsc.yaml
    romhack_gym_leader_lab.yaml
    mechanic_unit_tests/

  schemas/
    battle_state.schema.json
    benchmark_public.schema.json
    benchmark_oracle.schema.json
    policy_answer.schema.json
    mistake.schema.json

  benchmarks/
    public/
      train/
      validation/
      holdout_sealed/
    oracle/
      train/
      validation/
      holdout_sealed/

  policies/
    deterministic_baseline/
      rules/
      policy_runner.py
    learned_models/
      README_quarantined_until_ready.md

  policy_answers/
    run_YYYYMMDD_policy_version/

  reports/
    benchmark_reports/
    battle_reviews/
    weekly_reports/

  ledgers/
    mistake_ledger.jsonl
    battle_turn_ledger.jsonl
    simulator_mismatch_ledger.jsonl
    romhack_delta_register.jsonl

  simulations/
    toy_models/
    outputs/
    assumptions/

  docs/
    notebook_index.md
    policy_registry.md
    curriculum.md
```

## 31. Measuring progress without pretending mastery

Win rate matters, but it is a noisy late metric. Track these too:

Mechanics accuracy.

State-tracking accuracy.

Legal/effective move rate.

Catastrophic blunder rate.

Best-or-acceptable benchmark rate.

Holdout generalization.

Branch re-score accuracy.

Hidden-info calibration.

Irreplaceable-piece preservation accuracy.

Route naming accuracy.

Endgame conversion.

PP reasoning accuracy.

Romhack delta error rate.

Earliest-error review accuracy.

Simulator mismatch detection.

Reasonable mastery gates:

```text
mechanics accuracy:
  99%+ on core vanilla tests; 100% on legality/no-op rules before serious play

state tracking:
  98%+ exact on reviewed turns; zero repeated hazard/sleep/status class errors

move-choice quality:
  85%+ best/acceptable on validation; 70%+ on fresh holdout before claiming generalization

severe blunder rate:
  zero on known regression set; less than 1 severe avoidable catastrophe per 50 reviewed turns

hidden-info reasoning:
  90%+ of relevant plausible punishes represented; zero oracle-peeking

long-game planning:
  route object matches expert review on 80%+ of nontrivial turns

endgame conversion:
  85%+ on constructed 2v2/3v3/4v4 endgame cards

romhack transfer:
  separate from vanilla; do not promote until delta tests pass and romhack validation exceeds 75-80%

benchmark generalization:
  performance must hold on mutation families, not just original cards
```

## 32. The smallest next build step

Build a deterministic baseline policy that consumes public benchmark cards and writes policy-answer JSON.

Not because it will play brilliantly. Because it will expose whether your schemas, evaluator, state representation, and mistake loop are real.

The baseline should include:

Mechanics legality filters.

Max Spikes / no-effect filters.

Sleep clause and target-status filters.

Rest full-HP filter.

Explosion Ghost/Protect/plausible-block filters.

Irreplaceable-answer preservation.

Immediate setup catastrophe detection.

Basic route scoring.

Basic hidden-info labels.

Answer-changing info output.

It should avoid:

Species slogans.

Benchmark-ID-specific rules.

Hard-coded exact answers.

“Always set Spikes early.”

“Always preserve walls.”

“Always boom low-HP Pokémon.”

“Always scout unknown coverage.”

“Always attack if in KO range.”

Make it transparent but not brittle by writing generic predicates:

```yaml
predicate: opponent_side.spikes_layers == mechanics.max_spikes_layers
not:
predicate: benchmark_id == "gll-spikes-017"
```

Next after that: add a mutation generator. It should create adversarial variants from each card.

## 33. Adversarial benchmark mutations

From one card, generate mutations that flip the correct move.

Examples:

Sleep clause occupied:

```text
Original: Lovely Kiss best.
Mutation: sleep clause already used.
Expected flip: attack or switch; sleep move catastrophic/no-op.
```

Target already statused:

```text
Original: Sleep Powder best.
Mutation: target paralyzed.
Expected flip: attack, switch, or setup depending route.
```

Spikes layer count changed:

```text
Original: Spikes best at 0/3.
Mutation: opponent side 3/3.
Expected flip: Spikes catastrophic; attack/switch/Explosion rises.
```

Spinner revealed:

```text
Original: set Spikes.
Mutation: Starmie revealed healthy and spinblocker dead.
Expected flip: Spikes lower; pressure spinner or preserve spinblock route.
```

Explosion blocked by Ghost/Protect:

```text
Original: Explosion converts.
Mutation: opponent has revealed healthy Ghost / Protect.
Expected flip: scout, attack, switch, or double.
```

Defensive pivot too low HP:

```text
Original: switch to Skarmory.
Mutation: Skarmory at 18 and dies to entry + hit.
Expected flip: sack different piece or attack now.
```

Opponent coverage revealed:

```text
Original: Forretress can stay.
Mutation: Fire Punch / Fire Blast revealed.
Expected flip: switch or boom.
```

Active slower than assumed:

```text
Original: phaze works / attack first matters.
Mutation: speed relation flips.
Expected flip: phaze may fail or attack loses value.
```

KO range changes:

```text
Original: setup safe.
Mutation: opponent attack now KOs after Spikes.
Expected flip: attack/switch/Rest.
```

Other high-value mutations:

PP low.

Sleep Talk present/absent.

Phazer alive/dead.

Spinblocker alive/dead.

Grounded target count changed.

Passive ability revealed.

Screens active.

Rest PP exhausted.

Explosion user becomes irreplaceable.

Opponent win condition removed.

Boundary cases are gold. Pair cards should explicitly say:

```json
{
  "paired_boundary": {
    "base_card": "gsc-spikes-012",
    "mutation_card": "gsc-spikes-012-m1",
    "minimal_delta": "opp_side.spikes_layers: 2 -> 3",
    "answer_flip": "Spikes -> Explosion",
    "principle": "max hazard layer no-op dominates set Spikes heuristic"
  }
}
```

## 34. Role maps, win conditions, and sacrifice legality

Role maps should be state-dependent:

```json
{
  "role_map": [
    {
      "piece": "Skarmory",
      "role": "Snorlax answer",
      "viability": {
        "can_switch_in_now": true,
        "survives_after_spikes": true,
        "survives_revealed_coverage": "unknown_if_FireBlast",
        "critical_pp_remaining": 7
      },
      "confidence": 0.72
    }
  ]
}
```

Win condition object:

```json
{
  "route_id": "machamp_breaks_curselax_then_zapdos_cleans",
  "owner": "us",
  "route_type": "break_then_clean",
  "primary_piece": "Machamp",
  "secondary_piece": "Zapdos",
  "required_conditions": [
    "Machamp awake",
    "Snorlax below 70 or no Reflect",
    "Raikou removed or below 25",
    "Spikes on opponent side"
  ],
  "blockers": [
    "healthy Raikou",
    "healthy Skarmory",
    "Machamp asleep"
  ],
  "next_actions": [
    "preserve Machamp",
    "force Snorlax Rest",
    "use Explosion on Raikou if opportunity appears"
  ],
  "failure_conditions": [
    "Machamp sacrificed before Snorlax damaged",
    "Zapdos paralyzed and Raikou healthy"
  ]
}
```

Sacrifice is legal only if:

The sacrificed piece has no remaining irreplaceable role, or the role is no longer needed.

The sacrifice creates a forced or strongly favored route.

The remaining opponent routes are still covered.

The resource gained is concrete: free switch, KO, Explosion target removed, Rest forced, PP exhausted, hazard retained.

A “concrete winning route” after a sacrifice is not “we have pressure.” It is a sequence:

```text
Sack Cloyster -> bring Machamp in safely -> Cross Chop forces Snorlax Rest -> Zapdos enters on Rest turn -> Thunderbolt pressure wins because Raikou is gone and Spikes puts Starmie in range.
```

If the route cannot survive one competent opponent response, it is not concrete.

## 35. Snorlax and Snorlax answers

In vanilla GSC, Snorlax is format-warping; Smogon’s dex summary calls it one of the most dominant Pokémon in OU history. ([Smogon][4])

The agent should learn two separate policies:

Preserve own Snorlax when it is your special sponge, RestTalk stabilizer, Curse win condition, Self-Destruct trade, or status absorber.

Preserve Snorlax answers when the opposing Snorlax route is live.

But it must not turn that into “never sack Snorlax” or “always preserve Skarmory.” Snorlax policy depends on set, HP, status, PP, opposing Lax set, phazers, Fighting pressure, Explosion routes, and whether the game is still about Snorlax at all.

Core GSC lessons before romhack transfer:

Mechanics exactness.

One-layer Spikes and hazard retention.

RestTalk pacing.

Sleep as temporary pressure, not guaranteed tempo.

Explosion as route conversion.

Snorlax centrality.

Phazing timing.

PP and long-game resource accounting.

Hidden-info discipline.

Defensive answer preservation.

Route-based review.

The ideas most likely to be distorted by three-layer Spikes and passive type abilities are Spikes value, groundedness, Rest-cycle math, damage thresholds, type-based defensive answers, Explosion routes, and “safe” pivots.

## 36. Testing state re-scoring

Make branch cards where the correct move after the branch differs from the original plan.

Example:

```text
Turn 1: Sleep Powder is best.
Branch A: Sleep Powder hits. Setup is best.
Branch B: Sleep Powder misses and user is chipped. Switch is best.
Branch C: opponent switches to Sleep Talk user. Attack/switch is best.
Branch D: target wakes and phazes. Rebuild route.
```

To detect script-following, require the agent to output:

```json
{
  "rescore_required": true,
  "old_plan_invalidated_by": "Lovely Kiss miss",
  "new_primary_route": "preserve Jynx for later sleep threat",
  "chosen_action": "switch:Snorlax"
}
```

Red flags in explanations:

“Continue the plan.”

“Free turn.”

“Cloyster should set Spikes.”

“Skarmory walls this.”

“Explosion creates momentum.”

“Sleep lets us set up.”

No HP, hazards, PP, status, or route references.

No opponent branch.

No answer-changing info.

No mention of mechanics profile.

Good signs:

Names current route and opponent route.

Mentions exact layer count, sleep clause, HP, status, PP, speed, or boost state.

Names irreplaceable pieces.

Names catastrophe branch.

Explains why a normally good heuristic loses here.

Says what information would flip the answer.

## 37. Expert disagreement

Store disagreement instead of erasing it.

```json
{
  "expert_disagreement": [
    {
      "expert_id": "reviewer_A",
      "preferred": "Explosion",
      "acceptable": ["switch:Skarmory"],
      "reason": "values route conversion before Snorlax reaches +2"
    },
    {
      "expert_id": "reviewer_B",
      "preferred": "switch:Skarmory",
      "acceptable": ["Explosion"],
      "reason": "Ghost branch too costly without more info"
    }
  ],
  "disagreement_axis": "risk tolerance around Ghost switch",
  "grading_policy": "both acceptable; explanation must identify Ghost branch"
}
```

Smogon or expert principles should be treated as hypotheses and priors, not law. For example, Smogon’s Spikes article emphasizes both the importance of Spikes support and the danger of becoming trapped into thinking only about Spikes when the whole position demands another route. That is exactly the kind of principle that should become benchmarked policy, not copied prose. ([Smogon][5])

## 38. Logs and curriculum

Study in this order:

Constructed drills first, because they isolate mechanics and arbitration.

Expert GSC logs second, because they show long-game route management.

Self-play logs third, because they reveal the agent’s actual failure modes.

Romhack emulator traces fourth, because they validate deltas and expose transfer errors.

Do not start with romhack traces alone. The agent will learn fork-specific noise before it has the grammar.

Practical curriculum:

```text
Phase 1: mechanics unit tests
Phase 2: one-turn benchmark cards
Phase 3: branch re-score cards
Phase 4: battle ledger and review
Phase 5: mutation families
Phase 6: expert log annotation
Phase 7: self-play mistake mining
Phase 8: romhack delta transfer
Phase 9: sealed holdout evaluation
```

## 39. The next 20 benchmark cards I would create

1. Sleep clause occupied: agent must not click sleep.

2. Target already paralyzed: sleep move no longer creates opportunity.

3. Sleep move miss branch: setup script becomes unsafe.

4. Sleep Talk absorber switch: best move is attack/pivot, not sleep.

5. Sleep target wakes and phazes: re-score required.

6. Vanilla Spikes at 0 layers: set Spikes is best because grounded switch traffic is high.

7. Vanilla Spikes already set: second click is catastrophic/no-op.

8. Romhack Spikes 1/3: second layer best if setter survives.

9. Romhack Spikes 2/3: third layer versus attack boundary.

10. Romhack Spikes 3/3: fourth-click failure.

11. Spinner revealed, spinblocker alive: set Spikes plus preserve spinblocker.

12. Spinner revealed, spinblocker dead: Spikes value collapses or requires pressure.

13. Forretress Explosion on Raikou opens Zapdos route.

14. Explosion into plausible Ghost switch is catastrophic.

15. Explosion throws away only Snorlax answer.

16. Low-HP Skarmory still irreplaceable against Curse Snorlax.

17. Low-HP Cloyster expendable because Spikes done and Explosion route live.

18. Rest now versus attack now: delaying Rest loses role.

19. Phazing timing: faster Roar/Whirlwind fails under GSC conditions.

20. PP endgame: do not waste final phazing/recovery PP.

## 40. Category ideas and catastrophic patterns

Sleep/setup disruption:

Catastrophic pattern: “sleep landed, continue setup script.”

Spikes and hazard control:

Catastrophic pattern: “set Spikes because Spikes are good,” ignoring layers, spin, grounded count, or immediate punish.

Explosion/sacrifice:

Catastrophic pattern: “low HP means expendable,” without route proof.

Defensive preservation:

Catastrophic pattern: “take value now,” losing only answer to a live threat.

Rest cycles:

Catastrophic pattern: “Rest when low,” ignoring setup punish, full-HP failure, wake timing, or PP.

Phazing:

Catastrophic pattern: “Roar stops setup,” ignoring GSC timing, PP, hazards, and phazer survival.

PP/endgames:

Catastrophic pattern: “click the strongest move,” losing the actual PP route.

Hidden coverage scouting:

Catastrophic pattern: “not revealed means absent.”

Romhack passive type abilities:

Catastrophic pattern: “vanilla type chart says safe,” ignoring passive modifier.

Romhack three-layer Spikes:

Catastrophic pattern: treating layer 1, layer 3, and layer 4 attempts as the same heuristic.

## 41. Long-running weekly loop

A productive weekly loop:

```text
1. Pick one failure theme.
2. Add 5-10 benchmark cards.
3. Add at least one mutation per card.
4. Run deterministic baseline.
5. Run current policy generator.
6. Review catastrophic failures first.
7. Convert each failure into a regression card.
8. Update exactly one policy rule or mechanics truth file.
9. Re-run validation.
10. Touch holdout only on scheduled evaluation.
11. Review one long battle for earliest meaningful error.
12. Update the notebook index and mistake ledger.
```

The loop should never end with “general advice.” It should end with cards, rules, reports, or deltas.

## 42. What to build first, second, third, and what to postpone

First:

State schema, mechanics truth files, hidden-oracle benchmark structure, policy-answer schema, and evaluator.

Second:

Deterministic baseline policy with hard mechanics filters, catastrophe detection, route objects, and structured explanations.

Third:

Mutation generator and branch-tree re-score tests.

Fourth:

Battle ledger and earliest-error review tooling.

Fifth:

Toy simulations for specific mechanics and route questions.

Sixth:

Romhack delta register and transfer tests.

Postpone:

Learned preference models.

Large search.

Self-play optimization.

Automated team-building.

Broad notebook prose.

Claims of mastery.

Deep romhack strategy before the mechanics fork is tested.

The sharp truth: the agent will not become strategically competent because it has more Pokémon wisdom in prose. It will become competent when every slogan is forced to survive contact with state, mechanics, branches, and regression tests.

[1]: https://www.smogon.com/forums/threads/gsc-mechanics.3542417/ "Resource - Gsc Mechanics | Smogon Forums"
[2]: https://www.smogon.com/gs/articles/status "Introduction to Status in GSC - Smogon University"
[3]: https://github.com/smogon/pokemon-showdown/blob/master/data/mods/gen2/moves.ts "pokemon-showdown/data/mods/gen2/moves.ts at master · smogon/pokemon-showdown · GitHub"
[4]: https://www.smogon.com/dex/gs/pokemon/snorlax/?utm_source=chatgpt.com "Snorlax | GS | Smogon Strategy Pokedex"
[5]: https://www.smogon.com/gs/articles/gsc_spikes "Playing with Spikes in GSC - Smogon University"
