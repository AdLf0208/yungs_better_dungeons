# Validation — betterdungeons 0.2.0 (first publication)

Every step ran through the shared build-slot registry, one lease, `CARGO_INCREMENTAL=0`,
`TMPDIR` beside the crate (`/tmp` is a full tmpfs on this box). The package on disk is the
bytes the launcher built the game from.

```sh
ports/tools/build-slot.sh run --job betterdungeons-final --port ports/betterdungeons \
    --step build -- ports/betterdungeons/tools/check.sh
ports/tools/launcher-game.sh run betterdungeons
```

| step | result |
|---|---|
| `cargo test --offline` | **26 passed, 0 failed**; doc-tests 0 |
| `cargo clippy --offline --all-targets -- -D warnings` | 0 warnings |
| `cargo fmt --check` | clean |
| `cargo horizon-mod build` (after `rm -f Cargo.lock`) | `betterdungeons.hmod` |
| `cargo horizon-mod check betterdungeons.hmod` | exit 0 — native-mod, `native-1/0b14f8ac…/e59da909…`, for 26.3, 83,682 B |
| `cargo horizon-mod fits betterdungeons.hmod` | exit 0 — `0b14f8a  made for` |
| `python3 tools/check_content.py --check` | `CONTENT CHECK:PASS` — 28 carried files match the jar, the two generated tables regenerate identically, 149 states and 67 biome ids exist in 26.3, the packaged definition names the port's type |
| the build run twice in one lease | byte-identical, `561c09a5…d50c26` both times |

## Package

`ports/betterdungeons/betterdungeons.hmod` — **83,682 B**, SHA-256
`561c09a5104489eb6c4acf9073467c5c2cf5d0d0a4feda628792e1a908d50c26`, **32 entries**:
`horizon-mod.toml`, `Cargo.toml`, `src/{lib,runtime,support,templates,pools}.rs`,
the 16 templates, the loot table, the biome tag, the structure and structure-set
definitions, `assets/betterdungeons/lang/en_us.json`, `LICENSE`,
`LICENSE-NOTICE.md`, `README.md`, `uses.json`. **No `Cargo.lock`.**
`uses.json` records `handle:Registrar::register_structure_type`,
`method:BlocksRegistrar::block_key`,
`method:StructurePiece::{bounding_box,post_process,add_additional_save_data}`,
`hook:register_commands`, `hook:run_mod_command` and `method:Commands::feedback`.

The jar measurement is `ports/_shared/evidence/betterdungeons/inventory-small_dungeon.json`;
the ladder's own output is `ports/_shared/evidence/betterdungeons/ladder.log`.

## In-game (launcher 0.2.78, nightly `0b14f8a`)

`ports/_shared/evidence/betterdungeons-e2e/`:

| log | verdict |
|---|---|
| `e2e-launcher.log` | `PASS: …` + `E2E EXIT:0` |
| `e2e-launcher-control.log` (same Nightly without the package) | `FAIL: the engine did not place the structure: There is no structure with type "betterdungeons:small_dungeon"` + `E2E EXIT:1` |
| `e2e-launcher-selftest.log` (the block assertion inverted) | `FAIL: SELFTEST: the dungeon is in the box, so the assertion is alive` + `E2E EXIT:1` |

`python3 ports/tools/check-e2e-logs.py betterdungeons-e2e --strict` →
`logs=3 ok=3 missing-exit=0 bad-exit=0`, exit 0.

Measured in the modded run (seed 20261105, creative, start box force-loaded before the
place): stone bricks 0 → 20, polished andesite 0 → 4, mossy cobblestone 0 → 107, cave air
0 → 331, spawner 0 → 1 (`{entity: {id: "minecraft:skeleton"}}`), chest 0 → 2
(`minecraft:chests/simple_dungeon`), the yellow and cyan placeholder glass 0 (processed
away). `/betterdungeons status` reported the registered type and the 5-piece sample
assembly. In the control Nightly the same command answers `Unknown or incomplete command`,
the place answers `There is no structure with type "betterdungeons:small_dungeon"`, and
the search box stays empty.

## Gate

`python3 ports/tools/check-skills.py --notes ports/betterdungeons --strict` → `SKILLS GATE: PASS`.
