# Licence notice — YUNG's Better Dungeons for Horizon

## The work this port is derived from

| | |
|---|---|
| mod | **YUNG's Better Dungeons** 1.21.1-NeoForge-5.1.4 |
| authors | YUNGNICKYOUNG, Acarii (jar `META-INF/neoforge.mods.toml`, `credits` and `authors`) |
| licence | **LGPL-3.0-only** — the jar declares `license="LGPLv3"` and ships the licence text as `LICENSE_YungsBetterDungeons` (7,815 B, the GNU Lesser General Public License version 3) |
| asset licence | **none separate** — the repository `YUNG-GANG/YUNGs-Better-Dungeons` carries a single root `LICENSE`; unlike Twilight Forest there is no `ASSET_LICENSE`, so the templates, loot tables, tags and lang file travel under the same LGPL-3.0-only |
| jar | `YungsBetterDungeons-1.21.1-NeoForge-5.1.4.jar`, 782,160 B, SHA-256 recorded in `carry-manifest.json` |

## What this package carries from it

`carry-manifest.json` lists every carried file with its size, SHA-256, the jar
entry it came from and whether it was rewritten:

- the 16 `small_dungeon` `.nbt` templates — **verbatim**;
- `loot_table/small_dungeon/chests/loot_piles.json` — verbatim;
- `tags/worldgen/biome/has_structure/small_dungeon.json` — verbatim;
- `worldgen/structure_set/small_dungeons.json` — verbatim;
- `worldgen/structure/small_dungeon.json` — **only `"type"` rewritten**, from
  `yungsapi:yung_jigsaw` to `betterdungeons:small_dungeon_type`, because this
  project does not have that library's type and registers its own instead;
- `assets/betterdungeons/lang/en_us.json` — verbatim (the banner names);
- `LICENSE` — the jar's `LICENSE_YungsBetterDungeons`, verbatim.

The two template pools and the four processor lists are kept under
`carry-work/jar/` as the evidence `tools/check_content.py` reads; they are **not**
packaged, because a pack carrying them fails to decode: the engine refuses the
`yungsapi:yung_single_element` element type and the mod's own
`betterdungeons:*` processor types (`crates/horizon-world/src/worldgen/structure/
processor.rs` refuses an unknown `processor_type`). The port's generated Rust
tables are their loadable form.

## What this package does not carry

No Java code, no textures, no models, no mixins. `src/` is a clean-room Rust
rewrite from the mod's behaviour: the assembly follows the published
`YUNG-GANG/YUNGs-API` structure type (read as analysis, v5.1.9, `YungJigsawStructure`
and `JigsawStructureAssembler`), and the processors follow
`YUNG-GANG/YUNGs-Better-Dungeons` (v6.1.1, `Common/…/world/processor/**`). The
piece construction, the state/rotation tables and every line of Rust are this
port's own.

## Licence of this package

**LGPL-3.0-only.** The complete corresponding source is this crate. The original
copyright and licence notice travel with it (this file and `LICENSE`).
