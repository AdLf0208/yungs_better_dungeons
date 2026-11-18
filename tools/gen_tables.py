#!/usr/bin/env python3
"""Generate `src/templates.rs` and `src/pools.rs` from the jar's carried content.

This is the port's only bridge from the jar's data to Rust. It reads, from
`ports/_shared/licence-cache/YungsBetterDungeons-1.21.1-NeoForge-5.1.4.jar`:

  * the 16 `small_dungeon` templates (palette, blocks, jigsaw connectors),
  * the two template pools (`small_dungeon`, `small_dungeon_loot_piles`),
  * the four `small_dungeon` processor lists,
  * `worldgen/structure/small_dungeon.json` and its structure set,

and writes:

  * `STATES` + `ROTATED` — every block state the templates and the processor
    chains name, with all four clockwise rotations resolved here (so no Rust
    code needs to know a block property's rotation rules), after mapping the
    1.21.1 block ids 26.3 renamed and checking every block name, property and
    value against the prepared 26.3 resources;
  * `TEMPLATES` — size, blocks (pos, state, payload) and jigsaw connectors
    (pos, state, pool, name, target, final_state) of each template;
  * `POOLS`, `PROCESSOR_LISTS`, `STRUCTURE` — the jar's weights, order and
    limits, the processor chains in file order with their parameters, and the
    structure definition `/betterdungeons status` compares a pack's config to.

Every processor type and element type must be one this port implements: an
unknown one aborts the generation instead of being dropped silently.

    python3 tools/gen_tables.py            # write src/templates.rs, src/pools.rs
    python3 tools/gen_tables.py --check    # regenerate + rustfmt, compare, exit 1 on drift
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt_read  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = os.path.dirname(HERE)
JAR = os.environ.get(
    "BD_JAR",
    os.path.join(HERE, "..", "..", "..", "ports", "_shared", "licence-cache",
                 "YungsBetterDungeons-1.21.1-NeoForge-5.1.4.jar"),
)
RES = os.environ.get("HORIZON_RES", "/home/adlf/Desktop/horizon/.local/horizon-client/26.3")

TEMPLATE_ROOT = "data/betterdungeons/structure/small_dungeon/"
SHELL_POOL = "data/betterdungeons/worldgen/template_pool/small_dungeon.json"
LOOT_POOL = "data/betterdungeons/worldgen/template_pool/small_dungeon_loot_piles.json"
PROC_ROOT = "data/betterdungeons/worldgen/processor_list/"
SMALL_PROC = PROC_ROOT + "small_dungeon/"
STRUCTURE = "data/betterdungeons/worldgen/structure/small_dungeon.json"
SET = "data/betterdungeons/worldgen/structure_set/small_dungeons.json"

# 1.21.1 -> 26.3 block ids the carried palette needs. Each is proved by the 26.3
# registry: the target exists there and the source does not.
RENAMES = {"minecraft:chain": "minecraft:iron_chain"}

# The block entities the templates carry, in `PAYLOAD_*` order.
PAYLOADS = ["minecraft:chest", "minecraft:barrel", "minecraft:banner",
            "minecraft:mob_spawner", "minecraft:skull", "minecraft:jukebox",
            "minecraft:furnace"]

# The processor types this port implements: JSON `processor_type` -> (KIND, parameter field).
PROCESSORS = {
    "betterdungeons:small_dungeon_banner_processor": ("BANNER", "dungeon_type"),
    "betterdungeons:mob_spawner_processor": ("SPAWNER", "spawner_mob"),
    "betterdungeons:candle_processor": ("CANDLE", None),
    "betterdungeons:head_processor": ("HEAD", None),
    "betterdungeons:nether_block_processor": ("NETHER_BLOCK", None),
    "betterdungeons:small_dungeon_chest_processor": ("CHEST", None),
    "betterdungeons:small_dungeon_ceiling_prop_processor": ("CEILING_PROP", None),
    "betterdungeons:small_dungeon_ceiling_lamp_processor": ("CEILING_LAMP", None),
    "betterdungeons:small_dungeon_cobblestone_processor": ("COBBLESTONE", None),
    "betterdungeons:small_dungeon_leg_processor": ("LEG", None),
    "betterdungeons:small_dungeon_ceiling_processor": ("CEILING", None),
    "betterdungeons:small_dungeon_ore_processor": ("ORE", None),
    "minecraft:rule": ("RULE", None),
}
KINDS = ["BANNER", "SPAWNER", "CANDLE", "HEAD", "NETHER_BLOCK", "CHEST",
         "CEILING_PROP", "CEILING_LAMP", "COBBLESTONE", "LEG", "CEILING", "ORE",
         "RULE"]

FACING = ["north", "east", "south", "west"]
CLOCKWISE = {"north": "east", "east": "south", "south": "west", "west": "north"}
VERTICAL = {"up", "down"}
ROTATIONS = (0, 1, 2, 3)  # clockwise quarter turns


# --------------------------------------------------------------- 26.3 resources


def registry_blocks():
    with open(os.path.join(RES, "registries.json")) as f:
        return set(json.load(f)["minecraft:block"]["entries"])


def state_schemas():
    """block -> {property: allowed values}, from the prepared 26.3 model-state table.

    `assets/minecraft/blockstates/*.json` is not usable for this at 26.3: the
    prepared export collapses most blocks to one variant key. `model-states.json`
    is the game's own per-block state table instead.
    """
    with open(os.path.join(RES, "model-states.json")) as f:
        table = json.load(f)
    out = {}
    for block, entry in table.items():
        schema = entry["schema"]
        allowed = {}
        for name, kind in schema.items():
            if "named" in kind:
                allowed[name] = set(kind["named"])
            elif "integer" in kind:
                low, high = kind["integer"]
                allowed[name] = {str(value) for value in range(low, high + 1)}
            else:
                raise SystemExit("%s: property %s has no known kind" % (block, name))
        out[block] = allowed
    return out


# ---------------------------------------------------------------- state algebra


def rotate_facing(value, turns):
    if value in VERTICAL or value not in CLOCKWISE:
        return value
    for _ in range(turns % 4):
        value = CLOCKWISE[value]
    return value


def rotate_state(name, props, turns):
    """One clockwise quarter turn of a state, property by property.

    The property set is the carried palette's, enumerated: a property without a
    rule stops the generation rather than being guessed.
    """
    out = {}
    for key, value in props.items():
        if key == "facing":
            out[key] = rotate_facing(value, turns)
        elif key == "axis":
            out[key] = ({"x": "z", "z": "x"}.get(value, value)
                        if turns % 2 else value)
        elif key == "orientation":
            front, top = value.split("_")
            out[key] = "%s_%s" % (rotate_facing(front, turns),
                                  rotate_facing(top, turns))
        elif key == "rotation":
            out[key] = str((int(value) + 4 * (turns % 4)) % 16)
        elif key == "shape":
            out[key] = ({"left": "right", "right": "left",
                         "inner_left": "inner_right",
                         "inner_right": "inner_left",
                         "outer_left": "outer_right",
                         "outer_right": "outer_left"}.get(value, value)
                        if turns % 2 else value)
        elif key == "type" and name in ("minecraft:chest", "minecraft:trapped_chest"):
            out[key] = ({"left": "right", "right": "left"}.get(value, value)
                        if turns % 2 else value)
        elif key == "type":  # a slab's top/bottom/double does not turn
            out[key] = value
        elif key in ("half", "waterlogged", "lit", "open", "powered", "has_record",
                     "hanging", "candles", "pickles", "stage", "level", "age",
                     "distance"):
            out[key] = value
        else:
            raise SystemExit("%s{%s=%s}: property %r has no rotation rule"
                             % (name, key, value, key))
    return name, tuple(sorted(out.items()))


class States:
    """The state table; every entry keeps its four clockwise rotations."""

    def __init__(self):
        self.index = {}
        self.entries = []
        self.rot = []

    def get(self, name, props, turns=0):
        key = rotate_state(name, dict(props), turns)
        if key not in self.index:
            self.index[key] = len(self.entries)
            self.entries.append(key)
        return self.index[key]

    def resolve(self):
        self.rot = [[self.get(name, dict(props), k) for k in ROTATIONS]
                    for name, props in self.entries]


# -------------------------------------------------------------------- jar input


def read_jar():
    with zipfile.ZipFile(JAR) as z:
        names = z.namelist()
        templates = sorted(n for n in names
                           if n.startswith(TEMPLATE_ROOT) and n.endswith(".nbt"))
        if len(templates) != 16:
            raise SystemExit("expected 16 small_dungeon templates, found %d"
                             % len(templates))
        wanted = (SHELL_POOL, LOOT_POOL, STRUCTURE, SET) + tuple(
            sorted(n for n in names
                   if n.startswith(SMALL_PROC) and n.endswith(".json")))
        jsons = {path: json.loads(z.read(path).decode("utf-8")) for path in wanted}
        trees = {}
        for path in templates:
            with tempfile.NamedTemporaryFile(suffix=".nbt", delete=False) as tmp:
                tmp.write(z.read(path))
                tmp_name = tmp.name
            try:
                _, root = nbt_read.load(tmp_name)
            finally:
                os.unlink(tmp_name)
            trees[path] = root
    return jsons, trees


# ---------------------------------------------------------------------- emitting


def pool_id(path: str) -> str:
    """`data/betterdungeons/worldgen/template_pool/a/b.json` -> `betterdungeons:a/b`."""
    prefix = "data/betterdungeons/worldgen/template_pool/"
    if not path.startswith(prefix):
        raise SystemExit("%s is not a template pool" % path)
    return "betterdungeons:" + path[len(prefix):-len(".json")]


def sanitize(text):
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").upper()


def opt(value):
    if value is None:
        return "None"
    if isinstance(value, str):
        return "Some(%s)" % json.dumps(value)
    return "Some(%d)" % value


def register_states(trees, blocks, schemas, states):
    """Every palette state, checked against the 26.3 registry and state table."""
    for path, root in sorted(trees.items()):
        for entry in root.get("palette") or []:
            name = RENAMES.get(entry["Name"], entry["Name"])
            if name not in blocks:
                raise SystemExit("%s: palette block %s is not in the 26.3 registry"
                                 % (path, name))
            schema = schemas.get(name)
            if schema is None:
                raise SystemExit("%s: %s has no state table" % (path, name))
            props = entry.get("Properties") or {}
            for key, value in props.items():
                if key not in schema:
                    raise SystemExit("%s: %s has no property %r in 26.3"
                                     % (path, name, key))
                if value not in schema[key]:
                    raise SystemExit("%s: %s does not accept %s=%s in 26.3"
                                     % (path, name, key, value))
            states.get(name, props, 0)
    # The chains' own states, kept explicit so an index never depends on a template.
    for colour in ("candle", "white_candle", "gray_candle", "light_gray_candle",
                   "brown_candle", "green_candle", "purple_candle", "black_candle"):
        for count in ("1", "2", "3", "4"):
            for lit in ("false", "true"):
                states.get("minecraft:" + colour,
                           {"candles": count, "lit": lit, "waterlogged": "false"})
    states.get("minecraft:iron_chain", {"axis": "y", "waterlogged": "false"})
    for pickles in ("1", "2", "3", "4"):
        for waterlogged in ("false", "true"):
            states.get("minecraft:sea_pickle",
                       {"pickles": pickles, "waterlogged": waterlogged})
    for facing in FACING:
        states.get("minecraft:black_wall_banner", {"facing": facing})
        states.get("minecraft:red_wall_banner", {"facing": facing})
    for name in ("minecraft:air", "minecraft:cave_air", "minecraft:cobblestone",
                 "minecraft:mossy_cobblestone", "minecraft:mossy_stone_bricks",
                 "minecraft:cracked_stone_bricks", "minecraft:stone_bricks",
                 "minecraft:spawner", "minecraft:coarse_dirt", "minecraft:campfire",
                 "minecraft:lantern", "minecraft:soul_sand", "minecraft:soul_soil",
                 "minecraft:soul_campfire", "minecraft:soul_lantern"):
        if name not in blocks or name not in schemas:
            raise SystemExit("processor state %s is not in the 26.3 registry" % name)
        states.get(name, {}, 0)


def emit_templates(trees, states):
    loot = {}
    out = io.StringIO()
    out.write(
        "//! The carried `small_dungeon` templates, generated from the jar.\n//!\n"
        "//! Generated by `tools/gen_tables.py` from\n"
        "//! `YungsBetterDungeons-1.21.1-NeoForge-5.1.4.jar` (LGPL-3.0-only); do not edit.\n"
        "//! `python3 tools/gen_tables.py --check` proves this file is what the jar yields.\n"
        "//!\n"
        "//! Every state here is one the prepared 26.3 resources accept: the generator checks\n"
        "//! each block name, property and value against `registries.json` and the blockstate\n"
        "//! files, and maps the ids 26.3 renamed (see `RENAMES` there).\n\n"
        "/// One block state, as a carried template or a processor chain names it.\n"
        "#[derive(Clone, Copy, Debug)]\n"
        "pub struct State {\n"
        "    /// Canonical block id, `minecraft:stone_bricks`.\n"
        "    pub name: &'static str,\n"
        "    /// Its properties, in the template's own spelling.\n"
        "    pub props: &'static [(&'static str, &'static str)],\n"
        "}\n\n"
        "/// Every state the templates and the processor chains name.\n"
        "pub static STATES: &[State] = &[\n"
    )
    for name, props in states.entries:
        rendered = ", ".join('("%s", "%s")' % (k, v) for k, v in props)
        out.write('    State { name: %s, props: &[%s] },\n' % (json.dumps(name), rendered))
    out.write("];\n\n")
    out.write(
        "/// `ROTATED[state][k]` is `state` after `k` clockwise quarter turns.\n"
        "/// The generator resolves them, so no Rust code needs a block's rotation rules.\n"
        "pub static ROTATED: &[[u16; 4]] = &[\n"
    )
    for row in states.rot:
        out.write("    [%s],\n" % ", ".join(str(v) for v in row))
    out.write("];\n\n")
    out.write(
        "/// A template block: its position in the template, its state, its payload.\n"
        "#[derive(Clone, Copy, Debug)]\n"
        "pub struct Block {\n"
        "    /// Position in the template, before rotation.\n"
        "    pub pos: [i16; 3],\n"
        "    /// Index into [`STATES`].\n"
        "    pub state: u16,\n"
        "    /// A `PAYLOAD_*` value: the block entity the template carries.\n"
        "    pub payload: u8,\n"
        "}\n\n"
        "/// A jigsaw connector a template carries.\n"
        "#[derive(Clone, Copy, Debug)]\n"
        "pub struct Jigsaw {\n"
        "    /// Position in the template, before rotation.\n"
        "    pub pos: [i16; 3],\n"
        "    /// Index into [`STATES`]: the jigsaw block's own state, whose `orientation`\n"
        "    /// names its front and top.\n"
        "    pub state: u16,\n"
        "    /// The pool this connector draws from.\n"
        "    pub pool: &'static str,\n"
        "    /// This connector's name, which a child's `target` must equal.\n"
        "    pub name: &'static str,\n"
        "    /// The name this connector wants on the child it attaches to.\n"
        "    pub target: &'static str,\n"
        "    /// The state the connector block becomes once placed.\n"
        "    pub final_state: u16,\n"
        "}\n\n"
        "/// One carried template.\n"
        "#[derive(Clone, Copy, Debug)]\n"
        "pub struct Template {\n"
        "    /// The id a pool entry names, `betterdungeons:small_dungeon/shells/small_shell_5x5`.\n"
        "    pub id: &'static str,\n"
        "    /// Its size, before rotation.\n"
        "    pub size: [i16; 3],\n"
        "    /// Its blocks, in the template's own order.\n"
        "    pub blocks: &'static [Block],\n"
        "    /// Its jigsaw connectors.\n"
        "    pub jigsaws: &'static [Jigsaw],\n"
        "}\n\n"
    )
    ids = []
    for path, root in sorted(trees.items()):
        tid = "betterdungeons:" + path[len("data/betterdungeons/structure/"):-len(".nbt")]
        ids.append(tid)
        const = sanitize(tid)
        palette = root.get("palette") or []
        state_of = [states.get(RENAMES.get(p["Name"], p["Name"]),
                               p.get("Properties") or {}, 0) for p in palette]
        block_lines = []
        jigsaw_lines = []
        for block in root.get("blocks") or []:
            pos = block["pos"]
            state = state_of[block["state"]]
            payload = block.get("nbt") or {}
            pid = payload.get("id")
            if pid == "minecraft:jigsaw":
                entry = payload
                props = palette[block["state"]].get("Properties") or {}
                if "orientation" not in props:
                    raise SystemExit("%s: a jigsaw block without an orientation" % path)
                final = entry.get("final_state", "minecraft:air").split("[")[0]
                final = RENAMES.get(final, final)
                jigsaw_lines.append(
                    "    Jigsaw { pos: [%d, %d, %d], state: %d, pool: %s, name: %s, "
                    "target: %s, final_state: %d },"
                    % (pos[0], pos[1], pos[2], state,
                       json.dumps(entry.get("pool")), json.dumps(entry.get("name")),
                       json.dumps(entry.get("target", entry.get("name"))),
                       states.get(final, {}, 0)))
                continue
            if pid is None:
                payload_id = 0
            elif pid in PAYLOADS:
                payload_id = PAYLOADS.index(pid) + 1
            else:
                raise SystemExit("%s: block entity %s has no payload" % (path, pid))
            if pid in ("minecraft:chest", "minecraft:barrel"):
                table = payload.get("LootTable")
                if table is None:
                    raise SystemExit("%s: a %s without a LootTable" % (path, pid))
                loot.setdefault(pid, {}).setdefault(table, 0)
                loot[pid][table] += 1
            block_lines.append(
                "    Block { pos: [%d, %d, %d], state: %d, payload: %d },"
                % (pos[0], pos[1], pos[2], state, payload_id))
        out.write("/// `%s`\n" % tid)
        out.write("static B_%s: &[Block] = &[\n%s\n];\n"
                  % (const, "\n".join(block_lines)))
        out.write("static J_%s: &[Jigsaw] = &[\n%s\n];\n"
                  % (const, "\n".join(jigsaw_lines)))
        size = root["size"]
        out.write(
            "static T_%s: Template = Template { id: %s, size: [%d, %d, %d], "
            "blocks: B_%s, jigsaws: J_%s };\n\n"
            % (const, json.dumps(tid), size[0], size[1], size[2], const, const))
    out.write("/// The carried templates.\npub static TEMPLATES: &[Template] = &[\n")
    for tid in ids:
        out.write("    T_%s,\n" % sanitize(tid))
    out.write("];\n\n")
    out.write(
        "/// The template `id` names, or `None`.\n"
        "pub fn template(id: &str) -> Option<&'static Template> {\n"
        "    TEMPLATES.iter().find(|template| template.id == id)\n"
        "}\n\n"
    )
    for index, suffix in enumerate(["NONE"] + [PAYLOADS and sanitize(p) for p in PAYLOADS]):
        pass
    out.write("/// No block entity.\npub const PAYLOAD_NONE: u8 = 0;\n")
    for index, name in enumerate(PAYLOADS, start=1):
        out.write("/// `%s`.\npub const PAYLOAD_%s: u8 = %d;\n"
                  % (name, sanitize(name), index))
    for name, suffix in (("minecraft:chest", "CHEST"), ("minecraft:barrel", "BARREL")):
        tables = loot.get(name, {})
        if len(tables) != 1:
            raise SystemExit("%s: expected one loot table across the templates, found %s"
                             % (name, sorted(tables)))
        table = next(iter(tables))
        out.write("\n/// The loot table every `%s` in the carried templates asks for.\n"
                  "pub const %s_LOOT: &str = %s;\n" % (name, suffix, json.dumps(table)))
    return out.getvalue()


def emit_pools(jsons, states):
    out = io.StringIO()
    out.write(
        "//! The carried `small_dungeon` pools, processor chains and structure definition.\n//!\n"
        "//! Generated by `tools/gen_tables.py` from the jar; do not edit. These are the jar's\n"
        "//! own weights, order and limits in a form a Rust `StructureType` can run: the\n"
        "//! data-pack form of the pools is what the engine refuses to decode\n"
        "//! (`yungsapi:yung_single_element` and the mod's own `betterdungeons:*` processor\n"
        "//! types).\n\n"
        "/// One weighted pool element.\n"
        "#[derive(Clone, Copy, Debug)]\n"
        "pub struct Element {\n"
        "    /// Its weight in the pool.\n"
        "    pub weight: i32,\n"
        "    /// The template it places.\n"
        "    pub template: &'static str,\n"
        "    /// The processor list it runs, `minecraft:empty` for none.\n"
        "    pub processors: &'static str,\n"
        "    /// Its `name`, which a parent's `target` must equal; `max_count` needs it.\n"
        "    pub name: Option<&'static str>,\n"
        "    /// Its `max_count` in the whole structure, when limited.\n"
        "    pub max_count: Option<i32>,\n"
        "}\n\n"
        "/// One template pool.\n"
        "#[derive(Clone, Copy, Debug)]\n"
        "pub struct Pool {\n"
        "    /// Its id.\n"
        "    pub id: &'static str,\n"
        "    /// The pool drawn when this one yields nothing.\n"
        "    pub fallback: &'static str,\n"
        "    /// Its elements, in the jar's file order (a draw shuffles a copy).\n"
        "    pub elements: &'static [Element],\n"
        "}\n\n"
    )
    # A pool's registry id is its file's path, not the `name` field the jar also
    # carries (vanilla's `StructureTemplatePool` codec has no `name`: it is a
    # leftover from older datapack editors, and the loot-pile file's value even
    # disagrees with its own id — see notes.md).
    pools = [(pool_id(path), jsons[path]) for path in (SHELL_POOL, LOOT_POOL)]
    for index, (pool_name, pool) in enumerate(pools):
        out.write("static E_%d: &[Element] = &[\n" % index)
        for entry in pool["elements"]:
            element = entry["element"]
            kind = element["element_type"]
            if kind not in ("minecraft:single_pool_element", "yungsapi:yung_single_element"):
                raise SystemExit("pool %s: element type %s is not carried"
                                 % (pool_name, kind))
            location = element["location"]
            if not location.startswith("betterdungeons:"):
                raise SystemExit("pool %s: template %s is outside the mod"
                                 % (pool_name, location))
            if element.get("projection") != "rigid":
                raise SystemExit("pool %s: only rigid projections are carried"
                                 % (pool_name,))
            unknown = set(element) - {"location", "processors", "projection",
                                      "element_type", "name", "max_count"}
            if unknown:
                raise SystemExit("pool %s: element field(s) %s are not carried"
                                 % (pool_name, sorted(unknown)))
            name = element.get("name") if kind != "minecraft:single_pool_element" else None
            max_count = element.get("max_count") if kind != "minecraft:single_pool_element" else None
            if max_count is not None and name is None:
                raise SystemExit("pool %s: max_count without a name" % pool_name)
            out.write(
                "    Element { weight: %d, template: %s, processors: %s, name: %s, "
                "max_count: %s },\n"
                % (entry["weight"], json.dumps(location),
                   json.dumps(element.get("processors", "minecraft:empty")),
                   opt(name), opt(max_count)))
        out.write("];\n")
    out.write("/// The carried pools.\npub static POOLS: &[Pool] = &[\n")
    for index, (pool_name, pool) in enumerate(pools):
        out.write("    Pool { id: %s, fallback: %s, elements: E_%d },\n"
                  % (json.dumps(pool_name), json.dumps(pool["fallback"]), index))
    out.write("];\n\n")
    out.write(
        "/// The pool `id` names, or `None`.\n"
        "pub fn pool(id: &str) -> Option<&'static Pool> {\n"
        "    POOLS.iter().find(|pool| pool.id == id)\n"
        "}\n\n"
        "/// One `minecraft:rule` processor's rule.\n"
        "#[derive(Clone, Copy, Debug)]\n"
        "pub struct Rule {\n"
        "    /// The state it matches.\n"
        "    pub input: u16,\n"
        "    /// The state it writes.\n"
        "    pub output: u16,\n"
        "    /// Its chance; 1.0 for `block_match`.\n"
        "    pub probability: f32,\n"
        "}\n\n"
        "/// One processor in a chain, in the jar's order.\n"
        "#[derive(Clone, Copy, Debug)]\n"
        "pub struct Step {\n"
        "    /// A `KIND_*` value naming the processor.\n"
        "    pub kind: u8,\n"
        "    /// Its parameter: the dungeon type, or the spawner's mob id.\n"
        "    pub text: &'static str,\n"
        "    /// Its rules, for `KIND_RULE`.\n"
        "    pub rules: &'static [Rule],\n"
        "}\n\n"
        "/// One processor list.\n"
        "#[derive(Clone, Copy, Debug)]\n"
        "pub struct ProcList {\n"
        "    /// Its id.\n"
        "    pub id: &'static str,\n"
        "    /// Its processors, in the jar's order.\n"
        "    pub steps: &'static [Step],\n"
        "}\n\n"
    )
    lists = []
    for index, path in enumerate(sorted(p for p in jsons if p.startswith(SMALL_PROC))):
        data = jsons[path]
        rules_names = {}
        for step_index, step in enumerate(data["processors"]):
            kind = step["processor_type"]
            if kind not in PROCESSORS:
                raise SystemExit("%s: processor %s is not implemented by this port"
                                 % (path, kind))
            allowed = {"processor_type", PROCESSORS[kind][1], "rules"}
            unknown = set(step) - {k for k in allowed if k}
            if unknown:
                raise SystemExit("%s: processor field(s) %s are not carried"
                                 % (path, sorted(unknown)))
            if kind != "minecraft:rule":
                continue
            name = "R_%d_%d" % (index, step_index)
            rules_names[step_index] = name
            out.write("static %s: &[Rule] = &[\n" % name)
            for rule in step["rules"]:
                pred = rule["input_predicate"]
                if pred["predicate_type"] not in ("minecraft:block_match",
                                                  "minecraft:random_block_match"):
                    raise SystemExit("%s: predicate %s is not carried"
                                     % (path, pred["predicate_type"]))
                if rule.get("location_predicate", {}).get("predicate_type") != "minecraft:always_true":
                    raise SystemExit("%s: a location predicate is not carried" % path)
                state = rule["output_state"]
                out.write(
                    "    Rule { input: %d, output: %d, probability: %sf32 },\n"
                    % (states.get(pred["block"], {}, 0),
                       states.get(RENAMES.get(state["Name"], state["Name"]),
                                  state.get("Properties") or {}, 0),
                       repr(float(pred.get("probability", 1.0)))))
            out.write("];\n")
        out.write("static S_%d: &[Step] = &[\n" % index)
        for step_index, step in enumerate(data["processors"]):
            kind = step["processor_type"]
            suffix, param = PROCESSORS[kind]
            rules = rules_names.get(step_index, "&[]")
            text = json.dumps(step.get(param, "") if param else "")
            out.write("    Step { kind: KIND_%s, text: %s, rules: %s },\n"
                      % (suffix, text, rules))
        out.write("];\n")
        lists.append(("betterdungeons:" + path[len(PROC_ROOT):-len(".json")], index))
    out.write("/// The carried processor lists.\npub static PROCESSOR_LISTS: &[ProcList] = &[\n")
    for name, index in lists:
        out.write("    ProcList { id: %s, steps: S_%d },\n" % (json.dumps(name), index))
    out.write("];\n\n")
    out.write(
        "/// The processor list `id` names, or `None`.\n"
        "pub fn processor_list(id: &str) -> Option<&'static ProcList> {\n"
        "    PROCESSOR_LISTS.iter().find(|list| list.id == id)\n"
        "}\n\n"
    )
    for index, suffix in enumerate(KINDS):
        out.write("/// `%s`.\npub const KIND_%s: u8 = %d;\n" % (suffix, suffix, index))
    out.write("\n")

    structure = jsons[STRUCTURE]
    placement = jsons[SET]["placement"]
    out.write(
        "/// The structure definition as the jar carries it. `/betterdungeons status` reports\n"
        "/// it, and `find_generation_point` compares a pack's own config against it.\n"
        "#[derive(Clone, Copy, Debug)]\n"
        "pub struct StructureDef {\n"
    )
    fields = [
        ("id", "str", "Its id."),
        ("worldgen_type", "str", "The jar's `type` (`yungsapi:yung_jigsaw`)."),
        ("start_pool", "str", "Its `start_pool`."),
        ("start_jigsaw", "opt", "Its `start_jigsaw_name`."),
        ("size", "i32", "Its `size`, the jigsaw depth cap."),
        ("start_y", "range", "Its `start_height` as an inclusive absolute range."),
        ("max_distance", "i32", "Its `max_distance_from_center`."),
        ("use_expansion_hack", "bool", "Its `use_expansion_hack`."),
        ("step", "str", "Its `step`."),
        ("biomes", "str", "Its `biomes` tag."),
        ("liquid_settings", "str", "Its `liquid_settings`."),
        ("salt", "i32", "Its structure set's `salt`."),
        ("spacing", "i32", "Its structure set's `spacing`, in chunks."),
        ("separation", "i32", "Its structure set's `separation`, in chunks."),
    ]
    for name, kind, doc in fields:
        out.write("    /// %s\n" % doc)
        out.write("    pub %s: %s,\n"
                  % (name, {"str": "&'static str", "i32": "i32", "bool": "bool",
                            "opt": "Option<&'static str>",
                            "range": "(i32, i32)"}[kind]))
    out.write("}\n\n")
    out.write("/// The jar's `small_dungeon` definition.\n")
    out.write("pub static STRUCTURE: StructureDef = StructureDef {\n")
    low = structure["start_height"]["min_inclusive"]["absolute"]
    high = structure["start_height"]["max_inclusive"]["absolute"]
    out.write('    id: "betterdungeons:small_dungeon",\n')
    out.write("    worldgen_type: %s,\n" % json.dumps(structure["type"]))
    out.write("    start_pool: %s,\n" % json.dumps(structure["start_pool"]))
    out.write("    start_jigsaw: %s,\n" % opt(structure.get("start_jigsaw_name")))
    out.write("    size: %d,\n" % structure["size"])
    out.write("    start_y: (%d, %d),\n" % (low, high))
    out.write("    max_distance: %d,\n" % structure["max_distance_from_center"])
    out.write("    use_expansion_hack: %s,\n"
              % str(bool(structure.get("use_expansion_hack", False))).lower())
    out.write("    step: %s,\n" % json.dumps(structure["step"]))
    out.write("    biomes: %s,\n" % json.dumps(structure["biomes"]))
    out.write("    liquid_settings: %s,\n"
              % json.dumps(structure.get("liquid_settings", "apply_waterlogging")))
    out.write("    salt: %d,\n" % placement["salt"])
    out.write("    spacing: %d,\n" % placement["spacing"])
    out.write("    separation: %d,\n" % placement["separation"])
    out.write("};\n")
    return out.getvalue()


# ------------------------------------------------------------------------- driver


def generate():
    states = States()
    blocks = registry_blocks()
    schemas = state_schemas()
    jsons, trees = read_jar()
    register_states(trees, blocks, schemas, states)
    # The template pass registers any state it names that `register_states` did
    # not (a palette entry's own spelling), so the rotations are resolved only
    # after it has run once: `ROTATED` must have a row per `STATES` entry.
    emit_templates(trees, states)
    states.resolve()
    outputs = {
        "src/templates.rs": emit_templates(trees, states),
        "src/pools.rs": emit_pools(jsons, states),
    }
    if len(states.rot) != len(states.entries):
        raise SystemExit("%d states but %d rotation rows" % (len(states.entries), len(states.rot)))
    status = 0
    for name, text in outputs.items():
        path = os.path.join(PORT, name)
        if "--check" in sys.argv:
            with tempfile.NamedTemporaryFile("w", suffix=".rs", delete=False) as tmp:
                tmp.write(text)
                tmp_name = tmp.name
            subprocess.run(["rustfmt", "--edition", "2024", tmp_name], check=True)
            with open(tmp_name) as f:
                generated = f.read()
            os.unlink(tmp_name)
            try:
                with open(path) as f:
                    committed = f.read()
            except FileNotFoundError:
                committed = ""
            if generated != committed:
                print("DRIFT: %s is not what the jar yields" % name)
                status = 1
            else:
                print("ok %s (%d bytes)" % (name, len(committed)))
        else:
            with open(path, "w") as f:
                f.write(text)
            subprocess.run(["rustfmt", "--edition", "2024", path], check=True)
            print("wrote %s (%d bytes)" % (name, os.path.getsize(path)))
    return status


if __name__ == "__main__":
    sys.exit(generate())
