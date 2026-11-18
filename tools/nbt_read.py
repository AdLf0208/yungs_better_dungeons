#!/usr/bin/env python3
"""Read-only NBT (gzip or raw) dumper used to inventory the jar's structure templates.

Not part of the package; it is the evidence tool that produced notes.md's template
inventory (palette, blocks, jigsaw blocks, entities).  Only the standard library.
"""
import gzip
import io
import struct
import sys
import zlib


class Reader:
    def __init__(self, data: bytes):
        self.f = io.BytesIO(data)

    def take(self, n: int) -> bytes:
        b = self.f.read(n)
        if len(b) != n:
            raise EOFError("short read")
        return b

    def u1(self) -> int:
        return self.take(1)[0]

    def i2(self) -> int:
        return struct.unpack(">h", self.take(2))[0]

    def u2(self) -> int:
        return struct.unpack(">H", self.take(2))[0]

    def i4(self) -> int:
        return struct.unpack(">i", self.take(4))[0]

    def i8(self) -> int:
        return struct.unpack(">q", self.take(8))[0]

    def f4(self) -> float:
        return struct.unpack(">f", self.take(4))[0]

    def f8(self) -> float:
        return struct.unpack(">d", self.take(8))[0]

    def string(self) -> str:
        return self.take(self.u2()).decode("utf-8", "replace")


def payload(r: Reader, tag: int, depth: int = 0):
    if tag == 1:
        return r.u1()
    if tag == 2:
        return r.i2()
    if tag == 3:
        return r.i4()
    if tag == 4:
        return r.i8()
    if tag == 5:
        return r.f4()
    if tag == 6:
        return r.f8()
    if tag == 7:
        return [r.u1() for _ in range(r.i4())]
    if tag == 8:
        return r.string()
    if tag == 9:
        sub = r.u1()
        n = r.i4()
        return [payload(r, sub, depth + 1) for _ in range(n)]
    if tag == 10:
        out = {}
        while True:
            t = r.u1()
            if t == 0:
                return out
            name = r.string()
            out[name] = payload(r, t, depth + 1)
    if tag == 11:
        return [r.i4() for _ in range(r.i4())]
    if tag == 12:
        return [r.i8() for _ in range(r.i4())]
    raise ValueError(f"bad tag {tag}")


def load(path: str):
    raw = open(path, "rb").read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    elif raw[:1] not in (b"\x0a", b"\x08"):
        try:
            raw = zlib.decompress(raw)
        except zlib.error:
            pass
    r = Reader(raw)
    t = r.u1()
    if t != 10:
        raise ValueError(f"root is not a compound: {t}")
    name = r.string()
    return name, payload(r, 10)


def summarize(path: str) -> None:
    name, root = load(path)
    print(f"== {path} root={name!r}")
    print("   size", root.get("size"), "data_version", root.get("DataVersion"))
    palette = root.get("palette", [])
    print(f"   palette {len(palette)}:")
    for entry in palette:
        print("     ", entry)
    blocks = root.get("blocks", [])
    print(f"   blocks {len(blocks)}")
    for b in blocks:
        nbt = b.get("nbt")
        if nbt:
            print("     block", b["pos"], b["state"], "nbt:", {k: v for k, v in nbt.items() if k in ("id", "LootTable", "joint", "name", "pool", "target", "final_state")})
    for e in root.get("entities", []):
        print("   entity", e.get("pos"), e.get("blockPos"), e.get("nbt", {}).get("id"))
    print(f"   entities {len(root.get('entities', []))}")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        summarize(arg)
