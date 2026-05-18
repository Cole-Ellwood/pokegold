# Legendary Timeline Events Spec — Pokémon Gold/Silver Hack

> **STATUS: PARKED IDEA — NOT FOR IMPLEMENTATION.**
>
> Stored 2026-05-18 from a brainstorm/spec session. This document is a
> parked design candidate. It is **not** a current workstream and **not**
> cleared for code. The user (gameplay-design lead) will green-light if /
> when they want this revived. Until then, do not begin authoring maps,
> scripts, sprites, prose, save-format changes, or any of the content
> sketched below.
>
> Agents reading this: if you're looking for active work, see
> `docs/project_roadmap.md`. This file is a "maybe later" record.
>
> ---
>
> Goal: in-game (no Mystery Gift) event content for catching Celebi,
> Mew, and Mewtwo, plus cross-version Ho-oh / Lugia handling.
> Mechanic: Celebi-powered time travel to two new regions —
> the **Verdant Cradle** (distant past, Mew) and the **Cinderspire
> Tomorrow** (dystopian future, Mewtwo).

## 1. Concept

The Ilex Forest shrine is canonically Celebi's anchor in space-time.
The vanilla game treated it as scenery. This hack treats it as the
hinge of the postgame metaplot.

After completing the existing Johto/Kanto campaign + the legendary
beasts arc, the player acquires a key item that summons Celebi at the
Ilex shrine. Once Celebi is caught, the shrine becomes a **time
gate**. Celebi can carry the player to two anchored moments:

- **The Verdant Cradle** — the distant pre-civilization past, when
  Pokémon had no human companions. Lush, vast, sacred. Mew is the
  unseen heart of this world.
- **The Cinderspire Tomorrow** — a ruined future Kanto, an alternate
  timeline where Mewtwo's rage was never reconciled and the world
  paid. Mewtwo waits at the end, full of grief.

Two trips. Two mythicals. One Celebi narrating it all. Plus a
cross-version flourish: Gold-side players gain the Silver Wing in the
future trip; Silver-side players gain the Rainbow Wing in the past
trip. The mythological wings come from the timelines that *match
their mythology*.

## 2. North Star fit

The hack's North Star (per `CLAUDE.md`) is restoring **uncertainty**,
discovery, and danger for a veteran Pokémon player. This event content
fits because:

- **Mythical Pokémon become diegetic, not gift-shop.** Mew has been
  one of two things in 30 years: a glitched-out tile near Cerulean, or
  a Mystery Gift download code. Putting it inside a story finally
  earns it.
- **Mewtwo recontextualized.** Vanilla Gen 2 has Cerulean Cave Mewtwo
  but the lore is barely surfaced. The Cinderspire trip makes Mewtwo
  the load-bearing emotional moment of the postgame.
- **Celebi finally has a job.** "Voice of the Forest" gets to actually
  speak. The mythical that always felt the least connected to anything
  becomes the *conductor* of the entire event arc.
- **Catches the user's "ADD don't restrict" preference**
  ([[additive-replay-over-restrictive]]). New regions, new lore, new
  mons to catch — all additive, none restricting the existing player
  experience.
- **Stays Gen 2 in texture.** No abilities, no natures, no modern
  mechanics. The past timeline literally pre-dates everything;
  mechanics couldn't be more Gen-2-pure than "no inventions yet."

The discovery loop a returning veteran experiences: *"Wait, you can
go where? With Celebi? And I find what there?"* That's exactly the
emotion the hack exists to manufacture.

## 3. ROM budget (target 100–130 KB, leaves room for other content)

| Component | Bytes | Notes |
| --- | ---: | --- |
| New maps (12–17 maps across both timelines + shrine expansion) | ~35 KB | Compressed Gen 2 block data + collision |
| New tilesets (Verdant jungle, Cinderspire ruin) | ~16 KB | 2 fresh tilesets, ~8 KB each |
| Map scripts (events, NPCs, encounters) | ~22 KB | Largest authored content |
| New text (dialogue, lore, journals, Mewtwo monologue) | ~14 KB | Compressed Gen 2 text |
| New music tracks (3 new — Verdant, Cinderspire, Mewtwo cue) | ~10 KB | Reuse Suicune theme for Mew |
| New NPC overworld sprites + battle sprites | ~6 KB | Ancient guardians, future ghosts |
| Key item data + flag bytes + misc | ~3 KB | |
| **TOTAL** | **~106 KB** | Lands in 7 of 14 free banks |

That leaves **7 banks (~112 KB) free** for other postgame content,
QoL, save-format-bump bundles, or future expansion. This is a much
smaller footprint than the Hoenn option — by design.

Sizing reference: each new map's block data is typically 256–2048 bytes
depending on size; scripts run 1–3 KB; a fresh tileset (graphic +
metatile + collision data) is ~8 KB. Music tracks are 2–4 KB each in
Gen 2.

## 4. Player journey overview

The full arc, end-to-end. Bold = new content; everything else is
existing or only slightly modified.

1. Complete the main Johto + Kanto campaign + defeat Red. *(existing)*
2. Catch all three legendary beasts (Raikou, Entei, Suicune). *(existing
   Crystal-style trigger, kept as the gate)*
3. **Return to Pewter City. The Move Tutor's old friend gifts you a
   small wooden object — a "Time Locket" carved from an Ilex sapling.**
4. **Take the Time Locket to Kurt in Azalea Town. He fits a smooth
   sphere into the Locket overnight — it becomes the GS Ball.**
5. **Walk into Ilex Forest, place the GS Ball on the shrine. Celebi
   appears at L40. Battle it. Catch it.**
6. **Celebi joins your team. Return to the shrine — a new dialogue
   option: "Travel with Celebi?" — opens the Time Anchor menu.**
7. **First trip: the Verdant Cradle.** ~2-3 hours of content. Catch
   Mew, witness the origin myth. *Gold-only:* a vision of Ho-oh
   resurrecting the three beasts at Brass Tower — origin of the
   **Rainbow Wing** that already exists in your inventory in vanilla
   Gold. *Silver-only:* you find the Rainbow Wing here.
8. **Second trip: the Cinderspire Tomorrow.** ~3 hours of content.
   Confront Mewtwo, read the extended Mansion journals, fight (or
   flee from) the most dangerous mon in the hack. *Silver-only:* a
   vision of Lugia calming a tsunami — origin of the **Silver Wing**.
   *Gold-only:* you find the Silver Wing here.
9. **Post-arc.** Celebi remains catchable / Tradeable. Both timelines
   stay accessible — you can revisit for side encounters and lore.

Total new content: roughly **5–8 hours** for a thorough player. Smaller
than the Hoenn option but with much higher craft per hour.

## 5. The key item chain (how the player unlocks time travel)

No Mystery Gift. Everything is in-game.

### 5.1 Step 1 — earn the Time Locket

The Move Tutor's home in Pewter City (or some other low-profile NPC
already in Kanto) becomes a new event hook. After defeating Red, a
new NPC appears in the Move Tutor's house — an elderly woman who
introduces herself as the Tutor's late wife's sister. She tells the
player about her dream:

> *"I dreamed of a green light, and a forest that wasn't there. The
> light asked for someone strong enough to carry it. I think she
> meant you."*

She gives the player a **Time Locket** — described as "a small
wooden ornament, warm to the touch, carved from a single Ilex
sapling." Item description: *"Said to belong to one who can hear the
forest's voice. Open only at the right shrine."*

This step is gated behind:
- All 16 badges
- Red defeated on Mt. Silver
- All three legendary beasts caught (or seen + roaming)

(Catching the beasts is the canonical Crystal pre-requisite for the
Rainbow Wing in vanilla; here it's the *Time Locket* gate, so the
existing infrastructure is reused.)

### 5.2 Step 2 — Kurt fits the GS Ball

The Time Locket has an empty socket. The player brings it to **Kurt
in Azalea Town**, who recognizes the wood:

> *"This is from the Old Tree, isn't it? Where the spirit lives.
> Leave it overnight. I've got something that fits."*

Kurt fits a smooth, opalescent sphere into the Locket. The next day
the player retrieves it; the Locket has become the **GS Ball**.

This step honors the vanilla Crystal Japanese-event GS-Ball-via-Kurt
flow, just with an in-game justification instead of a Mobile-System-GB
event.

### 5.3 Step 3 — Ilex shrine summons Celebi

The player walks into Ilex Forest, faces the shrine, presses A. The
GS Ball glows. A flash. Celebi descends. **Battle: Celebi L40.**

After capture (or KO + respawn after 24 in-game hours), the GS Ball
remains in the inventory and re-keys to the shrine. Walking up to the
shrine with the GS Ball + Celebi in the party prompts:

> *Celebi looks restless. Will you let it guide you?*
>
> ▸ Travel with Celebi
> ▸ Stay here

Choosing "Travel" opens the **Time Anchor menu**.

### 5.4 The Time Anchor menu

Two anchors at first. Each one is unlocked at first visit and stays
accessible. A third anchor (the present-day shrine) is always the
return point.

| Anchor | Name | Description |
| --- | --- | --- |
| 1 | **Verdant Cradle** | "The forest before the world." |
| 2 | **Cinderspire Tomorrow** | "The sky that fell." |
| 3 | (Return) | "Back to now." |

Selecting an anchor triggers a fade-out + Celebi animation + map
transition. New BGM. New region.

### 5.5 Step 4 — completing the arcs

Both trips can be done in either order. Each trip has its own
content, its own ending, its own mythical mon. Once both arcs are
complete, Celebi gains a final dialogue line at the shrine, and the
postgame has additional ambient sightings (Celebi appearing in
Sprout Tower in Violet, in the Dragon's Den, etc. — small overworld
cameos as recurring flavor).

## 6. The Ilex Shrine expansion

The shrine itself was a single tile in vanilla. It becomes a small
**3×3 sub-map** with:

- The original shrine sprite (canonical, untouched)
- Two ancient stone markers flanking it (lore-readable: "From this
  place, the green one comes." / "From this place, the green one
  returns.")
- A faint mossy circle on the ground (Celebi's landing point)
- An animation glow effect that triggers during time-travel transitions

ROM cost: ~600 bytes including new sprite + sub-map + scripts.

## 7. Celebi — capture, role, mechanic

### 7.1 The capture

Celebi appears at the shrine at **L40**. Moveset:

- Heal Bell
- Recover
- Leech Seed
- Confusion (or Magical Leaf if added to the hack)

Celebi has standard catch rate (45) and uses Master Ball / Ultra Ball
priors. Battle is *gentle* — Celebi does not attempt to OHKO; it
delays, recovers, evades. The fight is meant to *feel* like
negotiating with a forest spirit, not slaying it.

Special hook: if the player attempts to flee, Celebi follows them out
of the shrine via overworld dialogue and reappears every 30 minutes
real-time until either caught or killed. (Soft re-roll mechanic that
matches Celebi's myth — it doesn't *want* to leave.)

### 7.2 Celebi as guide

Catching Celebi does NOT auto-unlock time travel. The player has to
walk back up to the shrine, **with Celebi in party**, and trigger the
travel prompt. This means Celebi can be traded away, but trading away
Celebi removes time-travel access until a replacement Celebi is
re-acquired (via re-enabling the shrine after waiting an in-game
week).

Design intent: Celebi is your **companion**, not just a McGuffin
holder. The player has to want this Pokémon on their team.

### 7.3 Celebi's voice

In-game Celebi communicates through **italicized thought-text** in a
distinct text color. It has no spoken voice — it's the Voice of the
Forest, all telepathy. Example mid-trip dialogue:

> *... the wind here remembers you. Be still.*
>
> *... do not be afraid. The world here is younger than fear.*

This is a small text engine change (italic toggle exists in Gen 2;
color toggle requires a few bytes of palette state). Budget: ~1 KB
for Celebi-specific text presentation.

## 8. The Verdant Cradle — past timeline (Mew)

> *"The forest before the world."*

### 8.1 The world

Mew is canonically described as discovered in Guyana (the jungles of
South America) — see [Bulbapedia — Mew (Pokémon)](https://bulbapedia.bulbagarden.net/wiki/Mew_(Pok%C3%A9mon)).
The Verdant Cradle is that jungle, viewed at its primordial peak —
**no humans, no roads, no civilization**. Just an endless living
forest watered by misty rivers, with Pokémon roaming freely.

Aesthetic anchors:
- Lush green tileset with bioluminescent flowers
- Ancient megafauna versions of common Pokémon — Aerodactyl flying
  overhead, herds of Tauros, schools of Lapras in the river
- No fences. No doors. No interior maps. Pure outdoors.
- Soft, ethereal music — reuse the existing Suicune theme as the base
  ambience; one new theme for the central grove

### 8.2 Map layout

5 connected maps, all outdoor:

| # | Name | Notes |
| --- | --- | --- |
| 1 | **Cradle Arrival** | Player materializes in a glade. Celebi explains in thought-text. Path leads three ways. |
| 2 | **River of Beginnings** | A wide river. Lapras trio waits silently. One has a wound — player helps (no battle). |
| 3 | **Megafauna Plateau** | Wild Aerodactyl, Kabutops, Omastar (their living forms in this era). NOT angry — neutral encounters. |
| 4 | **The First Shrine** | A small stone circle. Three offering tiles. Player must place three items (see §8.3). |
| 5 | **Heart of the Cradle** | A vast tree at the center of the world. Mew descends. |

Optional sixth map:
| 6 | **Sleeping Grove** | A hidden grove where ancient Pokémon are resting — accessible only after Mew is caught. Contains a hint about the Cinderspire Tomorrow. |

### 8.3 The Trial of Compassion (catching Mew via "pure of heart")

Mew is canonically only revealed to those "pure of heart." The Trial
is a **no-combat puzzle sequence** spread across the five maps:

1. **River of Beginnings** — the wounded Lapras has a small thorn.
   Use a Berry (any) from your bag to heal it. It thanks you and
   gives you the first **Mew Token** (a glowing leaf).
2. **Megafauna Plateau** — a young Bagon (out-of-place; doesn't exist
   in this era yet) is lost. Lead it (Pokémon-following style, or via
   dialogue choice) back to the Verdant glade. It gives you the
   second token.
3. **The First Shrine** — three offering tiles. Place the two Mew
   Tokens on two of them. The third is **silence** — you have to
   stand on it for 10 real-time seconds without input. The shrine
   activates.

Failing any step doesn't lock the player out — they can retry.
There's no fail state, only "not yet."

After the shrine activates, the path to the Heart opens.

### 8.4 The Mew encounter

At the Heart of the Cradle, the great tree shimmers. Mew appears.

> *Celebi: ... it sees you. Do not move suddenly.*

Battle: **Mew L40**. Moveset:
- Transform
- Pound
- Aqua Tail (or Surf if it learns Surf at level)
- Recover

Mew is fully canonical playful behavior. It uses Transform liberally —
the player may find themselves fighting their own Pokémon's stat block
mid-battle. This is intentional flavor.

Catching Mew is not difficult mechanically (standard catch rate 45)
but emotionally the moment is the centerpiece.

If KO'd, Mew respawns at the Heart after the player exits and
re-enters the Cradle. Mew cannot be lost permanently.

### 8.5 Side-encounters (optional content)

Wild Pokémon in the Cradle, with seed-level appropriate to a player
arriving at L70+ team strength but who wants to catch ancient forms:

- **Aerodactyl** (L40 wild — rare). Living, not fossil-revived. Has
  flavor dialogue: "It studies you. It has never seen anything like
  you."
- **Kabutops, Omastar** (L38, L38). Same flavor — they are *current*
  Pokémon here, not relics.
- **Lapras** trio at the river (L35–40). One can be caught after
  helping the wounded one.
- **Larvitar, Pupitar, Tyranitar** in the **Megafauna Plateau cliffs**
  — full evolutionary line, L40-50. Lore: Tyranitars are
  prehistoric apex predators (matches Tyranitar dex flavor).

These are gift-bonuses, not gated. They reward exploration but aren't
required.

### 8.6 The Rainbow Wing scene (Silver-version only)

While walking the Megafauna Plateau, the Silver-version player can
witness a one-time cutscene:

> A great fire spreads through a far-away tower. From the smoke,
> three creatures rise — a fox of lightning, a wolf of fire, a
> blueprint of water.
>
> Above them, the sun bird descends.
>
> Celebi: *... that's how the three came to be. He gives them back
> what was taken.*
>
> [A glowing red feather drifts down and lands at the player's feet.]
>
> [Got the Rainbow Wing!]

The Gold-version player already has the Rainbow Wing via Tin Tower
flow; this scene is *not shown* to them. Replace with a quiet ambient
moment.

### 8.7 Departure

Walking back to **Cradle Arrival** triggers Celebi's prompt:

> *Celebi: This place will fade. It always does. Hold on.*

Return to the present-day Ilex shrine. Mew is now in your party (if
caught).

## 9. The Cinderspire Tomorrow — future timeline (Mewtwo)

> *"The sky that fell."*

### 9.1 The world

A dystopian future Kanto. The premise: in this alternate timeline,
Mewtwo's creation was not contained. Mewtwo's rage spilled outward;
Team Rocket's resurgence (the one Lance prevented in Johto vanilla
Gen 2) succeeded; the world has fallen into a slow industrial decay.
The Pokémon world's "After the End" trope, applied with restraint.

Per post-apocalyptic design research
([Game Developer / TVTropes — After the End](https://tvtropes.org/pmwiki/pmwiki.php/AfterTheEnd/VideoGames),
[Beyond Barren Wastelands](https://gamescriticism.org/2024/09/06/bianchi-6-a/)),
the visual shorthand: ruined landmarks, return-to-nature, isolated
silence, no living NPCs (only ghost-trainer encounters, see §9.6).

Aesthetic anchors:
- Rust + ash tileset, broken Silph Co. modules
- Skies in a permanent twilight (palette shift)
- No music in most maps — *deliberate quiet* — sparse ambient pulses
- A single new theme for Mewtwo's confrontation
- All "people" are gone. The world is post-Mewtwo, post-everything.

### 9.2 Map layout

8 connected maps. Larger than the Cradle because the dystopia is the
*content* — the player slowly understands what happened.

| # | Name | Notes |
| --- | --- | --- |
| 1 | **Cinder Arrival (Pallet)** | Pallet Town. Ruined. Oak's lab a collapsed shell. One stray Eevee skitters away — too fast to catch. |
| 2 | **Route 1 (Wasted)** | Tall grass replaced with dry husks. Wild Rattata corrupted by hunger. |
| 3 | **Viridian Husk** | Viridian City, half-flooded. PokéMart sign half-buried. |
| 4 | **Pewter Memorial** | Pewter Museum stands, vaults locked. Inside: extended Pokémon Mansion journals, relocated here for safekeeping (lore conceit). |
| 5 | **Route 24 South (Wreckage)** | The bridge to Cerulean is broken; player must Surf. |
| 6 | **Cerulean Hollow** | Cerulean Cave entrance. The cave is collapsed at the surface — Mewtwo's old home is closed off, sealed. |
| 7 | **Silph Spire** | Silph Co. tower, but in ruin. Climb 8 floors of broken corridors. Each floor has a ghost-trainer encounter. |
| 8 | **The Roof** | Top of Silph Spire. Mewtwo waits. |

Optional ninth map:
| 9 | **Cinnabar Drowned** | Cinnabar Island, fully sunken; reachable via Surf in southern Cerulean. The original Pokémon Mansion, partially underwater. Contains the *original* Mansion journal pages, untouched (see §9.3). |

### 9.3 Extended Pokémon Mansion journals

Canonical Mansion journals (Gen 1 / FRLG / LGPE), per
[Bulbapedia — Pokémon Mansion journals](https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_Mansion_journals):

> July 5: Guyana, South America. Discovered new Pokémon in the
> jungle.
>
> July 10: We christened the newly discovered Pokémon, Mew.
>
> Feb. 6: Mew gave birth. We named the newborn Mewtwo.
>
> Sept. 1: Mewtwo is far too powerful.

The Cinderspire postgame adds **new journal pages** continuing past
the canonical entries, written by the same researcher (Dr. Fuji or
unnamed) in this alternate future. Each is found in the Pewter
Memorial (relocated for safekeeping) or in the drowned Cinnabar
Mansion (originals):

> Sept. 23: Mewtwo escaped. The lab burns. I write this from a
> shelter.
>
> Oct. 8: They say the storm above Cerulean Cave is alive. We don't
> go there anymore.
>
> Nov. 15: I tried to talk to it. From the cave mouth. It heard me.
> It did not speak.
>
> Dec. 1: Three of the children are dead. I cannot mourn yet. I have
> to finish this.
>
> Dec. 14: Found a note in the rubble of the Mansion. "Mewtwo was a
> child too." I do not know who wrote it.
>
> Feb. 6 (next year): Today would have been its birthday. I left an
> offering. The wind moved.
>
> [final entry, undated]: We did this. I did this. I do not have a
> way to fix it. If anyone reads this — find it. Tell it I am sorry.

That last entry is the emotional anchor of the entire arc. The
journal sequence is **~5 KB of text** — the heaviest single piece of
writing in the spec.

### 9.4 The Mewtwo encounter

The Silph Spire rooftop. The skyline is in ruins. Mewtwo levitates
above an exposed rebar pile. A long monologue:

> *(in italics, telepathic — Celebi shrinks back, frightened)*
>
> Mewtwo: ... you should not be here. None of you should still be
> here.
>
> Mewtwo: I remember the cave. I remember the cave before the cave.
> I remember the lab. I remember the woman who said I was beautiful
> and then ran from me.
>
> Mewtwo: I tried, at first, to be smaller. To make less of myself.
> They wanted a weapon. I am not a weapon. I am... I do not have a
> word.
>
> Mewtwo: This world ended because no one ever asked me what I
> wanted. Not until you. And you are very late.

The player has **two options**:

1. **Battle Mewtwo.** L70. Full team. The fight is balanced as the
   hardest legendary encounter in the hack — comparable to Red's
   ace, with Recover spam and Psychic STAB.
2. **Speak.** A dialogue check — only available if the player
   completed the journal-reading side content in §9.3 (~5 specific
   tiles examined). Speaking unlocks an *alternate* catch path: Mewtwo
   surrenders at L70 with full HP after a one-turn "scene battle"
   where it does not attack. Catching is normal-rate Master Ball /
   Ultra Ball.

Both endings catch the same Mewtwo. The difference is **what the
player saw of Mewtwo before catching it**.

### 9.5 The Silver Wing scene (Gold-version only)

While crossing the broken bridge to Cerulean (Map 5), the Gold-version
player witnesses:

> The water rises. A wave taller than the Silph Spire bears down on
> the wasted city.
>
> Above the wave, a great pale shape — wings wide as a thundercloud
> — descends. It cries once. The wave calms. The water sinks.
>
> Celebi: *... that's how it's done. He holds back what we built.
> Even here.*
>
> [A glowing silver feather drifts down and lands at the player's
> feet.]
>
> [Got the Silver Wing!]

Silver-version player gets the Silver Wing in vanilla; replace with
quiet ambient moment.

### 9.6 Ghost trainers in Silph Spire

Inside the Spire, each floor has one "ghost-trainer" encounter — the
faded shade of a Silph Co. employee or trainer who fell during the
collapse. They fight like normal trainers, but their sprites are
**translucent** (palette trick), they don't speak before battle, and
after victory they fade out with one quiet line:

| Floor | Trainer class | Team | Final line |
| --- | --- | --- | --- |
| 1 | Office Worker (ghost) | Raticate L65, Hypno L65 | *"... thank you. I forgot what light felt like."* |
| 2 | Scientist (ghost) | Magneton L65, Magnezone-as-Magneton L65 | *"... Fuji was right. Even him."* |
| 3 | Rocket Grunt (ghost) | Houndoom L66, Crobat L66, Mightyena-stand-in L66 | *"... we lost too. Everyone lost."* |
| 4 | Trainer (ghost) | Espeon L67, Umbreon L67 | *"... I trained them well. We just had nowhere to go."* |
| 5 | Channeler (ghost) | Gengar L68, Misdreavus L68 | *"... I am a ghost trainer. I knew it before you did."* |
| 6 | Old Man (ghost) | Snorlax L68 | *"... still asleep. He was always asleep. Let him keep dreaming."* |
| 7 | Researcher (ghost) | Porygon2 L69, Alakazam L70 | *"... I made him because I could. I never thought to ask if I should."* |
| 8 | Silph CEO (ghost) | Aerodactyl L70, Gyarados L70, Tyranitar L72 | *"... we paid to bring it forward. We paid everything."* |

These ghost battles are optional but powerfully atmospheric. Total ROM
cost: ~3 KB scripts + ~2 KB text + the trainer rosters.

### 9.7 Wild Pokémon in the Cinderspire

All wild encounters are **corrupted / aged** versions of common
Pokémon — narratively framed via dex-text-style flavor when caught,
not via stat changes (the hack stays Gen-2-mechanical):

- Routes: Rattata, Raticate, Zubat, Golbat (Crobat unavailable here),
  Spinarak/Ariados, Ekans/Arbok — all L60-68
- Husk Viridian: Pidgey/Pidgeot, Magnemite/Magneton
- Cerulean Hollow: Magikarp, Gyarados, Slowpoke, Slowbro
- Silph Spire: Gastly, Haunter, Gengar, Misdreavus, Voltorb,
  Electrode
- Drowned Cinnabar: Tentacool, Tentacruel, Magikarp (rare Shiny —
  flavor cameo), Lapras (L72, rare; the survivor of the trio you met
  in the past?)

Optional one-of-each capture: a **dark-feel** Eevee at L60 in Pallet
ruins. Unique. Limited to one.

### 9.8 Departure

After catching Mewtwo (battle or speech path), the player walks back
to **Cinder Arrival**. Celebi softly:

> *Celebi: It is not done. It will never be done. But you carry
> something out with you now.*

Return to the present-day shrine. Mewtwo is in your party (if
caught).

## 10. Cross-version Lugia / Ho-oh integration

Vanilla Gen 2 Gold/Silver already allows both legendaries via the
Rainbow Wing + Silver Wing system. Per [Bulbapedia — Silver and
Rainbow Wings](https://bulbapedia.bulbagarden.net/wiki/Silver_and_Rainbow_Wings):

- **Gold:** Rainbow Wing → Ho-oh (Tin Tower). Silver Wing given by
  Pewter NPC after Radio Tower → Lugia.
- **Silver:** Silver Wing → Lugia. Rainbow Wing given by Pewter NPC
  after Radio Tower → Ho-oh.

The cross-version wing already exists; only the **path** to it varies.

This hack overlays new diegetic justifications:
- **Gold-version player** gets the Silver Wing during the Cinderspire
  trip (§9.5) — the timeline mythology fits: Lugia is "future-facing"
  / preserves the sea against ruin.
- **Silver-version player** gets the Rainbow Wing during the Verdant
  trip (§8.6) — Ho-oh is "past-facing" / births the legendary trio.

The vanilla Pewter NPC path is **also kept** (in case the player
misses the timeline scene or doesn't enter the relevant Map). The
NPC simply offers the wing in flat dialogue, no plot wrapper. The
timeline path is the *poetic* path; the NPC path is the safety net.

Wing acquisition unchanged in mechanics — just the diegetic frame
shifts. **Zero gameplay regression risk.**

## 11. Maps in detail (block budget per area)

Final map list (15 new maps including the optional 9.9 / 8.6 maps):

| # | Map | Type | Size | ROM (KB) |
| --- | --- | --- | ---: | ---: |
| Past 1 | Cradle Arrival | outdoor | small | 1.5 |
| Past 2 | River of Beginnings | outdoor | medium | 2.5 |
| Past 3 | Megafauna Plateau | outdoor | medium | 2.5 |
| Past 4 | The First Shrine | outdoor | small | 1.5 |
| Past 5 | Heart of the Cradle | outdoor | medium | 2.5 |
| Past 6 | Sleeping Grove (optional) | outdoor | small | 1.5 |
| Future 1 | Cinder Arrival (Pallet) | outdoor | small | 1.5 |
| Future 2 | Route 1 (Wasted) | outdoor | medium | 2.5 |
| Future 3 | Viridian Husk | outdoor | medium | 2.5 |
| Future 4 | Pewter Memorial | indoor | small | 1.5 |
| Future 5 | Route 24 South (Wreckage) | outdoor | medium | 2.5 |
| Future 6 | Cerulean Hollow | outdoor | small | 1.5 |
| Future 7 | Silph Spire (8 floors, sub-mapped) | indoor | large | 6.0 |
| Future 8 | The Roof | outdoor | small | 1.5 |
| Future 9 | Cinnabar Drowned (optional) | underwater | medium | 2.5 |
| Shrine | Ilex Shrine expansion | outdoor | small | 0.5 |
| **TOTAL** | | | | **~34 KB** |

Matches §3 estimate.

### 11.1 Why no interior maps in the past?

Design choice. The Cradle is supposed to feel *outside-of-time*.
Indoor architecture implies civilization; civilization doesn't exist
yet here. Even the First Shrine is just an open-air stone circle, not
a building.

The future, by contrast, is *all about* fallen civilization, so
interiors carry that theme — the Spire and Memorial are interior
heavy.

## 12. New tilesets

Two fresh tilesets, ~8 KB each:

### 12.1 Verdant Cradle tileset

- Base color: deep green (16 shades for variation)
- Tree variants: ancient oak, fern, banana tree, glowing vine
- Water tile: lily-pad river + waterfall
- Ground tile: moss + mud + bioluminescent flowers (sparkle frame)
- Stone tile: ancient stone circle, ivy-covered
- Sky overlay: mist (palette-based, no new tiles)

### 12.2 Cinderspire Tomorrow tileset

- Base color: muted brown/grey/rust
- Building variants: half-collapsed Silph cubes, broken pokeball
  fragments, twisted street signs
- Ground: cracked concrete, rubble, ash
- Water: stagnant pool (different from active water)
- Sky overlay: permanent twilight (palette shift)
- Spire interiors: broken corridors, exposed pipes, flickering
  lights (animation frame trick)

Both tilesets are **fresh art** but can reuse Gen 2 metatile patterns
(corner/edge/center) so the implementation is "new graphics, same
plumbing."

## 13. Music plan (~10 KB)

| Track | Source | Bytes |
| --- | --- | --- |
| Verdant Cradle ambient | NEW — original | ~3 KB |
| Heart of the Cradle (Mew theme) | Reuse Suicune theme (canonical mythic match) | 0 |
| Cinderspire ambient | NEW — sparse, dystopian | ~3 KB |
| Silph Spire (ghost floor) | Reuse Lavender Town theme | 0 |
| Mewtwo battle | NEW — heavy, mournful | ~3 KB |
| Time travel transition cue | NEW (very short) | ~1 KB |
| Celebi theme (return shrine) | Reuse Celebi cry sequence | 0 |
| **TOTAL** | | **~10 KB** |

If user wants Mewtwo Strikes Back movie-style theme cover for the
encounter, budget ~5 KB instead of 3 — eats a bit more of the slack.

## 14. NPCs, ancient guardians, future ghosts

### 14.1 Past NPCs (zero human NPCs by design)

The Cradle has no humans. Pokémon speak through context. The only
"dialogue" is Celebi's narration + a few interactable Pokémon (the
wounded Lapras, the lost Bagon). Author-cost: minimal — ~4 KB of
text total.

### 14.2 Future NPCs (eight ghost trainers + scattered remains)

§9.6 covers the 8 ghost trainers. Additional ambient NPCs are
**scattered remains** (not interactive battles, just text):

- A faded teddy bear in Pallet's ruined house ("It belonged to a
  child who lived here.")
- A torn Pokégear on the broken Route 24 bridge ("It rings sometimes.
  No one answers.")
- A small grave at the edge of Cerulean ("Beloved Bulbasaur. He was
  brave.")
- A faded note pinned to the Silph Spire entry ("To anyone who reads
  this: don't go up.")

These are world-building moments, ~50-100 bytes of text each. Author-
cost: ~1 KB total, but the *atmospheric weight* per byte is the
highest in the entire spec.

### 14.3 Pewter Memorial Curator

The Memorial has ONE non-ghost living presence: a Curator who has
chosen to live alone, tending the journals. He doesn't fight. He
just speaks. Three dialogue trees:

- First visit: explains what the Memorial is, refuses to let the
  player into the archive room until they've proven themselves
- After defeating one ghost trainer in Silph: opens the archive
- After Mewtwo encounter: a final dialogue, the player can ask him
  one question; answer varies by route taken (battle vs speak with
  Mewtwo)

The Curator IS the player's emotional witness for the future arc. He
might be the only voice in this timeline who's *glad* to see them.

## 15. Trainer encounters in each timeline

### 15.1 Cradle (past)

Zero trainer battles. Pure exploration + puzzle + capture. (User's
[[additive-replay-over-restrictive]] preference applied: no
unnecessary challenge gating.)

### 15.2 Cinderspire (future)

8 ghost trainers in Silph Spire (§9.6). Optionally **two side
trainers** in Cinnabar Drowned (the underwater optional map) — both
ghosts of failed Mansion researchers, both ghost-trainers.

Total trainer count: 8 mandatory + 2 optional. All ghost-themed.

Total trainer-roster data: ~1 KB.

## 16. Wild Pokémon in each timeline

Already covered §8.5 (past) and §9.7 (future). Net unique-species
adds: **zero** (all already in Gen 1/2 dex).

This is a major budget win — no new Pokémon species data needs
adding, just new encounter tables. ~2 KB of new encounter-table data
across all maps.

If the user wanted to add Mythic/event mons for prestige (e.g.,
**fossil Pokémon in their living forms**, with subtly different
sprites for "ancient living" Aerodactyl vs canonical fossil
Aerodactyl), that would cost ~6 KB per ancient-form sprite × 3-4 mons
= ~24 KB. **Recommendation: skip.** The "wait, they're alive here"
moment lands fine with the canonical sprite.

## 17. ROM bank assignment (proposal)

7 of the 14 free banks assigned. 7 banks remain free.

| Bank | Contents | Size |
| --- | --- | --- |
| `13` | New tilesets (Verdant + Cinderspire) + new tile animations | ~16 KB |
| `22` | New maps — Past timeline (5 + optional 1 = 6 maps) | ~12 KB |
| `27` | New maps — Future timeline (8 + optional 1 = 9 maps) + shrine expansion | ~14 KB |
| `28` | New map scripts (events for both timelines) | ~16 KB |
| `29` | New text (dialogue, journals, ghost lines, Mewtwo monologue) | ~14 KB |
| `2c` | New music tracks + transition cue + Mewtwo battle theme | ~10 KB |
| `2d` | New NPC sprites + ghost-trainer sprites + Curator overworld | ~6 KB |
| **TOTAL USED** | | **~88 KB** |

Banks **2f, 34, 35, 58, 63, 67, 6f** remain **fully free** — ~112 KB
of slack.

That slack is available for:
- Other postgame ideas (Battle Frontier-lite, more side scenarios)
- QoL pass
- Save-format-bump bundle (MASTERY-001 + 3.5 + 5.9 + 11.10 +
  BOSSAI-002 per the brainstorm doc)
- Future Hoenn add (if the user changes their mind later — Hoenn
  could fit in ~11 of the remaining 7 banks... wait, 7 banks ≠ 11.
  Hoenn would need scope reduction OR additional sources of ROM. Note
  the asymmetry: this scope is cheap, Hoenn was expensive)

## 18. WRAM / SRAM impact

### 18.1 WRAM (minimal)

- Current-timeline indicator: 1 byte (0=present, 1=past, 2=future).
  Used by the script engine to gate which warp targets are valid.
- "Trial of Compassion" progress: 1 byte (3 bits used for tokens,
  rest reserved).
- Ghost-trainer-defeated bitmap: 2 bytes (16 bits for ~10 ghosts +
  slack).

**Total: 4 bytes.** Fits within existing WRAM headroom; no new bank
allocation needed.

### 18.2 SRAM (save-format bump)

- **Time-Locket-received flag** (1 bit)
- **GS-Ball-built flag** (1 bit)
- **Celebi-caught flag** (1 bit)
- **Verdant-Cradle-visited flag** (1 bit)
- **Cinderspire-visited flag** (1 bit)
- **Mew-caught flag** (1 bit)
- **Mewtwo-caught flag** (1 bit)
- **Mewtwo-encounter-resolution** (1 bit — battle path vs speech
  path; gates final Curator dialogue)
- **Cross-version Wing scene seen flag** (1 bit)
- **Per-ghost-trainer-defeated** (10 bits)

**Total: ~21 bits = 3 bytes SRAM.** Per CLAUDE.md, any SRAM bump
needs `SAVE_FORMAT_VERSION` increment and user approval before
public release. Bundle this with the other save-touching ideas
(MASTERY-001, 3.5 player profile, 5.9 replay viewer, 11.10 mon
history, BOSSAI-002 scouting counters) for a single user-facing
migration event.

## 19. Mechanics decisions (the Gen-2-stays-Gen-2 promise)

- **No abilities.** Mew, Mewtwo, Celebi run vanilla Gen 2 stats and
  moves. No Pressure, Levitate, etc.
- **No alternate forms.** Mewtwo is not armored. No Mega Mewtwo Y/X.
  No Shadow Mewtwo. Pure Gen 2.
- **No new types.** All encountered Pokémon use canonical Gen 2 type
  charts.
- **Time travel mechanic is NOT a battle mechanic.** Nothing in
  combat changes when time-traveling. The "time anchor" is purely a
  map warp with story consequences.
- **Mythical mons obey standard catch mechanics.** Mew uses catch
  rate 45; Mewtwo uses catch rate 3 (canonical Gen 1); Celebi uses
  45 (Gen 2). No Master-Ball-required tricks.

## 20. Open questions for the user

These materially change scope; flag before commit.

1. **Catch all 3 beasts as the Time Locket gate** — yes / no. Vanilla
   Crystal uses this gate for the Rainbow Wing already. Reusing it
   means players who've already beaten Crystal-style postgame are
   immediately eligible. Alternative: gate behind Red defeat only.
2. **Mewtwo speech path requires reading 5 specific journal tiles** —
   how prominent should the journal trail be? Brutal (only one tile
   per map, easy to miss) or generous (clearly signposted)?
3. **Number of Verdant maps — 5 or 6?** The optional Sleeping Grove
   adds ~1.5 KB ROM but rounds out the area. Recommend yes.
4. **Number of Cinderspire maps — 8 or 9?** Cinnabar Drowned is the
   optional one. Adds underwater scene complexity. Recommend yes if
   the hack already supports Surf-into-underwater (Gen 2 doesn't
   canonically have Dive — would need to be a normal Surf map).
5. **Cinnabar Drowned as Dive or Surf?** Recommend **Surf-only** so
   no new mechanic is introduced.
6. **Mewtwo encounter — both paths catch the same mon, OR speech-path
   Mewtwo has a different ace move (e.g. Recover)?** Speech-Mewtwo
   could be slightly different to reward the journal trail. Recommend
   **same mon, different post-catch dialogue from Curator**.
7. **Curator's identity** — completely anonymous (more haunting) or
   reveal as future-Fuji (lore-heavier)? Recommend **anonymous**;
   stronger.
8. **Visual effect for time travel transition** — short (1 second
   flash) or long (4 second swirl)? Long is more cinematic, costs
   ~500 bytes more animation. Recommend long.
9. **Celebi's voice color** — green text (matches species color),
   yellow (matches mythical convention), or italic-only? Recommend
   green italic.
10. **Mythical / event mon prestige** — should catching all three
    (Celebi + Mew + Mewtwo) unlock a final ambient cameo at the Ilex
    shrine? Recommend **yes, small**: ~300 bytes for a one-time
    cutscene where the three appear together at the shrine and
    Celebi gifts the player a single Lum Berry as the world's
    smallest possible token.
11. **Save-format bump** — bundle with MASTERY-001 / 3.5 / 5.9 /
    BOSSAI-002 per brainstorm doc §17? Recommend yes.
12. **Should Brock's daughter (the Pewter NPC who gives the
    cross-version wing in vanilla) still appear?** Yes, as the
    redundant path; keeps backwards compatibility.

## 21. What this spec does NOT cover

Items I'm explicitly deferring:

- Specific pixel art for the tilesets (art, not architecture)
- Specific music composition (audio, not architecture)
- The exact prose for the 8 ghost trainer final lines (writing
  iteration with the user)
- The Pokémon Mansion journal continuation text (writing iteration —
  the spec lists the *beats*, the writing is its own pass)
- Save-state migration code (per CLAUDE.md, no migration code
  anywhere — flagged in §18.2)
- Implementation details for the "translucent ghost trainer" sprite
  effect (palette art trick, needs prototyping)
- The Mewtwo battle's exact moveset / IVs / EVs / level (combat tuning
  pass)

None of these change the FEASIBILITY answer. Feasibility: **yes,
fits in 7 banks with room to spare**.

## 22A. Authored text drafts (the load-bearing prose)

The spec called out in §21 that the writing is the highest-leverage
authoring cost. Drafting the load-bearing pieces here so the user has
something concrete to taste rather than just beats.

These are first drafts. The user (who has the playtest + taste seat)
will rewrite as they like.

### 22A.1 — Extended Mansion journal continuation

The canonical Cinnabar Mansion journal stops at *"Sept. 1: Mewtwo is
far too powerful."* These continuation entries are found scattered
across the **Pewter Memorial** (relocated copies) and the **Drowned
Cinnabar Mansion** (originals, water-damaged). Each entry is a single
interactable tile in the Cinderspire maps.

Each entry is signed (or hinted to be signed by) Dr. Fuji. Style:
clinical-becoming-personal. Roughly 800 bytes each, ~6 KB total.

**JOURNAL — Sept. 23.**
> The lab is gone. I am writing from a shelter beneath the breakwater.
> The boy survived. So did one of the assistants. The others, I do not
> know. Mewtwo broke the southern wall and walked out. It did not
> destroy. It did not pause. It walked out the way a man walks out of
> a room he is finished with.

**JOURNAL — Oct. 8.**
> They say the storm above Cerulean Cave is alive. It has not lifted
> in five weeks. The Pokémon League has closed the cave. I do not
> blame them. We do not go there anymore.
>
> I have been told twice this week that I should leave Cinnabar. I
> cannot leave. Not yet.

**JOURNAL — Nov. 15.**
> I went to the mouth of the cave. I stood there until the wind moved
> against me. I said its name. I said the only name it ever had.
>
> It heard me. I felt it hear me.
>
> It did not answer. But it did not strike, either. Perhaps that is
> all I am allowed.

**JOURNAL — Dec. 1.**
> Three of the children are dead. From the south breakwater. I cannot
> mourn yet. There is too much work and the work is the only thing
> keeping me from drowning.
>
> I asked someone today, an old researcher I used to know, whether a
> created thing can sin. He said no. He said only its makers can.

**JOURNAL — Dec. 14.**
> Found a note in the rubble of the Mansion. Folded into the back of
> a notebook that was not mine. The handwriting was a child's. It
> read:
>
>     *Mewtwo was a child too.*
>
> I do not know who wrote it. I cannot stop thinking about it.

**JOURNAL — Feb. 6 (one year later).**
> Today would have been its birthday. I do not know what to call this
> day. The first day of grief. The first day of guilt. The first day
> of however many I have left.
>
> I left an offering at the cave mouth. A small thing. A handful of
> berries and a folded note that said only "I am sorry." The wind
> moved when I set it down.
>
> Perhaps it has read it. Perhaps not. The wind moves for many
> reasons.

**JOURNAL — undated, final entry, handwriting unsteady.**
> We did this. I did this. There is no one else to write that down
> so I am writing it down. We took a thing that should have been
> sacred and we tried to make it into a weapon and when the weapon
> would not stay still we ran from what we had done.
>
> I do not have a way to fix it. I am not even certain I have the
> right to try.
>
> If anyone reads this — find it. Tell it I am sorry. Tell it I
> would have raised it differently. Tell it I did not know how to
> begin. Tell it I should have begun.

### 22A.2 — Mewtwo's monologue (Silph Spire rooftop)

Triggered when the player arrives at Map 8 (The Roof). Mewtwo
levitates over the rebar pile. The text plays one line at a time, A
to advance, in italicized purple — *not* the standard NPC text
color. Celebi visibly shrinks back during this scene.

> Mewtwo: *... you should not be here.*
>
> Mewtwo: *I cannot smell you. I cannot read you the way I read the
> ones who came before. You are somewhere this world has not touched.
> Celebi. I know that one's name. Hello, Celebi.*
>
> *(Celebi recoils.)*
>
> Mewtwo: *Be still. I am tired, today. I am not going to break you.*
>
> Mewtwo: *I remember the cave. I remember the cave before the cave.
> I remember the lab. I remember the woman in the lab who said I was
> beautiful and then ran from me.*
>
> Mewtwo: *I remember the man in the lab who wrote things down in a
> notebook. He was kinder than the others. He still ran. He just ran
> later.*
>
> Mewtwo: *I tried, at first, to be smaller. To take up less of the
> world. To bend my voice quieter so the lights would not break when
> I spoke.*
>
> Mewtwo: *They wanted a weapon. I am not a weapon. I am... I do not
> have a word.*
>
> Mewtwo: *This world ended because no one ever asked me what I
> wanted. Not until you. And you are very late.*
>
> *(if speech path unlocked — i.e. player read the 5 journal tiles
> in §22A.1 — the next line plays:)*
>
> Mewtwo: *... you read his notebook, didn't you. The kinder one. I
> can see it on you. You read the part where he tried to apologize.*
>
> Mewtwo: *I am tired of being afraid of the past. Hold out your
> hand. We will see what comes of it.*
>
> *(else, battle path:)*
>
> Mewtwo: *I cannot speak to you with words. I can only speak to you
> with what I am.*
>
> Mewtwo: *Show me, then. Show me what you would have been to me if
> you had been there at the start.*
>
> *(Battle begins: WILD MEWTWO L70 appeared!)*

Total: ~2 KB of text including both branches.

### 22A.3 — The 8 ghost trainer encounters

Each ghost in Silph Spire is a one-screen wordless approach, a
battle, then **one quiet final line as they fade out**. The final
line is what the player remembers. ROM cost per ghost: ~200 bytes of
text + standard trainer data.

**Floor 1 — Office Worker (ghost).**
*(no pre-battle line)*
team: Raticate L65 · Hypno L65
final line: *"... thank you. I forgot what light felt like."*

**Floor 2 — Scientist (ghost).**
*(no pre-battle line)*
team: Magneton L65 · Magneton L65 (one is brighter, palette-coded as a "what would have been Magnezone" — narrative only, mechanically a Magneton)
final line: *"... he was right. The kind one. I should have listened the year he wrote it down."*

**Floor 3 — Rocket Grunt (ghost).**
*(no pre-battle line)*
team: Houndoom L66 · Crobat L66 · Mightyena-stand-in L66
final line: *"... we lost too. Everyone lost. He didn't even hate us at the end."*

**Floor 4 — Cooltrainer (ghost).**
*(no pre-battle line)*
team: Espeon L67 · Umbreon L67
final line: *"... I trained them well. We just had nowhere to go."*

**Floor 5 — Channeler (ghost).**
*(no pre-battle line)*
team: Gengar L68 · Misdreavus L68
final line: *"... I am a ghost trainer. I knew it before you did."*

**Floor 6 — Sleeping Old Man (ghost).**
*(no pre-battle line, the trainer is asleep — battle triggers automatically)*
team: Snorlax L68
final line: *"... still asleep. He was always asleep. Let him keep dreaming. The world is kinder there."*

**Floor 7 — Researcher (ghost).**
*(no pre-battle line)*
team: Porygon2 L69 · Alakazam L70
final line: *"... I made him because I could. I never once thought to ask if I should."*

**Floor 8 — Silph CEO (ghost).**
*(no pre-battle line, but a portrait of Mr. Silph hangs above his head, cracked)*
team: Aerodactyl L70 · Gyarados L70 · Tyranitar L72
final line: *"... we paid to bring it forward. The future. We paid everything for it. Then it came."*

Total: ~1.6 KB of text + ~800 bytes trainer data.

### 22A.4 — The Curator (Pewter Memorial)

The single living human in the Cinderspire. He doesn't fight; he
speaks. Three dialogue trees.

**First visit (player arrives at Pewter Memorial, Map 4):**
> Curator: There aren't many people anymore. Aren't many anything
> anymore. So forgive me if I stare.
>
> Curator: You're not from here, are you. No — I can tell. Your eyes
> haven't gotten dark yet.
>
> Curator: I keep the journals here. The old ones, before. They were
> in a building that is now under water. I copied them by hand. I am
> not a fast copier. But I had time.
>
> Curator: The archive's locked. I keep it locked because the
> letters are the only thing in here that aren't already ruined. You
> can come back when you've proven you'll be careful with them.
>
> Curator: Defeat one of the trainers in the broken tower. The shades.
> Any one of them. Then come back. I'll know.

**After one ghost defeat (archive unlocks):**
> Curator: You came back. Good. The shades told me. They tell me
> everything, on slow days.
>
> Curator: The archive is open. Read them in order. Don't try to read
> them all at once. They don't want to be read like that.
>
> Curator: I'll be here when you're done. I am always here.

**After Mewtwo encounter (final dialogue, branches on path):**

> Curator: You smell like static. The kind that lingers after a
> storm.
>
> *(if Mewtwo speech path:)*
>
> Curator: ... did you read the last entry? The one signed nothing?
>
> Player: *(yes / no)*
>
> Curator: He was a friend of mine. The man who wrote it. He died
> the winter after he wrote it.
>
> Curator: But I think — I think you read it to the one it was
> meant for. I think that's what you just did. So thank you.
>
> Curator: Tell your green friend to take you home. There is nothing
> left for you here.
>
> *(if Mewtwo battle path:)*
>
> Curator: You won, didn't you.
>
> Curator: ... I will not ask what you said to it before. I do not
> want to know. I am glad you walked out.
>
> Curator: Tell your green friend to take you home. There is nothing
> left for you here.

Total: ~1.6 KB of dialogue.

### 22A.5 — Celebi's narration arc

Celebi speaks throughout both trips. Style: italic green text,
always third-person about itself, no contractions, never raises its
voice. Below: Celebi's lines in **order of appearance**, both
trips. Each line is ~50-100 bytes.

**(Shrine, first time-travel selection:)**
> Celebi: *... where you want to go, the wind already knows. Pick.*

**(Verdant Cradle, Map 1 — arrival:)**
> Celebi: *We are early. This is before the wars. This is before the
> houses. The Pokémon here do not yet know what humans are.*
>
> Celebi: *Be gentle. The thread that brought us here is thin.*

**(Verdant Cradle, after healing the wounded Lapras:)**
> Celebi: *... it remembers you, now. Even after we leave. Even
> after this place forgets that we were here.*

**(Verdant Cradle, in the Megafauna Plateau, seeing wild Aerodactyl:)**
> Celebi: *In your time they only know its bones. Here, it has eyes.
> It is watching us. It is, I think, curious.*

**(Verdant Cradle, on the First Shrine silence tile:)**
> Celebi: *... do nothing. That is the offering.*

**(Verdant Cradle, Heart of the Cradle, Mew descending:)**
> Celebi: *It sees you. Do not move suddenly. It has wanted, for a
> long time, to be seen back.*

**(Verdant Cradle, departure:)**
> Celebi: *This place will fade. It always does. Hold on.*

**(Cinderspire Tomorrow, Map 1 — arrival, Pallet ruins:)**
> Celebi: *Oh. Oh.*
>
> Celebi: *... I am sorry. I should not have brought you to this
> one. But you needed to see it. So we are here.*

**(Cinderspire Tomorrow, Viridian Husk, finding the half-buried PokéMart sign:)**
> Celebi: *This is the future where it goes wrong. Not the only one.
> But this is the loud one. The one that wants to be remembered.*

**(Cinderspire Tomorrow, Cerulean Hollow, the storm above the cave:)**
> Celebi: *... I cannot go closer. The grief here is too thick. Take
> me out, please.*

**(Cinderspire Tomorrow, Silph Spire, between ghost-trainer floors:)**
> Celebi: *They cannot see me. Only you. I think they would want me
> to leave them be.*

**(Cinderspire Tomorrow, The Roof, Mewtwo's first line:)**
> Celebi: *(silent — Celebi hides behind the player's collar)*

**(Cinderspire Tomorrow, after the Mewtwo encounter:)**
> Celebi: *It is not done. It will never be done. But you carry
> something out with you now.*

**(Shrine, after both trips complete, only triggers once:)**
> Celebi: *... thank you. I had not seen them, either of them. Not
> in any of my lives. You showed me. You showed both of them.*
>
> Celebi: *I do not have a gift for you. I am sorry. I have only
> what I was when you found me. Take that, if you will have it.*

Total: ~2 KB of narration.

### 22A.6 — Final ambient cameo (if user picks §20 question 10 yes)

If the player has caught Celebi + Mew + Mewtwo, a single one-time
cameo plays the next time they enter the Ilex shrine:

> *(The shrine glows. The three appear above it — Celebi between Mew
> and Mewtwo, all three in the same frame. They look at each other.
> Mew tilts its head; Mewtwo nods, once. Celebi spins in a small
> circle.*)
>
> *(Mew approaches the player and drops something at their feet.)*
>
> [Got a Lum Berry!]
>
> *(The three vanish. The shrine quiets.)*

Total: ~300 bytes.

### 22A.7 — Total prose word count

| Block | Approx bytes | Approx words |
| --- | ---: | ---: |
| Mansion journal continuation (7 entries) | ~5 KB | ~900 |
| Mewtwo monologue (both branches) | ~2 KB | ~360 |
| 8 ghost trainer final lines | ~1.6 KB | ~290 |
| Curator (3 trees) | ~1.6 KB | ~290 |
| Celebi narration (full arc) | ~2 KB | ~360 |
| Final ambient cameo | ~0.3 KB | ~50 |
| **TOTAL** | **~12.5 KB** | **~2 250 words** |

Matches the §3 budget allocation for "story text + dialogue."

This is roughly the prose density of a long short story. It's the
amount of writing where, if you sit down for two evenings with a
quiet head, you can revise the whole thing.

The drafts above are **rev 0**. Each line above is meant to start a
conversation with the user, not lock in tone.

## 22. Sources

- Celebi lore + Ilex shrine: [Bulbapedia — Ilex Forest shrine](https://bulbapedia.bulbagarden.net/wiki/Ilex_Forest_shrine), [Serebii — Celebi & GS Ball](https://www.serebii.net/crystal/celebi.shtml), [Bulbapedia — Time travel in Pokémon](https://bulbapedia.bulbagarden.net/wiki/Time_travel)
- Celebi-Giovanni HG/SS event (template for the time-travel mechanic): [Serebii — HG/SS Celebi Event](https://www.serebii.net/heartgoldsoulsilver/celebi.shtml)
- Mew lore: [Bulbapedia — Mew (Pokémon)](https://bulbapedia.bulbagarden.net/wiki/Mew_(Pok%C3%A9mon)), [Pokémon GO Hub — Lore of Mew](https://pokemongohub.net/post/wiki/the-lore-of-mew/), [Wikipedia — Mew](https://en.wikipedia.org/wiki/Mew_(Pok%C3%A9mon))
- Mewtwo lore: [Bulbapedia — Cerulean Cave](https://bulbapedia.bulbagarden.net/wiki/Cerulean_Cave), [Bulbapedia — Pokémon Mansion (Kanto)](https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_Mansion_(Kanto)), [Bulbapedia — Pokémon Mansion journals](https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_Mansion_journals), [Bulbapedia — Mew duo](https://bulbapedia.bulbagarden.net/wiki/Mew_duo), [ScreenRant — Who Created Mewtwo](https://screenrant.com/pokemon-mewtwo-creator-red-blue-game-world/)
- Cross-version wings: [Bulbapedia — Silver and Rainbow Wings](https://bulbapedia.bulbagarden.net/wiki/Silver_and_Rainbow_Wings), [Bulbapedia — Tower duo](https://bulbapedia.bulbagarden.net/wiki/Tower_duo)
- Existing precedent ROM hacks: [Polished Crystal — Celebi event with Giovanni-Mewtwo flashback (TV Tropes)](https://tvtropes.org/pmwiki/pmwiki.php/VideoGame/PokemonPolishedCrystal), [Crystal Clear — Mew/Mewtwo sidequest (TV Tropes)](https://tvtropes.org/pmwiki/pmwiki.php/VideoGame/PokemonCrystalClear), [Mystic Crystal](https://pokemongamehack.wordpress.com/2026/05/11/pokemon-mystic-crystal-gbc/), [Core Crystal](https://www.pokecommunity.com/threads/pokemon-core-crystal-v2-1-1.538077/)
- Post-apocalyptic narrative tropes: [TVTropes — After the End: Video Games](https://tvtropes.org/pmwiki/pmwiki.php/AfterTheEnd/VideoGames), [TVTropes — Ruins of the Modern Age](https://tvtropes.org/pmwiki/pmwiki.php/Main/RuinsOfTheModernAge), [Games Criticism — Beyond Barren Wastelands](https://gamescriticism.org/2024/09/06/bianchi-6-a/), [Lancaster eprints — Post-Apocalyptic Play](https://eprints.lancs.ac.uk/id/eprint/137221/1/Fraser_Post_apocalyptic_play_Edits_2FINAL.pdf)
- Pokémon Gen 2 species data structure / sizing: [Bulbapedia — Species data structure (Gen II)](https://bulbapedia.bulbagarden.net/wiki/Pok%C3%A9mon_species_data_structure_(Generation_II))

## 23. Bottom line

A 100–130 KB postgame event arc that:

- Adds Celebi as an in-game catchable through a 3-step key item chain
- Adds Mew via a "Trial of Compassion" non-combat puzzle in the
  Verdant Cradle (5–6 maps, ancient pre-civilization jungle)
- Adds Mewtwo via a confrontation arc in the Cinderspire Tomorrow
  (8–9 maps, dystopian future Kanto with extended Mansion journals)
- Adds **two paths** for Mewtwo — battle or speak — both catch the
  same mon, the difference is what the player saw before catching
- Provides diegetic versions of the cross-version Silver Wing
  (Gold-side Cinderspire scene) and Rainbow Wing (Silver-side
  Verdant scene), keeping vanilla NPC paths as fallback
- Uses zero new Pokémon species (all encounters are existing Gen 1/2
  dex)
- Fits in ~7 of 14 free banks, leaving ~7 banks (~112 KB) free for
  other postgame ideas
- Stays pure Gen 2 mechanically — no abilities, no forms, no new
  battle systems
- Bundles its save-format change with the other queued save-touching
  features

The single biggest authoring cost is the **writing** — the journal
continuation entries, the ghost trainer final lines, Mewtwo's
monologue, Celebi's narration. ~14 KB of text across the arc, but
each byte is load-bearing. This is the only part of the spec where
the *quality of words* directly determines whether the postgame
lands or feels hollow.

The second-biggest cost is **two new tilesets** — fresh pixel art for
Verdant and Cinderspire. Reusing Gen 2 metatile plumbing keeps the
implementation cost low, but the art still has to be made (or
sourced from a community artist, as with sprites).

Everything else is bounded and small.
