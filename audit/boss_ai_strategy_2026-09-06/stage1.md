# Stage 1: shared public damage and survival facts

Implementation and acceptance record for stage 1 of the five-stage roadmap.
Final independent approval and exact artifact identity are recorded separately
in `stage1_review.md` and `stage1_manifest.json` when complete.

## Scope and decisions

| Unit | Decision and evidence |
|---|---|
| Arithmetic | One direction-free, 16-bit kernel follows actual combat integer ordering, joint one-time stat truncation, screens, known item caps/order, weather, type rows, and deterministic type passives. Per-hit HP changes update Ice thresholds. HP-loss envelopes cap overkill at starting HP. |
| Public construction | Own stats/items are known. Player offenses/defenses assume DV8 and use public species, level, stages and status. Raw Outrage category ties remain special. No hidden player item, stat, DV, badge or pending action is read. Transform ambiguity is explicit. |
| Hit/order/survival | Separate accuracy/priority and per-hit Psychic/known-own Focus Band thresholds. Thunder sunlight preprocessing, rain, Fly/Dig eligibility, Lock-On, X Accuracy, Foresight, accuracy stages, BrightPowder and Flying fractions follow combat. Zero-power actions have zero damage-negation/survival metadata. Future Protect/Endure is a successor action, not a promise inferred from transient flags. |
| KO consumers | Current, available-moveset and lookahead KO use outgoing minimum. Revealed priority uses incoming maximum. Both use exact current HP; accuracy zero and fainted HP cannot establish action pressure. Unsupported outgoing is not a KO; incoming uncertainty is conservative. Single hits stop at Substitute; unknown multi-hit incoming may reach real HP. |
| Removed duplication | The earlier unused fixed-only helper is retired. Its 48 current/available-moveset boundary cases remain. Repeated Pursuit contexts restore their minimum multiplier. |
| Information boundary | No-cheat audit now includes kernel/adapters and forbids direct private player stats/DVs/raw stats. Setup Speed headroom uses the same public speed estimate; the prior exact-speed exception is removed. Hidden-state invariance tests alter private stats, DVs, items and pending input after combat-reference preparation. |
| Mechanics documentation | Correct raw Outrage/Dragon Dance choice and ties, priority ranks/Vital Throw, damage order/caps, post-roll Pursuit/Fly/Dig effects, absence of modern Sandstorm Rock SpDef boost, and actual Focus Band30/256. Source comments/generator output agree. |

## Retained decisions and ordered follow-up

- Preserve the earlier approved consistency pass, authored tier/style/Haki gates,
  hard move-availability gates, Perish emergency escape and existing plan state.
  This stage changes their KO premises, not the authored difficulty goals.
- Keep nonlethal pressure, strong-matchup status backstops and bench risk heuristics
  until stage 2 prices actions jointly. They are preferences, not damage numbers.
- Keep conditional/ramping/counter/charge cases explicit unknowns until an action
  state supports them. This is not a harmless-zero assumption. Copied stats and
  multi-hit Substitute HP need a successor context or contextual observations.
- Keep crits, action denial, secondary effects, recoil/healing and future
  Protect/Endure distinct from noncritical on-hit damage. Stage 2/3 must value
  their branches; this stage does not claim guaranteed outcomes or full search.
- Keep no added persistent WRAM/save data. The public context is42 stack bytes;
  call frames/math scratch remain part of later measured stack/cycle acceptance.

The broader goal remains all five stages. Stage1 arithmetic or helper tests do
not establish joint action value, successor-search correctness, learned outcomes,
win-rate improvement or strategic acceptance across real boss rosters.

## Supported move inventory

This lists every current move table row. Direct means an amount conditional on
successful unblocked hits, not an unconditional guarantee. Status actions are
handled by policy/effect semantics and return no supported damage estimate.
Guillotine and Bide also have zero table power, but their effects can deal damage;
they are explicit unsupported damaging effects, not status moves.
SolarBeam needs sun/already-charged state; Dream Eater/Snore need public sleep;
multi-hit is unknown against Substitute. Pursuit retains1x..2x uncertainty.
Transform makes ordinary player stat estimates unsupported in both directions.

### Direct on-hit amount (115)

`IRON_HEAD`, `KARATE_CHOP`, `MEGA_PUNCH`, `PAY_DAY`, `FIRE_PUNCH`, `ICE_PUNCH`, `THUNDERPUNCH`, `SCRATCH`, `VICEGRIP`, `CUT`, `WING_ATTACK`, `BIND`, `SLAM`, `VINE_WHIP`, `MEGA_KICK`, `JUMP_KICK`, `ROLLING_KICK`, `HEADBUTT`, `HORN_ATTACK`, `TACKLE`, `BODY_SLAM`, `WRAP`, `TAKE_DOWN`, `THRASH`, `DOUBLE_EDGE`, `POISON_STING`, `BITE`, `SONICBOOM`, `ACID`, `EMBER`, `FLAMETHROWER`, `WATER_GUN`, `HYDRO_PUMP`, `SURF`, `ICE_BEAM`, `BLIZZARD`, `PSYBEAM`, `BUBBLEBEAM`, `AURORA_BEAM`, `HYPER_BEAM`, `PECK`, `DRILL_PECK`, `SUBMISSION`, `LOW_KICK`, `SEISMIC_TOSS`, `STRENGTH`, `ABSORB`, `MEGA_DRAIN`, `RAZOR_LEAF`, `PETAL_DANCE`, `DRAGON_RAGE`, `FIRE_SPIN`, `THUNDERSHOCK`, `THUNDERBOLT`, `THUNDER`, `ROCK_THROW`, `CONFUSION`, `PSYCHIC_M`, `QUICK_ATTACK`, `RAGE`, `NIGHT_SHADE`, `SELFDESTRUCT`, `EGG_BOMB`, `LICK`, `SMOG`, `SLUDGE`, `BONE_CLUB`, `FIRE_BLAST`, `WATERFALL`, `CLAMP`, `SWIFT`, `CONSTRICT`, `HI_JUMP_KICK`, `LEECH_LIFE`, `BUBBLE`, `DIZZY_PUNCH`, `CRABHAMMER`, `EXPLOSION`, `ROCK_SLIDE`, `HYPER_FANG`, `TRI_ATTACK`, `SUPER_FANG`, `SLASH`, `STRUGGLE`, `THIEF`, `FLAME_WHEEL`, `AEROBLAST`, `POWDER_SNOW`, `MACH_PUNCH`, `FAINT_ATTACK`, `SLUDGE_BOMB`, `MUD_SLAP`, `OCTAZOOKA`, `ZAP_CANNON`, `ICY_WIND`, `OUTRAGE`, `GIGA_DRAIN`, `FALSE_SWIPE`, `SPARK`, `STEEL_WING`, `SACRED_FIRE`, `DYNAMICPUNCH`, `MEGAHORN`, `DRAGONBREATH`, `RAPID_SPIN`, `IRON_TAIL`, `METAL_CLAW`, `VITAL_THROW`, `CROSS_CHOP`, `CRUNCH`, `EXTREMESPEED`, `ANCIENTPOWER`, `SHADOW_BALL`, `ROCK_SMASH`, `WHIRLPOOL`.

### Conditional on-hit amount (19)

`DOUBLESLAP`, `COMET_PUNCH`, `GUST`, `STOMP`, `DOUBLE_KICK`, `FURY_ATTACK`, `TWINEEDLE`, `PIN_MISSILE`, `SOLARBEAM`, `EARTHQUAKE`, `SPIKE_CANNON`, `DREAM_EATER`, `BARRAGE`, `FURY_SWIPES`, `BONEMERANG`, `SNORE`, `BONE_RUSH`, `PURSUIT`, `TWISTER`.

### Explicitly unsupported damaging effect (25)

`GUILLOTINE`, `BIDE`, `RAZOR_WIND`, `FLY`, `HORN_DRILL`, `COUNTER`, `FISSURE`, `DIG`, `SKULL_BASH`, `FOCUS_PUNCH`, `SKY_ATTACK`, `PSYWAVE`, `TRIPLE_KICK`, `FLAIL`, `REVERSAL`, `ROLLOUT`, `FURY_CUTTER`, `RETURN`, `PRESENT`, `FRUSTRATION`, `MAGNITUDE`, `HIDDEN_POWER`, `MIRROR_COAT`, `FUTURE_SIGHT`, `BEAT_UP`.

### Status/non-damage action (95)

`SWORDS_DANCE`, `WHIRLWIND`, `SAND_ATTACK`, `TAIL_WHIP`, `LEER`, `GROWL`, `ROAR`, `SING`, `SUPERSONIC`, `DISABLE`, `MIST`, `LEECH_SEED`, `GROWTH`, `POISONPOWDER`, `STUN_SPORE`, `SLEEP_POWDER`, `STRING_SHOT`, `THUNDER_WAVE`, `TOXIC`, `HYPNOSIS`, `MEDITATE`, `AGILITY`, `TELEPORT`, `MIMIC`, `SCREECH`, `DOUBLE_TEAM`, `RECOVER`, `HARDEN`, `MINIMIZE`, `SMOKESCREEN`, `CONFUSE_RAY`, `WITHDRAW`, `DEFENSE_CURL`, `BARRIER`, `LIGHT_SCREEN`, `HAZE`, `REFLECT`, `FOCUS_ENERGY`, `METRONOME`, `MIRROR_MOVE`, `AMNESIA`, `SOFTBOILED`, `GLARE`, `POISON_GAS`, `LOVELY_KISS`, `TRANSFORM`, `SPORE`, `FLASH`, `SPLASH`, `ACID_ARMOR`, `REST`, `SHARPEN`, `CONVERSION`, `SUBSTITUTE`, `SKETCH`, `SPIDER_WEB`, `MIND_READER`, `NIGHTMARE`, `CURSE`, `CONVERSION2`, `COTTON_SPORE`, `SPITE`, `PROTECT`, `SCARY_FACE`, `SWEET_KISS`, `BELLY_DRUM`, `SPIKES`, `FORESIGHT`, `DESTINY_BOND`, `PERISH_SONG`, `DETECT`, `LOCK_ON`, `SANDSTORM`, `ENDURE`, `CHARM`, `SWAGGER`, `MILK_DRINK`, `MEAN_LOOK`, `ATTRACT`, `SLEEP_TALK`, `HEAL_BELL`, `SAFEGUARD`, `PAIN_SPLIT`, `BATON_PASS`, `ENCORE`, `SWEET_SCENT`, `MORNING_SUN`, `SYNTHESIS`, `MOONLIGHT`, `RAIN_DANCE`, `SUNNY_DAY`, `PSYCH_UP`, `DRAGON_DANCE`, `CALM_MIND`, `QUIVER_DANCE`.

## Validation

`pokegold_stage1_fixtures.json` and `pokegold_trace_stage1_fixtures.json` record
full real-ROM policy regressions and damage comparisons. The reference runs
combat DamageStats/DamageCalc/Stab or ConstantDamage/ResetTypeMatchup, including
actual post-roll commands. Only endpoint roll scaling and aggregate HP clamping
are scalar test math. Independent CheckHit/GetMovePriority calls check metadata.
Known item, byte truncation, screens, low-HP passive, exact fixed HP, multi-hit,
Substitute, repeated context, copied-stat and hidden-noise cases cover boundaries.

The only prior expectation changes are the two Pidgey20 Tackle lookahead controls
against Snorlax80 at40/41HP: -4 became -2 because these are not KOs. Existing
nonlethal preference remains. Independent review agreed this follows combat.

Gold, Silver, debug and trace must all build; `stage1_checks.json` records the
12 applicable information-boundary, gating, trace, memory, indexing, contract,
preference, cross-bank and lookahead audits. Broader strategic metrics follow in
stage5, not inferred from these tests.
