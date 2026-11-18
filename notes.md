# betterdungeons — YUNG's Better Dungeons for Horizon

Slice 1: **one dungeon, placed in a real level**, assembled by this port's own
structure type from the jar's carried jigsaw templates.

| | |
|---|---|
| mod | YUNG's Better Dungeons 1.21.1-NeoForge-5.1.4 (YUNGNICKYOUNG, Acarii) |
| class · tier · kind · role | `content` · `data` · `mech` · `core` (ledger row), ported as a **deep** job: the structures are assembled by a Java type |
| licence | **LGPL-3.0-only — rank 1 (copyleft, publishable)** |
| pins | Horizon API/SDK `0b14f8acfd97fa2c750e42795249dcc981178ca4`, mixins `e59da9094f0c2fdda6c627fe9eff22dec6a906f0`, game 26.3, `api = "0.2"`, version `0.2.0` (first publication) |
| package | `betterdungeons.hmod` — 32 files, 83,682 B, SHA-256 `561c09a5…d50c26` (built twice, byte-identical) |
| in-game | **PASS** at the launcher nightly `0b14f8a`: `/place structure betterdungeons:small_dungeon` places the dungeon; the control Nightly answers `There is no structure with type "betterdungeons:small_dungeon"` |

## Licence evidence (read from the artefacts, not assumed)

- `META-INF/neoforge.mods.toml`: `license="LGPLv3"`, authors `YUNGNICKYOUNG,
  Acarii`, and a required dependency on `yungsapi` ≥ `1.21.1-NeoForge-5.1.3`.
- The jar ships `LICENSE_YungsBetterDungeons` (7,815 B) — the LGPL-3.0 text; it is
  carried as `LICENSE`.
- The upstream repository `YUNG-GANG/YUNGs-Better-Dungeons` (cloned `--depth 1`,
  HEAD `631719b` = v6.1.1) has a **single root `LICENSE`**, the LGPL-3.0 text, and
  **no** `ASSET_LICENSE` — so there is no separate asset rider (contrast
  `twilightforest`, whose `ASSET_LICENSE` is CC-BY-NC-SA-4.0). The templates,
  loot tables, biome tag and lang file therefore travel under LGPL-3.0-only.
- Rank 1 is publishable under the same licence with the complete corresponding
  source (this crate). Local-only until the maintainer approves publishing
  (ARCHITECTURE §8).

## Jar inventory (measured; this is the slice's scope evidence)

482 entries, 782,160 B. Tools: `ports/_shared/evidence/betterdungeons/tools/inventory.py`
and `nbt_dump.py` (read-only), output `ports/_shared/evidence/betterdungeons/inventory-small_dungeon.json`.

| family | count |
|---|---:|
| `.nbt` templates | **227** |
| `worldgen/template_pool/**.json` | **33** |
| `worldgen/processor_list/**.json` | **12** |
| `worldgen/structure/*.json` | **5** (`skeleton_dungeon`, `small_dungeon`, `small_nether_dungeon`, `spider_dungeon`, `zombie_dungeon`) |
| `worldgen/structure_set/*.json` | **5** |
| `loot_table/**.json` | 8 |
| `tags/worldgen/biome/has_structure/*.json` | 5 |
| `tags/worldgen/structure/better_dungeons.json` | 1 (the aggregate tag) |
| `neoforge|forge/biome_modifier/*.json` | 2 (`vanilla_dungeon_removal`) |
| `assets/betterdungeons/lang/*.json` | 6 |

**The brief and ARCHITECTURE §3 quote 227 `.nbt`, 38 pools, 17 processor lists, 6
structures.** The artifact says 33, 12 and 5. The difference is a counting one:
33 pools + 5 structure sets = 38 and 12 processor lists + 5 structure sets = 17,
and the "6th structure" is the aggregate `better_dungeons` **tag**, not a
structure definition. Recorded here rather than repeating the larger numbers.

### The slice's own content (16 templates, 25 block kinds, 3 251 blocks)

| | |
|---|---|
| shells | `small_shell_5x5`, `7x5`, `7x7`, `9x5`, `9x7`, `9x9` — 319/413/535/507/657/807 blocks |
| loot piles | `loot_pile_0`…`8` (2x2x2 or 2x1x2) and `loot_pile_empty` (1x1x1) |
| distinct blocks in the palette | 25 |
| jigsaw connectors | 5 per shell (4 loot-pile + the start anchor `betterdungeons:small_dungeon_anchor`), 1 per loot pile |
| block entities | chest ×48 (`minecraft:chests/simple_dungeon`), banner ×36 (patterns empty), spawner ×6, barrel ×5 (`betterdungeons:small_dungeon/chests/loot_piles`), skull ×5, jukebox ×1, furnace ×1 |
| entities | 0 |
| processor types used | 12 of the mod's own + `minecraft:rule` |

## The approach, and why

`horizon/docs/modpacks.md` puts this mod at **tier data**; the job is `deep`
because the structure *type* is code. ARCHITECTURE §3's structure-type row is the
charter (and records the corrected measurement above), §8 supplies
`StructuresRegistrar`/`StructureType`/`StructurePiece`/`StructureRandom`.

**Two engine facts decided the shape, both measured:**

1. `crates/horizon-world/src/worldgen/structure/processor.rs:748-800` refuses an
   unknown `processor_type` (`DecodeError::Field`). The jar's four processor lists
   start with the mod's own types (`betterdungeons:small_dungeon_banner_processor`
   and ten others), so **carrying them as data is fatal**: the pool would not
   decode and the structure would never generate. The eleven processors are only
   reachable as code.
2. The SDK registers structure types
   (`world/structure_type.rs`, `parts/structures.rs:19`), and a data-pack
   structure with `"type": "betterdungeons:small_dungeon_type"` then generates by
   that type. This is the sanctioned route and it is what the port uses.

So the port owns the assembly **and** the decoration, and the jar's pools and
processor lists are carried as `carry-work/jar/` evidence whose loadable form is
the generated Rust (`src/pools.rs`), proved equal by `tools/gen_tables.py --check`.

### Measured, and worth recording: the pin's engine also assembles YUNG structures

At the *game* pin `1d63e0a` the engine already implements `yungsapi:yung_jigsaw`:
`worldgen/structure/start.rs:346` maps that type to `jigsaw::Draws::Yung`, and
`jigsaw.rs` implements YUNG's weighted draws, priority entries and `max_count`
limits, including the `yungsapi:yung_single_element` element type
(`jigsaw.rs:144`). So on that pin a *data-only* carry could have assembled the
same dungeon — with the eleven Java processors still missing. Slice 2+ may revisit
whether the extra fidelity of the engine's assembler is worth preferring over this
port's own for the remaining structures; the port keeps its own type because
(a) the campaign may not register or depend on a library type it does not own,
(b) the processors need Rust regardless, and (c) the SDK's registrar is the
documented route for a mod's structure.

## What the port does (files)

| file | role |
|---|---|
| `src/lib.rs` | the one `#[mod_api::horizon_mod] impl Hooks`: `register`, `register_commands`, `run_mod_command` |
| `src/runtime.rs` | **pure** logic, no `mod_api` type: jigsaw assembly, rotation/attach rules, box tests, the twelve processors as decisions over a `World` trait, the chest/banner caps, the readout. 26 tests |
| `src/support.rs` | the glue: `register_structure_type("small_dungeon_type", …)`, one `block_key` per carried state, `StructureType::find_generation_point`, `StructurePiece` (place, save, load), `/betterdungeons` |
| `src/templates.rs` | **generated**: 149 block states with their four rotations resolved, 16 templates (blocks + jigsaw connectors + payloads), the loot-table ids |
| `src/pools.rs` | **generated**: 2 pools with the jar's weights/order/`max_count`, 4 processor lists with their parameters and rule rows, the structure definition |
| `tools/gen_tables.py` | jar → those two files; `--check` regenerates and diffs |
| `tools/carry.py` | jar → the package's content; `--check` proves the bytes |
| `tools/check_content.py --check` | both, plus the 26.3 registry and the package's shape |
| `tools/check.sh` | the ladder (test, clippy, fmt, build, check, fits, content) |
| `tools/e2e.sh` | the in-game leg, including its own control leg |

## The SDK structure surface this port uses (quoted)

- `StructureType` (`api-source/crates/horizon-mod-vocab/src/world/structure_type.rs`):
  `fn find_generation_point(&self, context: &mut dyn GenerationContext) -> Option<FoundStructure>;`
  `fn load_piece(&self, metadata: &dyn BlockMetadata, tag: &Compound) -> Result<Arc<dyn StructurePiece>, StructureError>;`
  `fn after_place(&self, _context: &mut dyn PieceContext, _pieces: &[BoundingBox]) -> Result<(), StructureError> { Ok(()) }`
- `StructurePiece`: `fn bounding_box(&self) -> BoundingBox;`
  `fn post_process(&self, context: &mut dyn PieceContext) -> Result<(), StructureError>;`
  `fn add_additional_save_data(&self, tag: &mut Compound);`
- `StructuresRegistrar` (`parts/structures.rs:19`):
  `pub fn register_structure_type<T: crate::StructureType>(&mut self, name: &str, ty: T)`
  — the type's id lives in the calling mod's namespace.
- `GenerationContext`: `metadata()`, `chunk() -> ChunkPos`, `seed() -> i64`,
  `min_y()`, `max_y()`, `random() -> &mut dyn StructureRandom`,
  `base_height()`, `base_columns()`, `noise_column()`, `noise_biome()`,
  `column_has_valid_biome()`, `config() -> Arc<Tag>`.
- `PieceContext`: `metadata()`, `chunk()`, `chunk_box()`, `random()`, `state()`,
  `state_with()`, `is_air()`, `block()`, `set_block()`, `height()`,
  `solid_render()`, `entity()`, `block_entity()`.
- `StructureRandom`: `next_int_bound(i32) -> i32`, `next_long()`, `next_float()`,
  `next_double()`, `next_boolean()` — the port implements `runtime::Rng` over it,
  so the draws are the game's own `WorldgenRandom`.
- `BlockState::of(metadata, block: BlockKey, &[StateConstraint])` and
  `BlockMetadata::name(BlockKey)`; `BlocksRegistrar::block_key(&str) -> BlockKey`.
- `FoundStructure { position: [i32; 3], pieces: Vec<Arc<dyn StructurePiece>> }`.

## The jigsaw design (and what it drops)

`runtime::assemble` follows `JigsawManager.getStartPiece` +
`JigsawStructureAssembler.chooseCandidateFromPool`:

1. **Start element**: the pool's entries shuffled (`Util.shuffle`: Fisher–Yates
   from the end), then a weighted draw (`nextInt(total) + 1`, subtract, first
   ≤ 0), with the element's `max_count`/depth limits removing candidates.
2. **Rotation**: `Rotation.getRandom` = one of four, drawn from the context's
   random.
3. **Start position**: `(chunk.minX + x_offset, start_height, chunk.minZ + z_offset)`
   — the jar sets neither offset — with `start_height` a uniform absolute −50..50.
4. **The anchor**: the piece is shifted so the jigsaw named
   `betterdungeons:small_dungeon_anchor` sits exactly on that position
   (`getPosOfJigsawBlockWithName`).
5. **Expansion**: breadth-first over the pieces' connectors, each piece's list
   shuffled; for each connector, draw from its `pool` (only the payload pool here),
   and for each candidate element try the four rotations until a child connector
   *as rotated* faces the parent (`canAttach`: opposite fronts, equal tops,
   `child.name == parent.target`), the piece fits the level's Y range, and it is
   inside the structure's box (`max_distance_from_center`) without overlapping a
   placed piece.
6. **The inside-target rule** (YUNG's own): a connector whose target cell lies
   inside the parent piece gets a fresh octree bounded by the parent with no boxes
   in it, so its child need only fit *inside the parent* — that is how the loot
   piles sit in the room. Reproduced as measured, and tested
   (`siblings_never_overlap_and_children_stay_in_their_parent`).
7. **The depth cap**: `size` 10 from the jar; a piece at depth = size only tries
   the fallback pool.
8. **Connectors become their `final_state`** (`JigsawReplacementProcessor`):
   every carried connector's `final_state` is `minecraft:air`.

Dropped, with what forced it:

- **`JigsawJunction` bookkeeping.** Only terrain adaptation's beardifier reads it,
  and this structure declares no `terrain_adaptation`; the engine's own
  `PieceBeardifier` is left at its default. (`JigsawStructureAssembler` lines
  527-568.)
- **The non-rigid "surface height" branch** (`settings.chunkGenerator
  .getFirstFreeHeight(WORLD_SURFACE_WG, …)`, assembler lines 450-514). Every
  carried pool element is `"projection": "rigid"`, and the generator refuses a
  non-rigid element rather than guessing; the branch is unreachable for this
  structure.
- **`use_expansion_hack`** — the jar's JSON sets `false`; the generator refuses a
  config that turns it on.
- **The `/locate` semantics of `start_jigsaw_name`** beyond the anchor offset: the
  engine's own `locate` answers from the structure set, which this port does not
  control.
- **The mod's config file** (`bannerMaxCount` 2, `chestMinCount` 1,
  `chestMaxCount` 2, `enableHeads`, `enableNetherBlocks`, `enableOreProps`, all at
  their defaults) — compiled in as `runtime::settings`; the config screen and the
  `removeVanillaDungeons` option (a biome modifier) are out of scope.
- **The other five structures, the aggregate tag and the two biome modifiers.**
- **YUNG's structure conditions / priorities / deadend pools / modifiers /
  `delay_generation`.** None of the seventeen carried elements sets any of them;
  the generator *refuses* an element field it does not carry (`tools/gen_tables.py`,
  the `unknown` sets), so a future data change fails loudly instead of being
  silently dropped.

## Content carried (jar → package)

| jar entry | package | transform |
|---|---|---|
| `structure/small_dungeon/**/*.nbt` (16) | same path | verbatim |
| `loot_table/small_dungeon/chests/loot_piles.json` | same | verbatim |
| `tags/worldgen/biome/has_structure/small_dungeon.json` | same | verbatim |
| `worldgen/structure_set/small_dungeons.json` | same | verbatim |
| `worldgen/structure/small_dungeon.json` | same | **only `type`** → `betterdungeons:small_dungeon_type` |
| `assets/betterdungeons/lang/en_us.json` | same | verbatim |
| `LICENSE_YungsBetterDungeons` | `LICENSE` | verbatim |
| 2 template pools + 4 processor lists | `carry-work/jar/…` | verbatim, **not packaged** (see above) |

`tools/carry.py --check` proves all 28 carried files (16 templates + 12 others)
plus the jar's own SHA-256; `tools/check_content.py --check` additionally proves
the packaged `data/` and `assets/` carry **nothing** the manifest does not
explain.

### 1.21.1 → 26.3 block renames

The templates are 1.21.1 data (`DataVersion` 3955). Exactly one palette block was
renamed by 26.3: **`minecraft:chain` → `minecraft:iron_chain`**. The generator
maps it (`RENAMES`) and refuses any name the 26.3 registry lacks and any property
or value the 26.3 model-state table does not accept — so the rename and the whole
palette are checked, not assumed.

## Verification

Skills: superpowers/using-superpowers, brainstorming, writing-plans, test-driven-development, systematic-debugging, verification-before-completion; BeautifulRust/rust-best-practices, rust-port

### Pure logic (26 tests, `cargo test --offline`)

`26 passed; 0 failed`. Fail-capable cases, each of which would fail if the
behaviour were wrong:

| test | what it pins |
|---|---|
| `every_generated_element_names_a_carried_template_and_processor_list` | the generated tables are internally complete |
| `every_generated_processor_step_is_one_this_port_implements` | no processor kind is silently unimplemented |
| `the_state_table_and_its_rotations_agree`, `every_state_rotation_is_a_state` | `ROTATED` has a row per state and four turns is the identity |
| `a_rotation_turns_facing_and_keeps_turning` | stairs `facing` north→east→south; north = east at 180° |
| `a_skull_rotation_moves_four_sixteenths_per_quarter_turn` | skull `rotation` 13 → 1 → 5 → 9 (16-step direction) |
| `a_loot_pile_attaches_to_every_shell_connector` | the attach predicate finds a rotation for all four connectors |
| `the_assembly_is_deterministic_for_a_seed` | same seed → identical pieces; a different seed differs |
| `the_anchor_sits_on_the_chunk_corner_at_the_drawn_height` | 32 seeds: the anchor is at `(32, y∈[-50,50], 48)` |
| `a_start_is_a_shell_and_its_children_are_loot_piles` | 16 seeds: piece 0 is a shell, the rest are piles at depth 1 |
| `siblings_never_overlap_and_children_stay_in_their_parent` | 64 seeds: no two children share a block, all fit the parent |
| `the_start_pool_draw_matches_the_jar_weights` | the 5x5 weight is 4 of 24, and 1 200 seeds draw it 10-28 % of the time |
| `a_max_count_element_is_refused_after_its_limit` | `loot_pile_0` (max 1) never appears twice |
| `a_pool_whose_entries_are_all_at_their_limit_yields_nothing` | the prop limits hold and a structure is at most 5 pieces |
| `a_config_the_tables_cannot_describe_is_refused` | a size/anchor the tables do not carry → `Unsupported` |
| `the_decoration_keeps_at_most_two_chests_and_two_banners` | 64 seeds: 1–2 chests, ≤ 2 banners |
| `a_chest_is_removed_only_after_the_minimum_is_kept` | with a world of air, 1–2 chests survive |
| `a_sea_pickle_becomes_a_lit_or_unlit_candle` | the candle processor writes a candle state |
| `a_support_leg_reaches_the_floor_and_stops_in_stone` | 9 stone-brick legs from y=29 to 21, stopping in stone |
| `a_rule_replaces_only_matching_states` | the jar's third rule turns air into cave air |
| `the_readout_names_the_registered_type_and_a_piece_count` | `/betterdungeons status` says 16/2/4 and 5 pieces |
| `support`: `a_saved_piece_round_trips_through_its_own_fields` | save → load gives the same `Piece` |
| `support`: `the_carried_config_decodes_to_the_carried_cap` | the NBT config decodes and is supported |
| `support`: `a_banner_carries_its_patterns_and_name`, `a_spawner_carries_its_mob_in_both_fields` | the block-entity NBT the processors write |

### The ladder (`tools/check.sh`, one build-slot lease)

| step | result |
|---|---|
| `cargo test --offline` | 26 passed, 0 failed |
| `cargo clippy --offline --all-targets -- -D warnings` | 0 warnings |
| `cargo fmt --check` | clean |
| `cargo horizon-mod build` (after `rm -f Cargo.lock`) | `betterdungeons.hmod` |
| `cargo horizon-mod check betterdungeons.hmod` | exit 0 — native-mod, `native-1/0b14f8ac…/e59da909…`, for 26.3, 83,682 B |
| `cargo horizon-mod fits betterdungeons.hmod` | exit 0 — `0b14f8a  made for` |
| `python3 tools/check_content.py --check` | `CONTENT CHECK:PASS` (bytes, tables, registry, shape) |
| built twice in one lease | byte-identical: `561c09a5104489eb6c4acf9073467c5c2cf5d0d0a4feda628792e1a908d50c26` |

Package: 32 entries — `horizon-mod.toml`, `Cargo.toml`, `src/{lib,runtime,support,templates,pools}.rs`,
16 templates, the loot table, the biome tag, the structure and structure-set
definitions, the lang file, `LICENSE`, `LICENSE-NOTICE.md`, `README.md`,
`uses.json`. **No `Cargo.lock`.** `uses.json` records
`handle:Registrar::register_structure_type`, `method:BlocksRegistrar::block_key`,
`method:StructurePiece::{bounding_box,post_process,add_additional_save_data}`,
`hook:register_commands`, `hook:run_mod_command` and `method:Commands::feedback`
— the code half wired to the SDK.

### In-game (launcher `0.2.78`, nightly `0b14f8a`)

`ports/tools/launcher-game.sh run betterdungeons` compiles the package into a game
at the SDK pin and runs `tools/e2e.sh`. Evidence:
`ports/_shared/evidence/betterdungeons-e2e/` (`e2e-launcher.log`,
`e2e-launcher-control.log`, `e2e-launcher-selftest.log`);
`python3 ports/tools/check-e2e-logs.py betterdungeons-e2e --strict` → `logs=3 ok=3
missing-exit=0 bad-exit=0`.

| leg | result |
|---|---|
| modded | **`PASS:` + `E2E EXIT:0`** |
| control (`GAME=$CONTROL_GAME`, the same Nightly without the package) | `FAIL: the engine did not place the structure: There is no structure with type "betterdungeons:small_dungeon"` + `E2E EXIT:1` |
| selftest (`SELFTEST=1`, the block assertion inverted) | `FAIL: SELFTEST: the dungeon is in the box, so the assertion is alive` + `E2E EXIT:1` |

What the modded run measured, in one headless world (seed 20261105, creative),
with the start box force-loaded **before** the place:

| | before the place | after `/place structure betterdungeons:small_dungeon 0 64 0` |
|---|---:|---:|
| `minecraft:stone_bricks` | 0 | **20** |
| `minecraft:polished_andesite` | 0 | **4** |
| `minecraft:mossy_cobblestone` | 0 | **107** |
| `minecraft:cave_air` | 0 | **331** |
| `minecraft:spawner` | 0 | **1** |
| `minecraft:chest` | 0 | **2** |
| `minecraft:yellow_stained_glass` (leg placeholders) | 0 | **0** (the leg processor replaced them) |
| `minecraft:cyan_stained_glass` (lamp placeholders) | 0 | **0** (the ceiling-lamp processor replaced them) |

and the block entities the decoration wrote:

```text
0, 44, 0 has the following block data: {entity: {id: "minecraft:skeleton"}}
-4, 44, -2 has the following block data: "minecraft:chests/simple_dungeon"
```

The spawner carries a dungeon mob (the `MobSpawnerProcessor`), the chest a loot
table, and the count is 2 — the structure-wide `chestMaxCount` holding in game.
`/betterdungeons status` answered in the same run:

```text
sample: chunk (2, 3), seed 20261105 -> 5 pieces at (32, 6, 48)
  #0 …/shells/small_shell_7x5 depth 0 rotation cw90 at (29, 4, 44) 7x7x9
  #1 …/loot_piles/loot_pile_1 depth 1 rotation cw180 at (30, 5, 45) 2x2x2
  #2 …/loot_piles/loot_pile_empty depth 1 rotation ccw90 at (33, 5, 46) 1x1x1
  #3 …/loot_piles/loot_pile_5 depth 1 rotation cw90 at (30, 5, 50) 2x1x2
  #4 …/loot_piles/loot_pile_8 depth 1 rotation none at (33, 5, 50) 2x2x2
```

The control Nightly, same world name and seed: `/betterdungeons status` → `Unknown
or incomplete command`, `/place structure betterdungeons:small_dungeon …` → `There
is no structure with type "betterdungeons:small_dungeon"`, and the search box stays
empty (0 stone bricks). So the dungeon in the modded leg cannot come from the
engine or from the terrain.

Also measured in a probe run on the same pin: `/locate structure
betterdungeons:small_dungeon` answers `[848, ~, 816] (238 blocks away)`, i.e. the
carried `structure_set` is registered and the type is reachable through natural
generation, not only through `/place`.

## Gaps (with file:line)

1. **Only one of the five structures.** `skeleton_dungeon`, `zombie_dungeon`,
   `small_nether_dungeon` and `spider_dungeon` are not carried. The last two use
   the mod's **own Java structure types** (`betterdungeons:small_nether_dungeon`,
   `betterdungeons:spider_dungeon` in `worldgen/structure/{small_nether_dungeon,
   spider_dungeon}.json`), with hand-written pieces
   (`Common/…/world/structure/spider_dungeon/piece/*.java`) — a later slice with
   its own `StructureType`s.
2. **The two `remove_*_feature_in` biome modifiers**
   (`forge|neoforge/biome_modifier/vanilla_dungeon_removal.json`, driven by
   `ConfigurationSectionVanillaRemoval`) are not carried: they remove vanilla
   dungeons by tag, which is a separate feature (and a biome-modifier decision the
   engine's `BiomeModifiersRegistrar` would express).
3. **The config file** — defaults compiled in (`src/runtime.rs`,
   `mod settings`); no config screen, no `enableHeads=false` /
   `enableNetherBlocks=false` / `enableOreProps=false` path to toggle them at run
   time.
4. **`start_height`'s `x_offset_in_chunk`/`z_offset_in_chunk`**: the jar omits
   both (default 0) and the port only implements the default; a pack that sets
   them is refused (`config_supported`).
5. **Saved pieces are re-derived from the template, not from a stored block list**
   (`src/support.rs::saved_spec`): the engine saves `BB`/`O`/`GD` and this port
   adds `Template`/`Rotation`/`Seed`/`Chests`/`Banners`/`MinY`. A structure saved
   by a *different* mod version (different processor list) would load its template
   with this port's chain — documented, not solved.
6. **Liquid settings**: the jar's `"liquid_settings": "ignore_waterlogging"` is
   carried in `pools::STRUCTURE` and reported, but the port does not implement
   waterlogging behaviour (it writes the template's own states); the engine's own
   liquid handling is what applies.
7. **`spawn_overrides`** are carried empty in the JSON and not read (the campaign
   records that the engine ignores `spawn_overrides` for a mod's structures).

## Upstream defects fixed

The rule is "fix the defect in the port, record it". Three findings, and what the
port does instead:

1. **The loot-pile pool's `name` disagrees with its own id.**
   `worldgen/template_pool/small_dungeon_loot_piles.json` says
   `"name": "betterdungeons:small_dungeon/small_dungeon_loot_piles"`, while the
   shell connectors ask for `betterdungeons:small_dungeon_loot_piles`
   (`structure/small_dungeon/shells/*.nbt`, the jigsaw `pool` field) and the
   registry id is the file's path. Vanilla's `StructureTemplatePool` codec has no
   `name` field, so the value is dead data — but a reader (and this port's
   generator, at first) can take it for the id and then find no pool. **The port
   uses the registry id (the path)**, ignores the `name` field, and records why
   (`tools/gen_tables.py::pool_id`). A user notices nothing; a maintainer stops
   chasing a pool that "does not exist".
2. **The ceiling-prop processor tests the wrong block for the 2-tall prop.**
   `SmallDungeonCeilingPropProcessor.java` reads
   `levelReader.getBlockState(pos.above(2))` for the brown-glass prop but then
   asks `isFaceSturdy(pos.above(), DOWN)` — the position it reads and the face it
   tests are two different blocks, so a 2-tall prop can hang under a non-solid
   ceiling (or be dropped under a solid one). **The port tests the face at
   `above(2)` for the brown prop** (`src/runtime.rs::ceiling_prop`), which is what
   the comment above the code says the check is for ("if ceiling isn't solid,
   place air since we don't want floating props"). Worth an upstream report.
3. **`minecraft:chain` no longer exists at 26.3.** The 1.21.1 templates name it;
   26.3 renamed it `minecraft:iron_chain` (the mod's own newer source already uses
   `Blocks.IRON_CHAIN`). The generator maps it and verifies the target against the
   26.3 registry, so the ceiling chains are placed rather than silently dropped by
   a failed state lookup.

## Traps new to this port (for the next structure job)

1. **The engine's working directory is where `saves/` goes**, not `HORIZON_HOME`.
   The first e2e run left `saves/BetterDungeons` in the campaign root, and the
   second run reopened it — the "before" counts were the previous run's dungeon.
   `tools/e2e.sh` now `cd`s into its scratch dir.
2. **`/place structure` writes nothing into a chunk that is not settled.** The
   first manual attempt at `(1000, 64, 1000)` reported success and placed no
   blocks; the same command next to a loaded spawn chunk placed the dungeon. The
   script force-loads the start box (`forceload remove all` then `add -24 -24 24
   24`) and waits before the place, and asserts the force-load reply.
3. **A stopped game leaves its socket file**, and the next `launch` on the same
   path fails; `rm -f "$SOCK"` before every launch.
4. **`forceload` takes block coordinates**, not chunk ones (`add 61 61 63 63` →
   "Marked chunk [3, 3]").
5. **A pool's registry id is its file path**, not its `name` field (defect 1).
6. **`minecraft:spawner` is the block id**; `minecraft:mob_spawner` is the block
   *entity* id. `find-block mob_spawner` finds nothing while the block is there.
7. **`/place structure` reports success for a structure whose type generated
   nothing** — the command's message is not the proof. The block scan (before/after)
   is, which is why the e2e counts blocks rather than trusting the reply.

## Publishing (first publication)

`0.2.0`, first publication: **LGPL-3.0-only**, the licence the jar declares, with
the complete corresponding source in the repository (this crate) and the original
copyright and licence notice (`LICENSE`, `LICENSE-NOTICE.md`). Nothing is
submitted yet; local-only until the maintainer approves (ARCHITECTURE §8). The
next version is a new package (`0.2.1`) — the registry refuses a duplicate while
an older version's PR is open.
