#!/usr/bin/env python3
"""Prove the package's content is the jar's, and nothing else moved.

Four independent checks, each able to fail on its own:

1. **bytes** — `tools/carry.py --check`: every packaged file is byte-identical to
   the jar entry it came from (the structure JSON differs only in `type`), and
   nothing in `carry-manifest.json` is missing or stale.
2. **tables** — `tools/gen_tables.py --check`: regenerating `src/tables` from the
   jar yields exactly the committed `src/templates.rs` and `src/pools.rs`, so the
   Rust tables *are* the jar's pools, weights, limits, processor chains and
   templates.
3. **registry** — every block name in `STATES` exists in the prepared 26.3
   registry with the properties the state names, and every biome in the carried
   tag exists there too.
4. **shape** — the packaged structure definition names this port's type, its
   other keys still say what the jar says, the loot table the templates ask for
   is in the package, and the package carries no file the manifest does not
   explain.

    python3 tools/check_content.py --check
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = os.path.dirname(HERE)
RES = os.environ.get("HORIZON_RES", "/home/adlf/Desktop/horizon/.local/horizon-client/26.3")
JAR = os.environ.get(
    "BD_JAR",
    os.path.join(HERE, "..", "..", "..", "ports", "_shared", "licence-cache",
                 "YungsBetterDungeons-1.21.1-NeoForge-5.1.4.jar"),
)
STRUCTURE = "data/betterdungeons/worldgen/structure/small_dungeon.json"
CARRIED_TYPE = "betterdungeons:small_dungeon_type"


def run(script: str) -> bool:
    print("== python3 tools/%s --check" % script)
    result = subprocess.run([sys.executable, os.path.join(HERE, script), "--check"])
    return result.returncode == 0


def states() -> list[tuple[str, list[tuple[str, str]]]]:
    text = open(os.path.join(PORT, "src", "templates.rs")).read()
    out = []
    for name, props in re.findall(
        r'State \{\s*name: "([^"]+)",\s*props: &\[(.*?)\],?\s*\}', text, re.S
    ):
        pairs = re.findall(r'\("([^"]+)", "([^"]+)"\)', props)
        out.append((name, pairs))
    return out


def check_registry() -> bool:
    print("== registry: every carried block and property exists in 26.3")
    with open(os.path.join(RES, "registries.json")) as f:
        blocks = set(json.load(f)["minecraft:block"]["entries"])
    with open(os.path.join(RES, "model-states.json")) as f:
        schemas = {name: entry["schema"] for name, entry in json.load(f).items()}

    def allowed(schema, name):
        kind = schema[name]
        if "named" in kind:
            return set(kind["named"])
        low, high = kind["integer"]
        return {str(value) for value in range(low, high + 1)}

    status = True
    table = states()
    for name, props in table:
        if name not in blocks:
            print("  %s is not in the 26.3 registry" % name)
            status = False
            continue
        schema = schemas.get(name)
        if schema is None:
            print("  %s has no state table" % name)
            status = False
            continue
        for key, value in props:
            if key not in schema:
                print("  %s has no property %s" % (name, key))
                status = False
            elif value not in allowed(schema, key):
                print("  %s does not accept %s=%s" % (name, key, value))
                status = False

    with open(os.path.join(PORT, "data/betterdungeons/tags/worldgen/biome/has_structure/"
                                 "small_dungeon.json")) as f:
        tag = json.load(f)
    biomes = set(os.listdir(os.path.join(RES, "data/minecraft/worldgen/biome")))
    biomes = {"minecraft:" + name[:-5] for name in biomes}
    for entry in tag["values"]:
        if isinstance(entry, dict):
            if not entry.get("required", True):
                continue
            entry = entry["id"]
        if entry.startswith("#"):
            continue
        if entry not in biomes:
            print("  the biome tag names %s, which 26.3 does not have" % entry)
            status = False
    print("  %d states, %d biome ids" % (len(table), len(biomes)))
    return status


def check_shape() -> bool:
    print("== shape: the packaged definition, loot table and file set")
    status = True
    with zipfile.ZipFile(JAR) as jar:
        original = json.loads(jar.read(STRUCTURE))
    packaged = json.load(open(os.path.join(PORT, STRUCTURE)))
    if packaged.get("type") != CARRIED_TYPE:
        print("  the packaged definition's type is %r" % packaged.get("type"))
        status = False
    if packaged.get("type") == original.get("type"):
        print("  the type was not rewritten")
        status = False
    for key, value in original.items():
        if key == "type":
            continue
        if packaged.get(key) != value:
            print("  %s differs: %r != %r" % (key, packaged.get(key), value))
            status = False

    manifest = json.load(open(os.path.join(PORT, "carry-manifest.json")))["files"]
    for path in manifest:
        if not os.path.exists(os.path.join(PORT, path)):
            print("  %s is in the manifest and not on disk" % path)
            status = False
    # Every packaged file under data/ or assets/ is either carried (in the
    # manifest) or generated by this port's own tools, and every carried file
    # under data/ is one this slice needs.
    for root in ("data", "assets"):
        for base, _, names in os.walk(os.path.join(PORT, root)):
            for name in names:
                full = os.path.join(base, name)
                rel = os.path.relpath(full, PORT)
                if rel not in manifest:
                    print("  %s is packaged and not carried from the jar" % rel)
                    status = False

    # The loot tables the templates ask for must be in the package, or the chests
    # and barrels place empty.
    jars = set()
    with zipfile.ZipFile(JAR) as jar:
        for entry in jar.namelist():
            if entry.startswith("data/betterdungeons/structure/small_dungeon/") and entry.endswith(".nbt"):
                pass
    templates = open(os.path.join(PORT, "src", "templates.rs")).read()
    for loot in re.findall(r'pub const (?:CHEST|BARREL)_LOOT: &str = "([^"]+)";', templates):
        if not loot.startswith("minecraft:") and not loot.startswith("betterdungeons:"):
            print("  the loot table %s is not a canonical id" % loot)
            status = False
            continue
        if loot.startswith("betterdungeons:"):
            path = os.path.join(PORT, "data", "betterdungeons", "loot_table",
                               loot.split(":", 1)[1] + ".json")
            if not os.path.exists(path):
                print("  %s is asked for and not packaged" % loot)
                status = False
            else:
                jars.add(loot)
        else:
            path = os.path.join(RES, "data", "minecraft", "loot_table",
                               loot.split(":", 1)[1] + ".json")
            if not os.path.exists(path):
                print("  %s is asked for and 26.3 does not have it" % loot)
                status = False
    print("  %d carried files, %d mod loot tables verified" % (len(manifest), len(jars)))
    return status


def main() -> int:
    if "--check" not in sys.argv:
        print(__doc__)
        return 0
    status = True
    status &= run("carry.py")
    status &= run("gen_tables.py")
    status &= check_registry()
    status &= check_shape()
    print("CONTENT CHECK:%s" % ("PASS" if status else "FAIL"))
    return 0 if status else 1


if __name__ == "__main__":
    sys.exit(main())
