# Heuristic: Role Package Ledger

Status: live tiny card.

Use when: a revealed move, voluntary entry, or repeated switch changes what a
Pokemon is doing for its team.

Rule: update the public job before ranking moves.

Ask:
- What package is now public: screen, Charm/Pursuit, trap/perish, phaze,
  Spin, Curse wall, RestTalk, lure coverage, lead item/status, pass receiver,
  cleric?
- For trap/perish, is the target actually held, or can it switch, pass, phaze,
  or KO the trapper before the count converts?
- If Perish Song starts before Mean Look, is it forcing a receiver that can be
  trapped next turn, and is the exit plan already named?
- Which next owner does that package enable, deny, or invite?
- If this is a lead item/status package, what absorbs the job and who enters
  after the job succeeds?
- If RestTalk is public, is its job pressure, sleep-turn absorbing, or pivoting?
- What does each revealed or strong-prior Sleep Talk roll do to the proposed
  absorber?
- If a Pokemon enters into a live sleep move, is its job to take sleep, stay
  via revealed Sleep Talk, or leave after Sleep Clause is active?
- After Lovely Kiss or another sleep reveal, is the package now sleep pressure
  plus a low-HP cash-out such as Self-Destruct or Explosion?
- If a sleeping RestTalk user can act, is Sleep Talk better than preserving it
  with an owner that absorbs the revealed attack?
- If lead Jynx has landed sleep, is Thief now part of the public/strong-prior
  package, and which lower-value item holder absorbs it?
- If Growth plus Baton Pass is live, who owns the boost, who can receive it,
  and which receiver survives the revealed or strong-prior immediate rolls?
- If AgilityPass is live, is the answer phaze, Reflect/status, Encore, or
  active damage, and which receiver does that answer beat?
- If a Pokemon voluntarily enters a threat, is it direct coverage, absorber,
  or bait-handoff into the real owner?
- In opening lead cycles, did a voluntary double-switch reveal a hard-answer
  chain that should be priced by class before default scripts?
- If a spiker enters into its support job, have Spikes/Toxic plus cash-out or
  Spin been priced before a valuable route piece attacks it?
- If Protect or Rest is revealed on a stall piece, is it scouting sleep/coverage
  or preserving a route job while poison, Spikes, or Rest pressure converts?
- Can a statused absorber own the hazard-tempo turn by blanking status while
  preserving the spinner, setter, or phazer for the later reset loop?
- Does a typed or status-tolerant absorber blank the likely STAB/status while
  preserving the generic wall for a harder job?
- Does our move beat the package, the enabled owner, or only the active target?
- If Curse, coverage, or Explosion is public, can it convert this cycle before
  the counter-handoff owner stabilizes?

Top move must answer the package route before it polishes the visible matchup.
Generic special walls are not automatic into fast support or Electric pressure
when a typed/status absorber both blanks the likely move and creates progress.
On stall structures, Protect and Rest are package actions, not passive flavor.
Protect can scout sleep, coverage, Explosion, Spin, or a phaze/reset attempt
while the clock advances. Rest can be top after the public clock has already
created progress and the RestTalker or spinblocker must keep its job.
The inverse also matters: Electric Hidden Power coverage is a strong-prior
package. Keep status or damage with the current owner above a Ground handoff
when coverage can punish that handoff and the current move already converts.
Sleep plus cash-out is a package, not two separate surprises. Once Snorlax has
revealed Lovely Kiss and Double-Edge, price Self-Destruct before leaving
Zapdos, Raikou, RestTalk Snorlax, or the current route owner in to click
damage. Do not wait for low HP unless Rest or four revealed moves disproves it.
Sleep plus item removal is also a package. After Jynx puts the RestTalk check
to sleep, do not default to Sleep Talk if Thief can take the item that makes
the absorber a route piece.

Sleep absorber transaction beats hidden coverage read unless coverage is
revealed, side-known, or explicitly marked as a high-risk read with fallback.
Voluntary entry is a clue, not proof of coverage. Sleeping RestTalk can act,
but Sleep Talk is not automatic when another owner can absorb the revealed hit.
Do not switch a Ghost or resist into RestTalk by assuming unrevealed coverage is
absent; price the coverage roll as a branch with fallback.
Counter-handoff is not automatic after naming the owner, but pricing may still
promote it when the owner class is revealed/strong-prior and the active action
only beats the old board. For cash-out, support, Rest, or phaze routes, run the
spend/save and reset-denial gates before ranking the package top.
For pass routes, the boost is a route piece. Attacking with the passer is top
only when it converts before phaze, reset, Explosion, or strong-prior attacking
rolls remove the passer; otherwise name the receiver and pass.
Against AgilityPass, hitting Jolteon is not enough. Reflect or status can be
the converter when the receiver would otherwise act before the real answer.
Encore is not a pass answer if the passer can Baton Pass before Encore lands.
Trap/perish order matters: hold the current target or Baton Pass receiver,
then use Confuse/Pain Split/Protect to survive, then start or maintain the
Perish count. Perish without a held target is usually just a forced switch.
The exception is branch-forcing Perish: starting the count first can be correct
when the expected switch receiver is the real target and the next action holds
that receiver. It is not progress unless hold and exit are both named.

Do not treat a support reveal as flavor text; it changes the role ledger.

Archive: `policy_cards/support_handoff_after_job.md`;
`policy_cards/branch_action_after_naming.md`.
