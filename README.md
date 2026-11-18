# YUNG's Better Dungeons — a Horizon port

**YUNG's Better Dungeons** is a Minecraft mod. Adds actual dungeons to the game. This repository is a **port of it to [Horizon](https://github.com/horizon-rust/horizon)**, the Rust engine for Minecraft Java 26.3. It carries the complete source of the port plus the content files it ships, and installs as a single `.hmod` package.

Upstream: [YUNG-GANG/YUNGs-Better-Dungeons](https://github.com/YUNG-GANG/YUNGs-Better-Dungeons) — licence **LGPL-3.0-only**.

| | |
|---|---|
| Upstream mod | YUNG's Better Dungeons ([source](https://github.com/YUNG-GANG/YUNGs-Better-Dungeons)) |
| Ported to | Horizon 0b14f8a, Minecraft Java 26.3, mod API `0.2` |
| Package | `betterdungeons.hmod` (install it with the Horizon launcher) |
| Licence | **LGPL-3.0-only** — the upstream mod's licence; see [Licence and credit](#licence-and-credit) |

## What this port implements

### What the slice implements

| | |
|---|---|
| one structure, end to end | `betterdungeons:small_dungeon`, placed by `/place structure` and by the jar's own `random_spread` structure set (salt 34239823, spacing 10, separation 6) |
| 16 templates | the six shells and ten loot piles, byte-identical to the jar, generated into `src/templates.rs` by `tools/gen_tables.py` |
| 2 template pools | the 18 weighted shell entries and the 10 loot-pile entries with their `max_count` limits, the jar's order and weights |
| 4 processor lists | the zombie/skeleton/spider shell chains and the loot-pile chain, in the jar's order |
| 1 readout command | `/betterdungeons status`: the registered type, what is carried, and a deterministic sample assembly |

## Not yet ported

- **Only one of the five structures.** `skeleton_dungeon`, `zombie_dungeon`,
- **The two `remove_*_feature_in` biome modifiers**
- **The config file** — defaults compiled in (`src/runtime.rs`,
- **`start_height`'s `x_offset_in_chunk`/`z_offset_in_chunk`**: the jar omits
- **Saved pieces are re-derived from the template, not from a stored block list**
- **Liquid settings**: the jar's `"liquid_settings": "ignore_waterlogging"` is
- **`spawn_overrides`** are carried empty in the JSON and not read (the campaign

## Installing

1. Install the [Horizon launcher](https://github.com/horizon-rust/horizon/releases) (0.2.70 or newer).
2. Add `betterdungeons.hmod` to the instance's mods.
3. The package is pinned to a specific Horizon build; the launcher checks that pin.

## Licence and credit

YUNG's Better Dungeons was created by its upstream authors; the code, models and assets in the original mod
remain theirs and are used here under **LGPL-3.0-only**. The Rust in this repository is a clean-room
rewrite for Horizon, not a translation of the original source.

- `LICENSE` — the upstream licence text.
- `LICENSE-NOTICE.md` — what this port carries and where it came from.
- The upstream project: https://github.com/YUNG-GANG/YUNGs-Better-Dungeons

## Technical details

```
horizon-mod.toml   package manifest (id, version, api, [native] pin)
Cargo.toml         the crate; depends on `horizon-mod-api` from the fetched SDK
src/               lib.rs (the one `impl Hooks`), runtime.rs (pure logic + tests), glue
assets/ data/      the content the package ships
tools/             content generators and the e2e scenario
```

- Build: `cargo horizon-mod build` (packages; it does not compile against the game).
- Test: `cargo test`, `cargo clippy --all-targets -- -D warnings`.
- In-game: `ports/tools/launcher-game.sh run betterdungeons` in the campaign tree, or install the
  `.hmod` and play; the harness scenario is `tools/e2e.sh`.

This repository is generated from the campaign's port at `ports/betterdungeons/`; the port's own
`notes.md` is the full record (decisions, traps, evidence).
