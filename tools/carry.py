#!/usr/bin/env python3
"""Carry the `small_dungeon` subset of the jar into this package, and prove it.

Reads `ports/_shared/licence-cache/YungsBetterDungeons-1.21.1-NeoForge-5.1.4.jar`
(LGPL-3.0-only) and writes the slice's content:

    data/betterdungeons/structure/small_dungeon/**.nbt      16 templates, verbatim
    data/betterdungeons/loot_table/small_dungeon/chests/    the loot pile table
    data/betterdungeons/tags/worldgen/biome/has_structure/  the biome tag
    data/betterdungeons/worldgen/structure_set/            the random-spread set
    data/betterdungeons/worldgen/structure/small_dungeon.json
                                                            only `type` rewritten
    assets/betterdungeons/lang/en_us.json                   the banner names
    LICENSE                                                 the jar's own licence

The two template pools and the four processor lists are carried to
`carry-work/jar/` instead of `data/`: their `yungsapi:yung_single_element` element
type and the mod's own `betterdungeons:*` processor types are what the engine
refuses to decode (a pack carrying them fails before it generates anything), so
the port's generated Rust tables are their loadable form and
`tools/check_content.py` proves table ≡ jar.

    python3 tools/carry.py            # write the package's content
    python3 tools/carry.py --check    # prove every carried byte still matches
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = os.path.dirname(HERE)
JAR = os.environ.get(
    "BD_JAR",
    os.path.join(HERE, "..", "..", "..", "ports", "_shared", "licence-cache",
                 "YungsBetterDungeons-1.21.1-NeoForge-5.1.4.jar"),
)
MANIFEST = os.path.join(PORT, "carry-manifest.json")

TEMPLATES = "data/betterdungeons/structure/small_dungeon/"
VERBATIM = [
    "data/betterdungeons/loot_table/small_dungeon/chests/loot_piles.json",
    "data/betterdungeons/tags/worldgen/biome/has_structure/small_dungeon.json",
    "data/betterdungeons/worldgen/structure_set/small_dungeons.json",
    "assets/betterdungeons/lang/en_us.json",
]
STRUCTURE = "data/betterdungeons/worldgen/structure/small_dungeon.json"
EVIDENCE = [
    "data/betterdungeons/worldgen/template_pool/small_dungeon.json",
    "data/betterdungeons/worldgen/template_pool/small_dungeon_loot_piles.json",
    "data/betterdungeons/worldgen/processor_list/small_dungeon/small_dungeon_loot_pile.json",
    "data/betterdungeons/worldgen/processor_list/small_dungeon/small_dungeon_skeleton.json",
    "data/betterdungeons/worldgen/processor_list/small_dungeon/small_dungeon_spider.json",
    "data/betterdungeons/worldgen/processor_list/small_dungeon/small_dungeon_zombie.json",
]
LICENCE = "LICENSE_YungsBetterDungeons"
LICENCE_TARGET = "LICENSE"

# The jar's structure type is `yungsapi:yung_jigsaw`, a library this campaign
# does not port; the port registers its own type and the definition names it.
CARRIED_TYPE = "betterdungeons:small_dungeon_type"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rewrite_structure(raw: bytes) -> bytes:
    """The jar's definition with only `type` replaced, keys kept in file order."""
    text = raw.decode("utf-8")
    marker = '"type": "yungsapi:yung_jigsaw"'
    if marker not in text:
        raise SystemExit("the structure definition no longer names yungsapi:yung_jigsaw")
    return text.replace(marker, '"type": "%s"' % CARRIED_TYPE, 1).encode("utf-8")


def plan():
    """Every packaged file's bytes and where they come from."""
    out = {}
    with zipfile.ZipFile(JAR) as z:
        names = z.namelist()
        for name in sorted(n for n in names
                           if n.startswith(TEMPLATES) and n.endswith(".nbt")):
            out[name] = (z.read(name), name, "verbatim")
        for name in VERBATIM:
            out[name] = (z.read(name), name, "verbatim")
        out[STRUCTURE] = (rewrite_structure(z.read(STRUCTURE)), STRUCTURE,
                          "type rewritten to %s" % CARRIED_TYPE)
        out[LICENCE_TARGET] = (z.read(LICENCE), LICENCE, "verbatim")
        for name in EVIDENCE:
            target = os.path.join("carry-work", "jar", name.split("worldgen/")[-1])
            out[target] = (z.read(name), name, "verbatim, evidence (not packed)")
    return out


def main() -> int:
    files = plan()
    if "--check" in sys.argv:
        try:
            with open(MANIFEST) as f:
                manifest = json.load(f)["files"]
        except FileNotFoundError:
            print("no carry-manifest.json")
            return 1
        status = 0
        for path, (data, source, transform) in sorted(files.items()):
            full = os.path.join(PORT, path)
            record = manifest.get(path)
            if record is None:
                print("MISSING in the manifest: %s" % path)
                status = 1
                continue
            if record["sha256"] != sha256(data) or record["bytes"] != len(data):
                print("DRIFT: %s is not what the jar yields" % path)
                status = 1
                continue
            try:
                on_disk = open(full, "rb").read()
            except FileNotFoundError:
                print("ABSENT: %s" % path)
                status = 1
                continue
            if on_disk != data:
                print("DIFFERS: %s" % path)
                status = 1
        for path in sorted(set(manifest) - set(files)):
            print("STALE: %s is in the manifest and not in the jar plan" % path)
            status = 1
        if status == 0:
            print("ok %d files match the jar (16 templates, %d others)"
                  % (len(files), len(files) - 16))
        return status

    manifest = {"jar": os.path.basename(JAR), "jar_sha256": sha256(open(JAR, "rb").read()),
                "files": {}}
    for path, (data, source, transform) in sorted(files.items()):
        full = os.path.join(PORT, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(data)
        manifest["files"][path] = {
            "bytes": len(data),
            "sha256": sha256(data),
            "jar_entry": source,
            "transform": transform,
        }
    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=1, sort_keys=True)
        f.write("\n")
    print("carried %d files (%d bytes) from %s"
          % (len(files), sum(len(d) for d, _, _ in files.values()), os.path.basename(JAR)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
