# YUNG's Better Dungeons for Horizon — slice 1: the small dungeon

This is a Horizon port of **YUNG's Better Dungeons 1.21.1-NeoForge-5.1.4**
(by YUNGNICKYOUNG and Acarii, **LGPL-3.0-only**), for Minecraft Java 26.3 on the
Horizon SDK (`api = "0.2"`, Horizon `0b14f8a…`, mixins `e59da90…`).

The mod's structures are assembled by `yungsapi:yung_jigsaw`, a Java structure type
that this project does not have. The port therefore registers **its own structure
type**, `betterdungeons:small_dungeon_type`, which does the assembly the Java type
did: it draws a start element from the jar's own template pool by the jar's
weights, places it so its named anchor jigsaw sits on the start position, walks
every jigsaw connector breadth-first (trying the four rotations until the child's
own connector faces the parent's), and decorates each piece with the eleven
`betterdungeons:*` processors the jar's four processor lists name — the dungeon
banner, the mob spawner, the chest and banner caps, the candle, the ceiling props
and lamps, the ruin pass that turns air into cave air, the support legs and the
rule processor.

## What the slice implements

| | |
|---|---|
| one structure, end to end | `betterdungeons:small_dungeon`, placed by `/place structure` and by the jar's own `random_spread` structure set (salt 34239823, spacing 10, separation 6) |
| 16 templates | the six shells and ten loot piles, byte-identical to the jar, generated into `src/templates.rs` by `tools/gen_tables.py` |
| 2 template pools | the 18 weighted shell entries and the 10 loot-pile entries with their `max_count` limits, the jar's order and weights |
| 4 processor lists | the zombie/skeleton/spider shell chains and the loot-pile chain, in the jar's order |
| 1 readout command | `/betterdungeons status`: the registered type, what is carried, and a deterministic sample assembly |

## What it does not implement (recorded in `notes.md`)

`skeleton_dungeon`, `zombie_dungeon`, `small_nether_dungeon`, `spider_dungeon`
and the aggregate `better_dungeons` structure tag; the two
`remove_*_feature_in` biome modifiers; the mod's config file (its defaults are
compiled in); and the `JigsawJunction` bookkeeping and non-rigid projection
branches, which nothing in this structure's data asks for.

## Building and checking

```sh
python3 tools/gen_tables.py --check     # the Rust tables are what the jar yields
python3 tools/carry.py --check          # every carried file is the jar's own bytes
python3 tools/check_content.py --check  # both, plus the 26.3 registry and the shape
ports/tools/build-slot.sh run --job betterdungeons --port ports/betterdungeons \
    --step build -- ports/betterdungeons/tools/check.sh
ports/tools/launcher-game.sh run betterdungeons   # the in-game leg
```

## Licence

The port is **LGPL-3.0-only**, the licence the jar declares (`license="LGPLv3"` in
`META-INF/neoforge.mods.toml`) and ships as `LICENSE_YungsBetterDungeons` (the
LGPL-3.0 text, carried as `LICENSE`). The jar has **no separate asset licence**
(unlike Twilight Forest), so the templates, loot tables, biome tag and lang file
travel under the same licence. The complete corresponding source is this crate:
`src/`, `tools/`, `horizon-mod.toml`, `Cargo.toml` and the carried content.
See `LICENSE-NOTICE.md` for where each file came from.
