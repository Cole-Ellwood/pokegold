# Codebase Drift Diary: Choreography And Refusal

Date: 2026-04-26
Repo: C:\Users\lolno\Downloads\pokemon gold hack

Boundary: source-read wander only. This note is the only intended write.

Subject: movement bytecode, collision permission, followers, emotes, and the map
scripts where personality becomes little stage directions.

## Starting Point

I wanted to avoid the warm grooves.

The earlier notes had already gone into Super Game Boy packets, ambient systems
that make the world keep living, and souvenirs/names. So I looked for something
less romantic. Movement seemed safe. Technical. Boring enough to resist me.

That was wrong.

Movement is where the game becomes bodily.

Not in a grand way. It is all packed bytes and object fields:
`OBJECT_WALKING`, `OBJECT_STEP_TYPE`, `OBJECT_ACTION`, `OBJECT_DIRECTION`,
`OBJECT_STEP_DURATION`. But that is the layer where the player feels whether
the world is solid, whether an NPC has urgency, whether a guide is dragging you
somewhere, whether Mary is flustered, whether ice has made your decision
irreversible for a few frames.

The emotional thing, if I can use that word loosely, was not "wonder" this time.
It was a kind of respect for the amount of refusal required before motion can
happen.

## Read Set

- `macros/scripts/movement.asm`
- `home/movement.asm`
- `engine/overworld/movement.asm`
- `engine/overworld/player_movement.asm`
- `engine/overworld/npc_movement.asm`
- `engine/overworld/map_objects.asm`
- `engine/overworld/map_object_action.asm`
- `engine/overworld/player_object.asm`
- `engine/overworld/scripting.asm`
- `constants/map_object_constants.asm`
- `constants/collision_constants.asm`
- `data/collision/collision_permissions.asm`
- `data/collision/collision_stdscripts.asm`
- `data/sprites/map_objects.asm`
- `data/sprites/emotes.asm`
- `engine/events/forced_movement.asm`
- `maps/CherrygroveCity.asm`
- `maps/VioletCity.asm`
- `maps/TeamRocketBaseB2F.asm`
- `maps/LancesRoom.asm`

## Movement Is Bytecode

`macros/scripts/movement.asm` is the little language.

Directional commands are packed in groups:

- `turn_head`
- `turn_step`
- `slow_step`
- `step`
- `big_step`
- slide steps
- jump steps
- `turn_away`, `turn_in`, `turn_waterfall`

Then the language gets stranger:

- `remove_sliding`
- `fix_facing`
- `show_object`
- `step_sleep`
- `teleport_from`
- `skyfall`
- `step_dig`
- `fish_got_bite`
- `show_emote`
- `tree_shake`
- `rock_smash`
- player-only turbo steps

I like that "walk one tile" and "the whole screen shakes" live in the same
movement command vocabulary. The language does not separate ordinary body motion
from theatrical punctuation. A person walking, a question mark appearing, a tree
shaking, a teleport spin: all are choreography.

That is the first thing that caught.

## The Player Moves Only After The Map Fails To Stop Them

`DoPlayerMovement` in `engine/overworld/player_movement.asm` feels like a court
of appeals.

The path is roughly:

- read input
- check forced movement
- translate input into direction, facing, x/y delta, tile pointer
- check tile behavior
- maybe just turn
- try stepping
- try jumping
- check warp
- otherwise stand or bump

The simple player feeling is "I pressed right." The code's actual question is:
"After tile permissions, NPCs, ledges, edge warps, surf state, ice state, bike
state, downhill state, and turning rules, is right allowed to become a step?"

Freedom is not the default. Motion is what remains after refusal.

That sounds heavier than the code maybe deserves, but it is true mechanically.
The map is a set of permissions and exceptions. The player only experiences
fluid motion because the refusal checks are consistent enough to disappear.

The bit I liked more than expected is `CheckTurning`. It lets a directional tap
change facing without moving. That is tiny, but it matters. The player can look
before acting. A turn is recognized as its own action, not a failed walk.

There is a design ethic in that.

## Collision Is Not Just Wall Or Floor

`constants/collision_constants.asm` looks plain at first: floor, wall, cut tree,
water, ice, doors, counters, ledges, side walls.

Then the table gets full of half-meaning:

- unused
- garbage
- talkable wall
- land tile that still has special behavior
- water tile with talk
- side walls and side buoys

`data/collision/collision_permissions.asm` compresses every collision byte into
one of a few permission categories: land, water, wall, sometimes with `TALK`.

The interesting thing is that "wall" is not only physical. Bookshelves, PCs,
radios, town maps, mart shelves, TVs, windows, incense burners: all wall-like
because you cannot walk through them, but some are also conversational because
the A button can talk to them.

`data/collision/collision_stdscripts.asm` makes that explicit. Certain collision
tiles route to standard scripts: bookshelf, PC, radio, town map, shelf, TV,
window, incense burner.

So the map has grammar:

- passable
- impassable
- impassable but readable
- passable but consequential
- directional
- slippery
- jumpable

That is better than "collision." Collision is too blunt a word for a tile that
can say "stop here and read me."

## Step Type Versus Object Action

This was the cleanest architectural pleasure in the wander.

`HandleObjectStep` does two things:

1. `HandleStepType`
2. `HandleObjectAction`

Step type is the physics/time state: sleep, walk, jump, turn, bump, teleport,
skyfall, rock smash, tracking object, screen shake, delete.

Object action is the visual facing/animation: stand, step, bump, spin, fishing,
shadow, emote, bounce, weird tree, boulder dust, grass shake.

That split feels right in the hand. A body can be in a step type while its
visible face is decided separately. The same object can be frozen, invisible,
offscreen, standing, spinning, tracking, or acting out a special effect.

It is not a modern abstraction. It is not named with tidy architecture words.
But the division is real and useful.

The wrong turn here would be to say "old assembly is messy." Some of it is.
But this part has a sturdy internal taste: state machine for what happens over
frames, action table for what tile frame to show.

## Emotes Are Objects

I had somehow never internalized this properly.

An emote is not just a UI sprite over a head. `SpawnEmote` copies temp object
data and creates a new object with:

- vtile `$f8`
- `PAL_OW_EMOTE`
- `SPRITEMOVEDATA_EMOTE`

The emote movement data marks it as `WONT_DELETE | FIXED_FACING | SLIDING |
EMOTE_OBJECT`, high priority, with `OBJECT_ACTION_EMOTE`.

The emote then uses `MovementFunction_Emote`, which initializes tracking fields
so the tiny object follows the target object's sprite coordinates with a
negative y offset. `DespawnEmote` scans object structs for `EMOTE_OBJECT_F` and
clears them.

That is so much more physical than "draw an icon."

A question mark is a temporary object attached to your existence.

Again, not a task, not a requested design change. I just liked it. The game does
not have a separate metaphysical category for expression. Expression is a
thing with coordinates, flags, priority, and deletion rules.

## Followers Are Queues Of Borrowed Steps

Following is a little stranger.

`Script_follow` stores leader and follower object IDs through `StartFollow`.
The follower's movement type becomes `SPRITEMOVEDATA_FOLLOWING`. Then movement
commands from the leader can be copied into `wFollowMovementQueue` by
`ApplyMovementToFollower`.

The queue intentionally ignores some commands:

- sleep
- end
- stop
- bump
- commands before slow-step

The follower does not imitate everything. It imitates motion.

I like that distinction. A follower should inherit the path, not the leader's
whole expressive state. Otherwise every scripted tour would become nonsense.

`QueueFollowerFirstStep` handles the initial offset. If leader and follower
begin on the same coordinate, the queue length gets `-1`. If not, it queues the
first step needed to close distance.

This is the kind of code where I feel the old machine's constraints as a kind of
choreographer. The system does not understand following as a relationship. It
understands a delayed movement queue. But to the player, an elder leads you
around Cherrygrove. Lance guides you toward the Hall of Fame. Mary tries to
follow and gets left behind.

The queue is enough.

## Map Scripts As Stage Directions

Once I had movement bytecode in my head, the map scripts changed.

The Cherrygrove guide gent tour is a whole civic ritual:

- `playmusic MUSIC_SHOW_ME_AROUND`
- `follow CHERRYGROVECITY_GRAMPS, PLAYER`
- `applymovement` through each stop
- turn the player toward the relevant building or sea
- talk
- stop follow
- restart map music
- have him walk away and disappear through a door

I used to remember that tour as text plus a nuisance. In source, it is a small
piece of theater about a town introducing itself by moving your body through it.

Earl in Violet is funnier because the movement data itself is personality.

`VioletCitySpinningEarl_MovementData` is just repeated `turn_head` commands:
down, left, up, right, again, again. His eccentricity is not only in the text.
It is in the spin loop.

Mary in Lance's room may be the best small example. She rushes in with
`big_step`, yields to Oak, interviews the player, tries to follow, gets shocked,
then runs back and forth:

`big_step RIGHT`, `big_step RIGHT`, `big_step LEFT`, `big_step LEFT`, etc.

The script does not need a paragraph saying she is flustered. Her movement data
is flustered.

That is the second real catch of this wander.

Text gives characters propositions. Movement gives them nerves.

## The Boring Part

Some of this was boring.

The collision permission table is long. The object action table is long. The
step functions are long. Reading offsets and flags for map object structs has a
gray texture after a while.

I am noting that because the previous notes had more immediate glow. This one
had stretches where my attention went flat, and then a single routine would make
the flatness worth it.

The movement system is not pretty in the same way SGB packets were pretty. It
is practical. Dense. It earns moments of grace by doing a lot of unglamorous
coordination.

That may be the honest admiration here: not "beautiful code" as a constant
condition, but beauty as a thing that occasionally emerges from labor.

## A Small Concern I Am Not Chasing

I noticed the custom player turbo movement additions:

- `movement_player_turbo_step_down`
- `movement_player_turbo_step_up`
- `movement_player_turbo_step_left`
- `movement_player_turbo_step_right`
- `STEP_PLAYER_TURBO`
- `STEP_PLAYER_TURBO_VECTOR`

This is active hack work, and I did not inspect it as a bug hunt. I only noted
that it is threaded through the same bytecode and step-vector machinery as
vanilla movement. That seems like the right kind of integration shape, but I am
not making a correctness claim. This diary is not verification.

Do not let a poetic note masquerade as an audit.

## What I Think I Learned

The previous note said memory equals selection with restraint.

This one says motion equals permission plus performance.

Permission: collision, tile type, NPC occupancy, movement radius, screen edge,
surf/land rules, ledge direction, warp facing.

Performance: step type, object action, facing frame, emote object, follower
queue, map-script choreography.

The player only sees one smooth layer. The code is two layers constantly
reconciling: what may happen, and how it should look if it does.

Something about that feels close to the project as a whole. This hack keeps
asking how to make Pokemon Gold dangerous again without cheating. That is also
permission plus performance. The boss may only act on fair information, but the
fight still has to look and feel scary.

Maybe that is why this movement trail caught. It is the same problem in tile
form.

The map must stop you honestly. Then it must make the stopping feel like a
world, not a rulebook.

## No Task

No code recommendation.

No cleanup request.

No claim that movement is bug-free.

Just this: do not underestimate the map-choreography layer when thinking about
the feel of this hack. Bosses and balance carry the headline promise, but
Pokemon Gold's body-feel lives down here too: taps that turn without walking,
bumps that make a sound, NPCs who spin, guides who make you follow, emotes that
become objects, walls that can be read.

The world is made of refusals that learned to act natural.

