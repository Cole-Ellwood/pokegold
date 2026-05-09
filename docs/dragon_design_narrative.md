# Dragon Design Narrative

Status: design intent locked 2026-05-09.
Source of truth for all Dragon-type mechanics in this hack. If gameplay
code conflicts with this doc, fix the code or surface the conflict here.

## The story arc

In vanilla GSC, Clair (final Johto gym) and Lance (Champion) are both
Dragon-type trainers in a row, and the player can wreck both of them
the same way: Ice STAB. The fight feels redundant because the
counter-play is identical and trivial.

This hack reframes that as **deliberate escalation**:

> The last gym is the Dragon trial. The Champion is the Dragon test.

The arc:

1. **Pre-Clair, the player has only weak Dragon access** — Twister (40
   BP, 20% flinch) and Dragonbreath (60 BP, 30% paralysis). These are
   the *anti-Dragon counter-tools* the non-Dragon world developed
   against Dragon defensive resistance-stacking ("Imperial Scales" /
   "dragon's majesty"). They're how the rest of the world fights back.
2. **Clair's Kingdra is built as a wall** — Water/Dragon, weak only to
   Dragon. The player has to beat her *without* Dragon STAB. The whole
   pre-Clair Dragon-access restriction exists to make Kingdra a real
   puzzle, not a free type-chart KO.
3. **Beating Clair grants the holy gift** — TM_OUTRAGE from the
   Dragon's Den. One-time, keystone item. The player is now initiated
   as a Dragon Master.
4. **Lance is the payoff fight** — the player walks in with Outrage
   and finally feels like the Dragon Master themselves, crushing the
   old master with the holy move he gave them the right to wield.
5. **Post-Lance, the Dragon-Master crown is real** — at L55 every
   Dragon learns Outrage via level-up. The player can build a full
   Dragon team for Kanto if they want; the Champion has been *trained*
   in dragons by now.

## Mechanical gates

### "Holy moves" — Dragon-only, no exceptions

| Move | Power | Gate | Mechanism |
|---|---|---|---|
| **Outrage** | 100 BP, 2-3 turn lock + confusion on lock-out | Level-up at **L55** on every Dragon (post-Lance / pre-Kanto-leaders); *plus* one-time TM from Clair after gym victory | TM50 is Dragon-type-restricted (step-3 commit `a10a8454`); level-up entries set per Dragon line |
| **Dragon Dance** | +1 Atk / +1 Spe | Level-up at **L30+** on every Dragon | Level-up move only — never a TM in this hack |

Non-Dragons must not have access to either move — with three named
legendary-flavor exceptions documented below. No other exceptions.

#### Documented exceptions

These three non-Dragon entries are intentional, locked, and not subject
to "is this Dragon-only" audit removals:

| Species | Move | Level | Reason |
|---|---|---|---|
| Kangaskhan | DRAGON_DANCE | L31 | Legacy character move; Kangaskhan's identity as a strong setup attacker predates this hack's Dragon-only rule and the user wants it preserved. |
| Larvitar (line) | DRAGON_DANCE | L15 (Larvitar); inherited by Pupitar/Tyranitar via evolution chain | Legacy character move on the pseudo-legend line. Tyranitar's identity as a setup-sweeper threat depends on it. |
| Arcanine | DRAGON_DANCE + OUTRAGE | L35 / L55 | Singular exception: Arcanine is "legendary enough" in flavor to have learned both holy moves despite reverting to pure Fire typing. The only non-Dragon with both. Preserves Arcanine's existing identity as an apex Fire attacker. |

If a future change wants to grant either holy move to a fourth
non-Dragon, that change is a real design decision and needs to be
documented as a fourth row here, not slipped in as a one-off.

### Anti-Dragon counter-moves — universal but uncommon

| Move | Power | Dragon access | Non-Dragon access |
|---|---|---|---|
| **Twister** | 40 BP, 20% flinch | Known on catch / on evolve (every Dragon) | Uncommon — ~10-20% of non-Dragon roster, thematic anchors only (serpentine, ocean/storm, anti-Dragon archetypes) |
| **Dragonbreath** | 60 BP, 30% paralysis | Level-up in the L30s on every Dragon | Uncommon — same density as Twister, often via TM24 |

"Uncommon" means: the player should occasionally find a non-Dragon
that learns one of these moves and feel a small "oh, that's the
counter-play" beat — but it should not be on every other team. Most
non-Dragons get nothing.

## Why this works

- **Restored danger.** A first-playthrough player who knows vanilla
  GSC expects to walk into Clair with Ice STAB and clean up. Kingdra's
  Dragon-only weakness inverts that. The player has to actually fight,
  not type-chart counter.
- **Earned reward.** Outrage isn't given because you reached a level —
  it's given because you proved you didn't need it. The narrative
  reward feels like an initiation, not a quest unlock.
- **Two-fight escalation, not repetition.** Clair and Lance feel
  *different* because the player's toolkit changes between them. The
  same trainer-archetype repeated becomes a deliberate before-and-after
  shot.
- **Rare elite type.** Dragons stay scary because they're not common.
  The player meets a few before Clair and the encounters feel
  meaningful precisely because the player has limited counter-play.

## Dragon roster

The 9 Dragon-types in this hack (as of 2026-05-09):

| Species | Typing | Notes |
|---|---|---|
| Dratini | Dragon | Canonical line — Dragon's Den gift / encounter |
| Dragonair | Dragon | L55 evolve into Dragonite (per existing `balance_intent.md` row) |
| Dragonite | Dragon/Flying | Canonical pseudo-legend |
| Kingdra | Water/Dragon | Clair's wall: only weak to Dragon |
| Gyarados | Water/Dragon | Was Water/Flying in vanilla |
| Ampharos | Electric/Dragon | Was pure Electric |
| Steelix | Steel/Dragon | Was Steel/Ground (step 2 retype) |
| Yanma | Bug/Dragon | Was Bug/Flying (2026-05-09 retype); fast pivot, not heavy attacker |

Arcanine reverted to pure Fire 2026-05-09 — it had been Fire/Dragon
but did not fit the "rare elite type" goal at 615 BST.

## Implementation status

| Item | State | Where |
|---|---|---|
| Outrage at 100 BP, 2-3 turn lock + confusion | done | `data/moves/moves.asm` |
| TM_OUTRAGE = TM50, Dragon-only restriction | done | step-3 commit `a10a8454` |
| Clair gives TM_OUTRAGE in Dragon's Den | done | `maps/DragonsDenB1F.asm` (per step-3 trainer-roster diffs) |
| Outrage level-up at L55 on every Dragon | TODO | `data/pokemon/evos_attacks.asm` |
| Dragon Dance level-up at L30+ on every Dragon | partial — Steelix L35 done; Dratini line, Kingdra, Gyarados, Ampharos, Yanma TBD | `data/pokemon/evos_attacks.asm` |
| Twister at L1 on every Dragon (knows on catch/evolve) | TODO | `data/pokemon/evos_attacks.asm` |
| Dragonbreath in L30s on every Dragon | TODO | `data/pokemon/evos_attacks.asm` |
| Non-Dragon Twister/Dragonbreath access set to "uncommon" density | TODO — currently TM24 is universal | `data/pokemon/base_stats/*.asm` |
| Audit script enforcing all of the above | TODO | new `tools/audit/check_dragon_holy_moves.py` |
| Clair roster all-Dragon, no non-Dragon filler | TODO | `data/trainers/parties.asm` |
| Lance roster all-Dragon, more intimidating than Clair, kill the Gligar copy-paste | TODO | `data/trainers/parties.asm` |
