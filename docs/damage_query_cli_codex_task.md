# Damage Query CLI — Codex Task Spec

> The damage debugger's `oracle.predict_damage` gives ROM-true Gen 2
> damage numbers (with all this hack's modifiers — Imperial Scales,
> Dragon's Majesty, Sharp Beak, Choice items, Expert Belt, etc) — but
> there is no quick CLI for "what's the damage of move X by attacker A
> against defender B?" Today every check requires a 30-line Python
> heredoc that hand-looks-up base stats from
> `data/pokemon/base_stats/<species>.asm`, move BP from
> `data/moves/moves.asm`, the `HELD_*` constant for any item, and
> manually computes computed-stats via the Gen 2 formula. That takes
> several minutes per query and most of it is discovery, not damage.
>
> This task ships `tools/damage_debugger/matchup.py` — a CLI wrapper
> over `oracle.predict_damage` that auto-looks-up everything from
> source-of-truth files and turns a damage check into a 10-second
> command. Same ROM-true math, zero discovery overhead.

## Execution shape

This task runs as 4 ordered steps (A → B → C → D). Codex executes all
four in one pass without stopping between them.

### STEP A — Worktree setup (BEFORE any file edit)

Run these commands first, exactly as written:

```bash
git fetch origin
git worktree add .claude/worktrees/codex-damage-query-cli origin/codex/cleanup-gsc-rebalance-split
cd .claude/worktrees/codex-damage-query-cli
cp -r ../../../rgbds-1.0.1 .
git rev-parse HEAD
git rev-parse origin/codex/cleanup-gsc-rebalance-split
```

The two `git rev-parse` outputs MUST match. If they do not, the
worktree is on a stale base and Codex must rerun.

THEN, before any file edit, print this **four-check report** so the
user can spot a misplacement before any commit:

```bash
pwd
git branch --show-current
git rev-parse HEAD
ls tools/damage_debugger/oracle.py
```

Required state:
- `pwd` ends in `.claude/worktrees/codex-damage-query-cli`
- branch is the auto-named codex worktree branch (NOT
  `codex/cleanup-gsc-rebalance-split` directly, NOT any pre-existing
  codex branch)
- `git rev-parse HEAD` matches
  `git rev-parse origin/codex/cleanup-gsc-rebalance-split`
- `tools/damage_debugger/oracle.py` lists

ALL subsequent work happens inside this worktree.

### STEP B — Reading

Before doing anything else, read:

- [`docs/codex_playbook.md`](codex_playbook.md) §1, §2, §2.3.
- [`tools/damage_debugger/oracle.py`](../tools/damage_debugger/oracle.py)
  — specifically the `BattleInputs` dataclass (~line 233) and
  `predict_damage` (~line 770). The CLI is a thin wrapper over
  `predict_damage`, so the input fields determine the CLI surface.
- [`tools/damage_debugger/README.md`](../tools/damage_debugger/README.md)
  to see the existing CLI surface (`clobber_smoke`, `fuzz`, `find`).
  The new tool is one more entry point on the same `python -m
  tools.damage_debugger.<name>` pattern.
- [`docs/mechanics_changes_from_base.md`](mechanics_changes_from_base.md)
  to understand what passives the oracle already models (Imperial
  Scales, Dragon's Majesty, type passives, etc) — these are
  load-bearing for hack-accurate output.

### STEP C — Execution

Run the 5 sub-steps in [Steps](#steps) below, in order.

### STEP D — Ship

Merge to dev tip via the playbook §2.3 commit-tree pattern. Final
merge commit body has the bug-check Findings report (§1.1 format),
including a sample CLI invocation + output, the auto-lookup design
notes, and audit results.

---

## Background

**Goal**: turn this 30-line Python heredoc:

```python
from tools.damage_debugger.oracle import BattleInputs, predict_damage, FLYING, POISON, PSYCHIC_TYPE, HELD_SHARP_BEAK, HELD_NONE
inp = BattleInputs(
    attacker_level=44, move_bp=80, move_type=FLYING, is_physical=True,
    attacker_atk=117,    # had to compute from base 120, IV 8, no EV, L44
    defender_def=78,     # had to compute from base 45, IV 13, partial EV, L44
    attacker_types=(POISON, FLYING),
    defender_types=(PSYCHIC_TYPE, PSYCHIC_TYPE),
    user_item=HELD_SHARP_BEAK, opponent_item=HELD_NONE,
    battle_turn=1,
)
print(predict_damage(inp))
```

into this one-liner:

```bash
python -m tools.damage_debugger.matchup CROBAT:44 ALAKAZAM:44 WING_ATTACK \
    --user-item sharp_beak --defender-grind mid --defender-hp 51
```

producing:

```
Wing Attack (Crobat L44 trainer, Sharp Beak) vs Alakazam L44 (mid-grind, 51% HP)
  damage roll:    71-84  (low: 71, max: 84)
  % of full HP:   51-60%  (max HP = 140)
  % of current HP: 100-118%  (current HP = 71)
  KO at current HP: GUARANTEED  (low roll = 100%)
  KO at full HP:   NEVER  (max roll = 60%)
  crit (×2 base):  142-168  (full HP: 101-120%, current: 200-237%)
```

The CLI does ALL the discovery work that today's heredoc requires the
human (or Claude) to do by hand:

1. **Base stats lookup**: parse `data/pokemon/base_stats/<species>.asm`
   to extract the 6-stat line and the type pair.
2. **Move data lookup**: parse `data/moves/moves.asm` to find the
   move's BP, type, and effect (for `is_physical` — Gen 2 categories
   are by attacking type, see `oracle.predict_damage`'s usage).
3. **Item name → HELD_* mapping**: take a friendly name like
   `sharp_beak` / `Sharp Beak` / `SHARP_BEAK` and resolve it to the
   numeric HELD_* constant the oracle expects.
4. **Stat computation**: apply the Gen 2 formula
   `((Base + IV) * 2 + StatExp_term) * Level / 100 + 5` (HP adds
   `+ Level + 10`) using grind presets.
5. **Damage variation**: the oracle returns max-roll damage; the CLI
   shows the full roll range by computing `low = max * 217 // 255`.

**Critical constraint**: the CLI must NOT reimplement the damage
math. It MUST call `oracle.predict_damage` for the actual numbers.
Re-implementing the Gen 2 formula would silently drift from the ROM
when the oracle gets updated for new mechanics (next hack feature,
new passive, etc).

---

## Files to investigate

- `tools/damage_debugger/oracle.py` — `BattleInputs` dataclass +
  `predict_damage` + constant exports (FLYING, POISON, PSYCHIC_TYPE,
  HELD_SHARP_BEAK, HELD_CHOICE_BAND, etc).
- `data/pokemon/base_stats/<species>.asm` — per-species base stats and
  type pair (~250 files, but the parse is uniform).
- `data/moves/moves.asm` — move table; each row is
  `move NAME, EFFECT, BP, TYPE, ACCURACY, PP, EFFECT_CHANCE`.
- `data/items/attributes.asm` — per-item attributes; the relevant
  field is the `held_item` byte that gives the `HELD_*` constant for
  the item.
- `constants/type_constants.asm` — type ordinals (POISON, FLYING,
  PSYCHIC_TYPE, etc) used by `BattleInputs.attacker_types`.
- `constants/item_data_constants.asm` — `HELD_*` constant ordinals,
  for the name-to-number map.
- `constants/move_constants.asm` — move name → ordinal (used to
  cross-reference `data/moves/moves.asm` rows with the move name the
  user types).

The tool reads these files at import time (or lazily) and caches the
parsed tables in module-level dicts.

---

## Steps

### Step 0 — Design the CLI surface

```
python -m tools.damage_debugger.matchup ATTACKER DEFENDER MOVE [options]

ATTACKER, DEFENDER:
  Format: <SPECIES>:<LEVEL>  (level 1-100, species by RGBDS constant
  name like CROBAT, ALAKAZAM, BLASTOISE)
  Optionally: <SPECIES>:<LEVEL>:<role> where role is "trainer" (IV 8,
  no EVs — Gen 2 NPC default) or "player" (configurable via
  --grind below).
  Default for ATTACKER: "trainer"
  Default for DEFENDER: "player"

MOVE:
  RGBDS constant name (WING_ATTACK, EARTHQUAKE, ICE_BEAM, etc).
  Case-insensitive but underscored (wing_attack OK, "Wing Attack" OK
  via lookup).

Options:
  --user-item NAME        Item the attacker holds. NAME is friendly
                          name (sharp_beak / "Sharp Beak" / SHARP_BEAK),
                          all map to the underlying HELD_* constant.
  --opponent-item NAME    Item the defender holds.
  --user-grind {low,mid,high,max}      Player IV/EV grind for attacker
                          when role is "player". Default: mid.
                          Presets:
                            low:  IV 8, no EVs (StatExp_term = 0)
                            mid:  IV 13, partial EVs (StatExp_term = 30)
                            high: IV 15, near-max EVs (StatExp_term = 50)
                            max:  IV 15, max EVs (StatExp_term = 64)
  --defender-grind {low,mid,high,max}  Same for defender.
  --defender-hp PERCENT   Defender's current HP as percentage of max
                          (1-100). Default: 100. Affects KO calc.
  --crit                  Force critical hit. Default: false.
  --weather {none,rain,sun,sandstorm,hail}
                          Weather. Default: none.
  --turn {auto,player,enemy}
                          Battle turn. Default: auto (enemy if
                          attacker is "trainer", player otherwise).
  --json                  JSON output instead of text. Schema must be
                          stable for downstream tooling.
  --trace                 Show damage at each step boundary
                          (DamageStats / DamageCalc / Stab / TypeMatchup
                          / TypePassive). Wraps
                          `oracle.predict_damage_trace`.

Exit codes: 0 success, 1 input error (bad species/move/item name),
2 internal error.
```

### Step 1 — Build the data loaders

Three lazy-loaded module-level loaders (cached after first call):

1. `_load_base_stats() -> dict[str, BaseStatsRow]`
   Returns mapping `species_name -> (hp, atk, def, spe, sat, sdf,
   type_a, type_b)`. Walks `data/pokemon/base_stats/*.asm`. Parses
   the 6-stat `db` line and the type pair line. Skips egg/dummy.

2. `_load_moves() -> dict[str, MoveRow]`
   Returns mapping `move_name -> (effect, bp, type_name, accuracy,
   pp, effect_chance)`. Parses `data/moves/moves.asm` lines that
   begin with `\tmove `.

3. `_load_held_item_constants() -> dict[str, int]`
   Returns mapping `friendly_name -> int` for HELD_* constants. Two
   sources to merge:
     a. `constants/item_data_constants.asm` — gives ordinals
        for HELD_NONE, HELD_BERRY, ..., HELD_CHOICE_BAND, etc.
     b. `data/items/attributes.asm` — gives item NAME →
        HELD_* mapping (so user can type "Sharp Beak" or "sharp beak"
        and get the right HELD_ constant).
   The CLI accepts any of: friendly item name (Sharp Beak),
   underscored (sharp_beak), or HELD_* constant name (HELD_SHARP_BEAK).

Each loader has a `--self-test` mode: load the table, assert key
known values (e.g., `_load_base_stats()["CROBAT"]` returns
`(100, 120, 105, 130, 70, 80, "POISON", "FLYING")` — source of
truth: `data/pokemon/base_stats/crobat.asm` at HEAD).

### Step 2 — Build the stat computer

```python
def compute_stat(base: int, level: int, iv: int, statexp_term: int,
                 is_hp: bool) -> int:
    """Gen 2 stat formula — see CLAUDE.md "Stat math" section."""
    inner = ((base + iv) * 2 + statexp_term) * level // 100
    return inner + level + 10 if is_hp else inner + 5
```

Grind presets — pick reasonable values; tune if the user pushes back:
- `low`:  IV 8,  StatExp_term = 0   (no investment)
- `mid`:  IV 13, StatExp_term = 30  (partial grind)
- `high`: IV 15, StatExp_term = 50  (near-max)
- `max`:  IV 15, StatExp_term = 64  (max EV cap, sqrt(65535)/4 ≈ 64)

Trainer profile is fixed: IV 8, StatExp_term = 0 — Gen 2 NPCs don't
have EVs.

### Step 3 — Wire it together

```python
def run_matchup(args) -> MatchupResult:
    base_stats = _load_base_stats()
    moves = _load_moves()
    held_items = _load_held_item_constants()
    types = _load_type_constants()  # from constants/type_constants.asm

    atk_species = base_stats[args.attacker_species]
    def_species = base_stats[args.defender_species]
    move = moves[args.move]

    # Compute stats.
    atk_iv, atk_statexp = _grind_to_iv_ev(args.user_role, args.user_grind)
    def_iv, def_statexp = _grind_to_iv_ev(args.defender_role, args.defender_grind)

    is_physical = _move_category(move)  # by attacking type, Gen 2 rule
    atk_stat = compute_stat(
        atk_species.atk if is_physical else atk_species.sat,
        args.attacker_level, atk_iv, atk_statexp, is_hp=False,
    )
    def_stat = compute_stat(
        def_species.def_ if is_physical else def_species.sdf,
        args.defender_level, def_iv, def_statexp, is_hp=False,
    )
    def_max_hp = compute_stat(
        def_species.hp, args.defender_level, def_iv, def_statexp,
        is_hp=True,
    )

    # Build BattleInputs.
    inp = BattleInputs(
        attacker_level=args.attacker_level,
        move_bp=move.bp,
        move_type=types[move.type_name],
        is_physical=is_physical,
        attacker_atk=atk_stat,
        defender_def=def_stat,
        attacker_types=(types[atk_species.type_a], types[atk_species.type_b]),
        defender_types=(types[def_species.type_a], types[def_species.type_b]),
        user_item=held_items.get(args.user_item, HELD_NONE),
        opponent_item=held_items.get(args.opponent_item, HELD_NONE),
        is_critical=args.crit,
        weather=_weather_to_int(args.weather),
        battle_turn=_turn_to_int(args.turn, args.attacker_role),
        # ...other defaults
    )

    max_damage = predict_damage(inp)
    min_damage = max_damage * 217 // 255
    current_hp = def_max_hp * args.defender_hp // 100

    return MatchupResult(
        damage_low=min_damage, damage_high=max_damage,
        defender_max_hp=def_max_hp, defender_current_hp=current_hp,
        ko_at_current=min_damage >= current_hp,
        ko_at_full=min_damage >= def_max_hp,
        crit_low=..., crit_high=...,
    )
```

### Step 4 — Implement output formatters

Two output paths: text (default) and JSON (`--json`).

**Text format** — see the example in [Background](#background)
above. Show damage range, % of current HP, % of full HP, KO chance
at current and full, plus crit damage if non-crit was the default.

**JSON format**:

```json
{
  "matchup": {
    "attacker": {"species": "CROBAT", "level": 44, "role": "trainer", "atk_stat": 117, "types": ["POISON", "FLYING"]},
    "defender": {"species": "ALAKAZAM", "level": 44, "role": "player", "def_stat": 78, "types": ["PSYCHIC_TYPE", "PSYCHIC_TYPE"], "max_hp": 140, "current_hp": 71},
    "move": {"name": "WING_ATTACK", "bp": 80, "type": "FLYING", "is_physical": true},
    "items": {"user": "HELD_SHARP_BEAK", "opponent": "HELD_NONE"},
    "weather": "none", "crit": false, "battle_turn": "enemy"
  },
  "result": {
    "damage_low": 71, "damage_high": 84,
    "pct_of_current_hp_low": 100, "pct_of_current_hp_high": 118,
    "pct_of_max_hp_low": 51, "pct_of_max_hp_high": 60,
    "ko_at_current_hp_guaranteed": true, "ko_at_max_hp_guaranteed": false,
    "crit_damage_low": 142, "crit_damage_high": 168
  }
}
```

### Step 5 — Self-tests + audit

Add a `--self-test` mode that runs ~5 known matchups and asserts
known damage values. Pinned to current HEAD's source-of-truth files
(base stats + moves + items). If any of those change, the self-test
breaks loudly. Required scenarios:

1. **The motivating case** — Crobat L44 (trainer, Sharp Beak) Wing
   Attack vs Alakazam L44 (player, mid-grind). Assert damage range
   71-84 (this is the Koga fixture answer the user just verified).
2. **Vanilla-baseline sanity** — a matchup with no held items, no
   weather, neutral type. E.g., Pikachu L20 Tackle vs Squirtle L20.
   Assert against hand-computed expected.
3. **Imperial Scales** — Suicune L42 (player, max) Surf vs Dragonite
   L42 (trainer, no item). Assert damage scales by ×0.5 type ×2/3
   Imperial Scales (the matchup the user just analyzed in the Clair
   fixture).
4. **Dragon's Majesty** — Ampharos L40 Thunder vs Piloswine L40.
   Without DM, Ground would be 0× Electric → 0 damage. With DM,
   Electric becomes 0.5× — the move now does damage.
5. **Choice Band** — physical attacker holding Choice Band; assert
   ×1.5 attack stat shows up in damage.

Add a static audit `tools/audit/check_matchup_cli.py` that runs
`--self-test` and exits 1 on regression. Wire into release-smoke
floor (add to `check_release_smoke.py`'s sub-audit list).

---

## Acceptance criteria

- [ ] `tools/damage_debugger/matchup.py` exists, importable as
      `python -m tools.damage_debugger.matchup --help`.
- [ ] CLI accepts `ATTACKER:LEVEL DEFENDER:LEVEL MOVE` positional args
      plus the option set in [Step 0](#step-0--design-the-cli-surface).
- [ ] All five auto-lookup paths work without user-supplied numerics:
      base stats, types, move BP/type, held item name → HELD_* int,
      stat computation by grind preset.
- [ ] Default text output matches the format shown in
      [Background](#background) (damage range, % of full/current HP,
      KO booleans, crit row).
- [ ] `--json` produces the schema in [Step 4](#step-4--implement-output-formatters).
- [ ] `--trace` shows per-step damage from `predict_damage_trace`.
- [ ] `--self-test` runs the 5 scenarios and exits 0; tampering with
      one expected value makes it exit 1.
- [ ] `tools/audit/check_matchup_cli.py` exists, runs the self-test,
      and is listed in `check_release_smoke.py`.
- [ ] `python -m tools.damage_debugger.matchup CROBAT:44 ALAKAZAM:44
      WING_ATTACK --user-item sharp_beak --defender-grind mid
      --defender-hp 51` produces the motivating-case output (damage
      71-84, KO at 51% guaranteed).
- [ ] No reimplementation of the Gen 2 damage formula. CLI delegates
      all damage math to `oracle.predict_damage` /
      `oracle.predict_damage_trace`.
- [ ] `make compare` byte-identical to dev tip (Python-only change;
      ROM unchanged).
- [ ] Final merge commit body has §1.1 Findings: sample invocation +
      output, list of auto-lookup paths, audit results.

---

## Scope boundaries / Do NOT

- Do NOT change `oracle.py` damage logic. The CLI is a thin wrapper.
- Do NOT cache damage results between runs — the lookup tables can be
  cached at module level, but each `predict_damage` call is fast
  enough to run on every invocation.
- Do NOT add interactive prompts. CLI should be one-shot, fully
  scriptable.
- Do NOT add support for legacy/Gen-1 type chart or Gen-3+ phys/spec
  split. This is a Gen 2 hack.
- Do NOT overload existing `tools.damage_debugger.find` semantics.
  This is a separate `matchup` entry point with a different purpose
  (quick query, not divergence diagnostic).
- Do NOT modify CLAUDE.md, the codex playbook, or any handoff docs.
- If any of the auto-lookup paths returns ambiguous results (move
  name collision, item name collision), fail fast with a clear error
  message — don't silently pick one.
- If the oracle-required field set drifts (new BattleInputs field
  added that the CLI doesn't expose), surface that gap in Findings
  rather than silently default it.
- Aim for **<300 lines** of CLI Python (excluding loader cache code).
  Most lines are arg parsing + output formatting; the actual damage
  call is one line.
