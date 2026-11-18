#!/usr/bin/env bash
# In-game check for YUNG's Better Dungeons (slice 1): a dungeon from the jar's own
# templates, assembled by this port's structure type, placed in a real level.
#
# The package is a flat `.hmod` the launcher compiles into the game, so GAME must name a
# game the launcher built with it:
#
#   ports/tools/launcher-game.sh run betterdungeons
#
# which builds (or reuses) the export and runs this script inside a build-slot lease with
# GAME/CTL/CONTROL_GAME/RES/E2E_TMP/SOCK already exported. Everything lives under
# `~/.cache/horizon-e2e/`; `/tmp` is a 7.5 GB tmpfs that has been full.
#
# What only a game can prove, and what this script asserts:
#
#  A. `/place structure betterdungeons:small_dungeon 0 64 0` **succeeds** — the engine
#     resolves the data-pack structure's `"type": "betterdungeons:small_dungeon_type"` to
#     this port's `StructureType`, runs its assembly and places its pieces. The start box
#     is force-loaded and the chunk settled *before* the place (the trap). This leg runs
#     first so that a control run fails on the structure, not on a missing command.
#  B. The blocks are the dungeon's: before the place the search box holds no stone bricks
#     and no polished andesite; after it, the shell's stone bricks, polished andesite,
#     mossy cobblestone and cave air are there, the support-leg processor has replaced the
#     yellow glass, the ceiling-lamp processor the cyan glass, and the decoration wrote a
#     mob spawner whose entity is one of the dungeon's mobs, plus at most two chests
#     carrying `minecraft:chests/simple_dungeon`.
#  C. `/betterdungeons status` answers: the registered type id, 16 templates, 2 pools,
#     4 processor lists, and the deterministic sample assembly of 5 pieces. Without the
#     package the command does not exist.
#  D. The control run — the same Nightly without the package, same world name and seed —
#     reads the command as unknown, answers `/place structure` with
#     `There is no structure with type "betterdungeons:small_dungeon"`, and leaves the
#     search box empty. Those are the two assertions that must fail there.
#
# SELFTEST=1 inverts C's stone-brick assertion (the box must still be empty), which must
# fail: that proves the assertion is alive.
#
#   GAME=$CONTROL_GAME tools/e2e.sh          # the control leg: must FAIL (EXIT:1)
#   SELFTEST=1 tools/e2e.sh                  # the inverted assertion: must FAIL
set -Eeuo pipefail
trap 'echo "FAILED at line $LINENO: $BASH_COMMAND" >&2' ERR

CLONE=${CLONE:-/home/adlf/Desktop/all_the_mods_10_rust_rewrite}
PORT=$CLONE/ports/betterdungeons
EVIDENCE=${EVIDENCE:-$CLONE/ports/_shared/evidence/betterdungeons-e2e}
CTL=${CTL:-/home/adlf/.cache/horizon-e2e/0b14f8a/betterdungeons/horizon-ctl}
GAME=${GAME:-/home/adlf/.cache/horizon-e2e/0b14f8a/betterdungeons/horizon-client}
CONTROL_GAME=${CONTROL_GAME:-/home/adlf/.cache/horizon-e2e/0b14f8a/control/horizon-client}
RES=${RES:-${HORIZON_RES:-/home/adlf/.cache/horizon-e2e/root/data/horizon-launcher/versions/nightly-2026-11-18-0b14f8a/.local/horizon-client/26.3}}
SELFTEST=${SELFTEST:-0}
LEG=${LEG:-launcher}
[ "$GAME" = "$CONTROL_GAME" ] && LEG=${LEG_OVERRIDE:-launcher-control}
SOCK=${SOCK:-${E2E_TMP:-$HOME/.cache/horizon-e2e/scratch}/betterdungeons-$LEG.sock}
SITE=0

for f in "$CTL" "$GAME"; do
    [ -x "$f" ] || { echo "missing binary: $f" >&2; exit 1; }
done
[ -d "$RES/assets" ] || { echo "missing prepared resources: $RES" >&2; exit 1; }

mkdir -p "$EVIDENCE" "$(dirname "$SOCK")"
LOG=${LOG:-$EVIDENCE/e2e-$LEG.log}
# The log is the evidence: everything the run says goes to it, and the last line is the exit
# status `check-e2e-logs.py` reads.
exec > >(tee "$LOG") 2>&1

SCRATCH=$(mktemp -d "${E2E_TMP:-$HOME/.cache/horizon-e2e/scratch}"/betterdungeons-$LEG.XXXXXX)
export HORIZON_HOME=$SCRATCH/home
export HORIZON_LAUNCHER_HOME=$SCRATCH/launcher
export XDG_DATA_HOME=$SCRATCH/data
export XDG_CONFIG_HOME=$SCRATCH/config
export HORIZON_NO_AUDIO=1
mkdir -p "$HORIZON_HOME" "$XDG_DATA_HOME" "$XDG_CONFIG_HOME"
# The game writes `saves/` under its working directory, so run from the scratch dir: a world
# left in the campaign root would make the next run open the previous dungeon (this happened).
cd "$SCRATCH"
rm -f "$SOCK"

ctl() { "$CTL" --socket "$SOCK" "$@"; }
fail() { echo "FAIL: $*" >&2; exit 1; }
say() { echo "== $* =="; }
count() { ctl find-block "$1" 48 | jq -r '.count'; }

# Every run ends with its status line, so the artefact proves the verdict.
finish() {
    local status=$?
    ctl quit >/dev/null 2>&1 || true
    sleep 1
    rm -rf "$SCRATCH" || true
    echo "E2E EXIT:$status"
}
trap finish EXIT

say "leg $LEG: $GAME"
rm -f "$SOCK"
ctl launch --game "$GAME" --headless --resources "$RES" --no-pause >/dev/null
[ -S "$SOCK" ] || fail "the game did not start: no socket at $SOCK"
echo "release: $(ctl hello | jq -r '.release')"

ctl open BetterDungeons 20261105 creative >/dev/null
ctl wait-ready 400 >/dev/null
ctl command "gamerule spawn_mobs false" >/dev/null

say "A. the start box is loaded, then /place structure"
ctl tp "$SITE" 64 "$SITE" >/dev/null
ctl wait 40 >/dev/null
# Clear any earlier force loads, then mark the start box: the reply is the proof the
# box the structure writes into is loaded *before* the place (the trap).
ctl command "forceload remove all" >/dev/null
FORCELOAD=$(ctl command "forceload add -24 -24 24 24" | jq -r '.chat | join("\n")')
echo "$FORCELOAD"
echo "$FORCELOAD" | grep -q 'force loaded' || fail "the start box was not force-loaded"
ctl wait 40 >/dev/null
BEFORE_BRICKS=$(count stone_bricks)
BEFORE_ANDESITE=$(count polished_andesite)
BEFORE_SPAWNERS=$(count spawner)
echo "before: stone_bricks=$BEFORE_BRICKS polished_andesite=$BEFORE_ANDESITE spawners=$BEFORE_SPAWNERS"
[ "$BEFORE_BRICKS" = 0 ] || fail "stone bricks were already in the search box before the place"
[ "$BEFORE_ANDESITE" = 0 ] || fail "polished andesite was already in the search box before the place"

PLACED=$(ctl command "place structure betterdungeons:small_dungeon $SITE 64 $SITE" | jq -r '.chat | join("\n")')
echo "place reply: $PLACED"
ctl wait 20 >/dev/null

say "B. the dungeon's own blocks"
BRICKS=$(count stone_bricks)
ANDESITE=$(count polished_andesite)
MOSSY=$(count mossy_cobblestone)
CAVE_AIR=$(count cave_air)
SPAWNERS=$(count spawner)
CHESTS=$(count chest)
YELLOW=$(count yellow_stained_glass)
CYAN=$(count cyan_stained_glass)
echo "after: stone_bricks=$BRICKS polished_andesite=$ANDESITE mossy_cobblestone=$MOSSY cave_air=$CAVE_AIR"
echo "       spawners=$SPAWNERS chests=$CHESTS yellow_glass=$YELLOW cyan_glass=$CYAN"

if [ "$SELFTEST" = 1 ]; then
    say "selftest: the search box must still be empty (must fail)"
    [ "$BRICKS" -ge 8 ] && fail "SELFTEST: the dungeon is in the box, so the assertion is alive" || true
    echo "SELFTEST unexpectedly found an empty box"
    exit 0
fi

echo "$PLACED" | grep -q 'Generated structure "betterdungeons:small_dungeon"' \
    || fail "the engine did not place the structure: $PLACED"
[ "$BRICKS" -ge 8 ] || fail "only $BRICKS stone bricks: the shell did not place"
[ "$ANDESITE" -ge 2 ] || fail "only $ANDESITE polished andesite: the shell floor did not place"
[ "$MOSSY" -ge 20 ] || fail "only $MOSSY mossy cobblestone: the dungeon's walls did not place"
[ "$CAVE_AIR" -ge 100 ] || fail "only $CAVE_AIR cave air: the rule processor did not run"
[ "$YELLOW" = 0 ] || fail "$YELLOW yellow stained glass left: the leg processor did not run"
[ "$CYAN" = 0 ] || fail "$CYAN cyan stained glass left: the ceiling-lamp processor did not run"
[ "$SPAWNERS" -ge 1 ] || fail "no mob spawner: the spawner processor did not run"
[ "$CHESTS" -ge 1 ] || fail "no chest: the chest cap kept none"
[ "$CHESTS" -le 2 ] || fail "$CHESTS chests: the structure-wide cap of 2 did not hold"

SPAWNER_POS=$(ctl find-block spawner 48 | jq -r '.nearest[0].pos | join(" ")')
echo "the spawner is at $SPAWNER_POS"
SPAWNER_DATA=$(ctl command "data get block $SPAWNER_POS SpawnData" | jq -r '.chat | join("\n")')
echo "spawner entity: $SPAWNER_DATA"
echo "$SPAWNER_DATA" | grep -qE 'id: "minecraft:(skeleton|zombie|spider)"' \
    || fail "the spawner carries no dungeon mob: $SPAWNER_DATA"

CHEST_POS=$(ctl find-block chest 48 | jq -r '.nearest[0].pos | join(" ")')
CHEST_DATA=$(ctl command "data get block $CHEST_POS LootTable" | jq -r '.chat | join("\n")')
echo "chest loot: $CHEST_DATA"
echo "$CHEST_DATA" | grep -q 'minecraft:chests/simple_dungeon' \
    || fail "the chest carries no loot table: $CHEST_DATA"

say "C. /betterdungeons status"
STATUS=$(ctl command "betterdungeons status" | jq -r '.chat | join("\n")')
echo "$STATUS"
if [ "$SELFTEST" != 1 ]; then
    echo "$STATUS" | grep -q 'type: betterdungeons:small_dungeon_type' \
        || fail "the readout does not name the registered structure type"
    echo "$STATUS" | grep -q '16 templates, 2 pools, 4 processor lists' \
        || fail "the readout does not report what the package carries"
    echo "$STATUS" | grep -q 'sample: chunk (2, 3), seed 20261105 -> 5 pieces' \
        || fail "the readout does not report the deterministic sample assembly"
    echo "$STATUS" | grep -q 'last refusal' \
        && fail "the generator recorded a refusal: $STATUS"
fi

say "D. the same world without the package"
ctl quit >/dev/null 2>&1 || true
sleep 2
# A stopped game leaves its socket file behind; a second launch on the same path refuses it.
rm -f "$SOCK"
SCRATCH2=$(mktemp -d "${E2E_TMP:-$HOME/.cache/horizon-e2e/scratch}"/betterdungeons-change.XXXXXX)
export HORIZON_HOME=$SCRATCH2/home HORIZON_LAUNCHER_HOME=$SCRATCH2/launcher
export XDG_DATA_HOME=$SCRATCH2/data XDG_CONFIG_HOME=$SCRATCH2/config
mkdir -p "$HORIZON_HOME" "$XDG_DATA_HOME" "$XDG_CONFIG_HOME"
cd "$SCRATCH2"
ctl launch --game "$CONTROL_GAME" --headless --resources "$RES" --no-pause >/dev/null
ctl open BetterDungeons 20261105 creative >/dev/null
ctl wait-ready 400 >/dev/null
ctl command "gamerule spawn_mobs false" >/dev/null
WITHOUT_COMMAND=$(ctl command "betterdungeons status" | jq -r '.chat | join("\n")')
echo "status without the package: $WITHOUT_COMMAND"
ctl tp "$SITE" 64 "$SITE" >/dev/null
ctl command "forceload add -24 -24 24 24" >/dev/null
ctl wait 40 >/dev/null
WITHOUT_PLACE=$(ctl command "place structure betterdungeons:small_dungeon $SITE 64 $SITE" \
    | jq -r '.chat | join("\n")')
echo "place without the package: $WITHOUT_PLACE"
ctl wait 20 >/dev/null
WITHOUT_BRICKS=$(count stone_bricks)
echo "without the package: stone_bricks=$WITHOUT_BRICKS"
echo "$WITHOUT_COMMAND" | grep -q 'Unknown or incomplete command' \
    || fail "the control game answered /betterdungeons status: $WITHOUT_COMMAND"
echo "$WITHOUT_PLACE" | grep -q 'There is no structure with type "betterdungeons:small_dungeon"' \
    || fail "the control game placed the structure: $WITHOUT_PLACE"
[ "$WITHOUT_BRICKS" = 0 ] || fail "the control game placed $WITHOUT_BRICKS stone bricks"
rm -rf "$SCRATCH2" || true

echo "PASS: /betterdungeons status reports the registered type and 5 pieces; /place structure betterdungeons:small_dungeon placed the shell ($BRICKS stone bricks, $ANDESITE polished andesite, $MOSSY mossy cobblestone) with $CAVE_AIR cave air, the yellow and cyan glass processed away, $SPAWNERS spawner carrying a dungeon mob and $CHESTS chests with minecraft:chests/simple_dungeon; the same Nightly without the package answers 'There is no structure with type \"betterdungeons:small_dungeon\"' and places nothing"
