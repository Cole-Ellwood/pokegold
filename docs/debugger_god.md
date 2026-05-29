# Debugger "God" — operational playbook

This is the working answer to Cole's ask: *"any weird thing I experience while
playing, you use God and find it immediately; I ask you to change something, God
tells you every consequence."*

What "God" is, concretely: the unified `tools/debugger` surface, matched to the
**live dev-tip ROM** (selftest 31/31, ROM SHA1 identical to `roms.sha1`). It does
not edit the ROM — it reads, reproduces, localizes, explains, and names the proof
gates. It is honest about what it cannot see.

Two ground truths set the ceiling, stated up front so nothing here over-promises:

- **Repro needs a handle.** "Find it immediately" works when you hand over a save
  state at/near the moment (VBA-M `.sgm` or a `.sav`), or an input log. With only a
  description, God localizes by symptom but cannot *prove* the live cause.
- **PyBoy is not VBA-M.** God executes in PyBoy; you play in VBA-M. Some VBA-only
  artifacts (the tile-jumble class) will not reproduce in PyBoy. `crossemu` is the
  divergence guard, but it is a check, not a guarantee.

---

## Scenario A — "I saw something weird while playing"

**You do:** in VBA-M, make a save state (`.sgm`) as close to the moment as you can,
and tell me one sentence about what looked wrong. Drop the `.sgm` path in chat.

**I do**, in rough order:

1. **Route the symptom.** `python -m tools.debugger investigate --symptom "<your sentence>"`
   — picks the right subsystem and proof path. Or `triage --symptom "..."` for just
   the routing.
2. **Inspect the captured state.** `save-state-lab inspect <bug.sgm>` — decodes the
   `.sgm`, reads CPU + the live WRAM window, and flags impossible script-VM / crash
   states (the post-battle/evolution freeze class). Fails closed on untrusted `.sgm`
   decoding rather than guessing.
3. **By symptom class:**
   - *Graphics / palette / tile glitch* → `vram-snapshot --decode --save-state bug.sgm`,
     then `vram-diff bug.sgm good.sgm` for a structured tile/OAM/palette delta. If it
     reproduces in PyBoy, `crossemu` confirms whether it is a real ROM bug or a
     VBA-only artifact.
   - *Wrong number (damage, stat, level)* → `when-wrote <symbol>` / `reverse-query
     --symbol <symbol>` to find what produced the value; for damage specifically,
     `tools.damage_debugger`.
   - *Softlock / frozen / music-keeps-playing* → `save-state-lab` for the script-VM
     crash signature, then `watch --watch-symbol wScriptBank --watch-symbol wScriptPos
     --save-state <before>.sgm --execute`.
   - *Boss did something dumb* → `tools.boss_ai_debugger` (matched to this ROM).
4. **Localize + explain.** `localize --symbol <s>` ranks suspects; `explain` builds the
   causal path from the runtime evidence to source `file:line`.
5. **Prove it.** The above commands print the exact `watch` / `trace-instructions
   --require-hit` / `dynamic-taint` command that turns a hypothesis into ROM-backed proof.

**Unsolicited surfacing:** `auto-watch` flags resulting bug classes on the next build,
so I am not always waiting for you to notice — it answers "did the last change break
something?" on every code landing.

---

## Scenario B — "I want to change X — what breaks?"

**Command:** `python -m tools.debugger consequence --symbol <LABEL>` (or
`--file <path>`).

It returns, for that edit:

- **Forward register ABI** (if a function) — which registers it clobbers, its calls/rets,
  push/pop pairs, and any opaque branches.
- **Static reference closure** — how many readers/writers/callers and which files the
  edit ripples into.
- **Hazard gates to run as proof** — the specific `tools/audit/check_*.py` /
  `clobber_smoke` that catch this repo's known failure classes (the 5x-damage register
  clobber, the farcall hl/a clobber, cross-bank calls, save-format breakage, …).
- **A balance `data_delta` note** for stat/move/roster/encounter edits — mechanical
  damage/stat deltas are computable (regen commands listed); gameplay *feel* stays your
  taste call, never auto-derived.
- **BLIND SPOTS** — printed every time. Indirect jumps, computed WRAM addresses, UNION
  aliasing, data-as-code, runtime bank state. With the dynamic commands that close them.

So `consequence` is **exhaustive over the known failure classes plus the static
reference set, never a completeness proof.** "Every consequence" in the literal sense
is unattainable for hand-written SM83 — this gives you the derivable consequences and
honestly names the rest.

---

## Honest gaps

- **Dev-tip verbs: all restored.** The harvest initially dropped 9 dev-tip verbs;
  they are now re-wired and working: `party-inspect`, `learnset-inspect`,
  `grass-regrowth`, `script-resume-gate` (post-battle/evolution freeze detector),
  `wram-ownership` / `wram-lifetime` / `wram-bank-hazards`, `repro-recipe`, and
  `next` (proof-step routing). `state-inspect` is superseded by `save-state-lab`;
  `prove` was a master-lineage verb never on this dev tip. So God is a superset of
  the dev-tip debugger plus the ~25 masterpiece verbs.
- **Two packages kept at dev-tip level on purpose:** `tools/trace` (`read_word`
  endianness) and `tools/damage_debugger` (taint) — masterpiece improved both, but
  those packages stay matched to the live ROM (a ROM-mismatched debugger lies).
  Two tests are skipped with that documented reason; they re-enable if those
  packages are harvested.
- **Branch state.** This lives on `claude/debugger-god-integration` (off the dev tip),
  unmerged. Merging to the dev line is a release-class event and stays a manual gate.

## Quick reference

```
python -m tools.debugger session-start                 # fresh-session orientation
python -m tools.debugger investigate --symptom "..."   # route a symptom -> proof path
python -m tools.debugger save-state-lab inspect x.sgm  # decode a VBA-M crash state
python -m tools.debugger vram-diff bug.sgm good.sgm    # structured graphics delta
python -m tools.debugger when-wrote <symbol>           # what produced this value
python -m tools.debugger consequence --symbol <LABEL>  # what breaks if I change this
python -m tools.debugger selftest                      # 31/31 health gate
```
