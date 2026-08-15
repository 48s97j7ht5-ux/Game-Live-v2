#!/usr/bin/env python3
"""Export MB-Lab dummy OBJs.

Topology comes from humanoid_library.blend (official MB-Lab templates).
Rest poses come from data/vertices/*_verts.json (character library).

Blender is Z-up; the workbench is Y-up: (x, y, z) -> (x, z, -y).
Meshes are AGPL-3.0 — see models/mblab/NOTICE.
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "models" / "mblab"

HEADER = """# MB-Lab {label}
# Source: https://github.com/animate1978/MB-Lab
# Mesh and JSON data: GNU Affero GPL v3 (AGPL-3.0)
# This is a character template dummy, not a MakeHuman hm08 morph.
o body
g body
"""


def align4(n: int) -> int:
    return (n + 3) & ~3


class Blend:
    def __init__(self, data: bytes):
        self.data = data
        hdr = data[:12]
        if not hdr.startswith(b"BLENDER"):
            raise ValueError("not a blend file")
        self.ptr = 8 if hdr[7:8] == b"-" else 4
        self.endian = "<" if hdr[8:9] == b"v" else ">"
        self.blocks = []
        self.by_addr = {}
        off = 12
        while off + 16 <= len(data):
            code = data[off : off + 4]
            size = struct.unpack_from(self.endian + "I", data, off + 4)[0]
            if self.ptr == 8:
                old = struct.unpack_from(self.endian + "Q", data, off + 8)[0]
                sdna = struct.unpack_from(self.endian + "I", data, off + 16)[0]
                count = struct.unpack_from(self.endian + "I", data, off + 20)[0]
                hdr_sz = 24
            else:
                old = struct.unpack_from(self.endian + "I", data, off + 8)[0]
                sdna = struct.unpack_from(self.endian + "I", data, off + 12)[0]
                count = struct.unpack_from(self.endian + "I", data, off + 16)[0]
                hdr_sz = 20
            payload = off + hdr_sz
            block = {"code": code, "size": size, "old": old, "sdna": sdna, "count": count, "off": payload}
            self.blocks.append(block)
            self.by_addr[old] = block
            off = payload + size
            if code == b"ENDB":
                break
        dna = next(b for b in self.blocks if b["code"] == b"DNA1")
        self._parse_dna(data[dna["off"] : dna["off"] + dna["size"]])

    def _u32(self, raw: bytes, i: int) -> tuple[int, int]:
        return struct.unpack_from(self.endian + "I", raw, i)[0], i + 4

    def _u16(self, raw: bytes, i: int) -> tuple[int, int]:
        return struct.unpack_from(self.endian + "H", raw, i)[0], i + 2

    def _parse_dna(self, raw: bytes) -> None:
        i = 4
        i += 4
        n_names, i = self._u32(raw, i)
        self.names = []
        for _ in range(n_names):
            end = raw.index(b"\x00", i)
            self.names.append(raw[i:end].decode("ascii"))
            i = end + 1
        i = align4(i)
        i += 4
        n_types, i = self._u32(raw, i)
        self.types = []
        for _ in range(n_types):
            end = raw.index(b"\x00", i)
            self.types.append(raw[i:end].decode("ascii"))
            i = end + 1
        i = align4(i)
        i += 4
        self.tlen = [self._u16(raw, i + 2 * k)[0] for k in range(n_types)]
        i = align4(i + 2 * n_types)
        i += 4
        n_structs, i = self._u32(raw, i)
        self.structs = []
        self.struct_by_type = {}
        for sidx in range(n_structs):
            tidx, i = self._u16(raw, i)
            nfields, i = self._u16(raw, i)
            fields = []
            for _ in range(nfields):
                ft, i = self._u16(raw, i)
                fn, i = self._u16(raw, i)
                fields.append((ft, fn))
            rec = {"type": tidx, "fields": fields, "index": sidx}
            self.structs.append(rec)
            self.struct_by_type[tidx] = rec

    def struct_name(self, sdna: int) -> str:
        return self.types[self.structs[sdna]["type"]]

    def field_layout(self, struct_name: str) -> list[tuple[str, str, int, int]]:
        rec = self.struct_by_type[self.types.index(struct_name)]
        out = []
        off = 0
        for ft, fn in rec["fields"]:
            name = self.names[fn]
            tname = self.types[ft]
            size = self._field_size(ft, name)
            align = self._align(ft, name)
            if align:
                off = (off + align - 1) & ~(align - 1)
            out.append((name, tname, off, size))
            off += size
        return out

    def _align(self, ft: int, name: str) -> int:
        if name.startswith("*") or name.startswith("(*"):
            return self.ptr
        tlen = self.tlen[ft]
        if tlen in (2, 4, 8):
            return tlen
        if tlen > 8:
            return 8 if self.ptr == 8 else 4
        return 1

    def _field_size(self, ft: int, name: str) -> int:
        n = name
        if n.startswith("(*"):
            return self.ptr
        ptr = 0
        while n.startswith("*"):
            ptr += 1
            n = n[1:]
        dims = 1
        while "[" in n:
            a = n.index("[")
            b = n.index("]")
            dims *= int(n[a + 1 : b])
            n = n[:a] + n[b + 1 :]
        base = self.ptr if ptr else self.tlen[ft]
        return base * dims

    def read_ptr(self, off: int) -> int:
        fmt = self.endian + ("Q" if self.ptr == 8 else "I")
        return struct.unpack_from(fmt, self.data, off)[0]

    def read_i32(self, off: int) -> int:
        return struct.unpack_from(self.endian + "i", self.data, off)[0]


def id_name(blend: Blend, block_off: int) -> str:
    for name, _t, off, size in blend.field_layout("ID"):
        if name.startswith("name["):
            raw = blend.data[block_off + off : block_off + off + size]
            return raw.split(b"\x00", 1)[0].decode("utf-8", "replace")
    return "?"


def mesh_faces(blend: Blend, template: str) -> tuple[int, list[list[int]]]:
    mesh_layout = {n: (t, o, s) for n, t, o, s in blend.field_layout("Mesh")}
    cd_fields = blend.field_layout("CustomData")
    layer_fields = blend.field_layout("CustomDataLayer")
    layer_sz = layer_fields[-1][2] + layer_fields[-1][3]
    layers_off = next(o for n, t, o, s in cd_fields if n == "*layers")
    totlayer_off = next(o for n, t, o, s in cd_fields if n == "totlayer")
    name_off = next(o for n, t, o, s in layer_fields if n.startswith("name["))
    data_off = next(o for n, t, o, s in layer_fields if n == "*data")

    for block in blend.blocks:
        if blend.struct_name(block["sdna"]) != "Mesh":
            continue
        name = id_name(blend, block["off"])
        if template not in name:
            continue
        totvert = blend.read_i32(block["off"] + mesh_layout["totvert"][1])
        totpoly = blend.read_i32(block["off"] + mesh_layout["totpoly"][1])
        totloop = blend.read_i32(block["off"] + mesh_layout["totloop"][1])
        poly_ptr = blend.read_ptr(block["off"] + mesh_layout["*poly_offset_indices"][1])
        poly_block = blend.by_addr[poly_ptr]
        offsets = struct.unpack_from(
            blend.endian + f"{totpoly + 1}i", blend.data, poly_block["off"]
        )
        ldata = block["off"] + mesh_layout["ldata"][1]
        layers_ptr = blend.read_ptr(ldata + layers_off)
        totlayer = blend.read_i32(ldata + totlayer_off)
        lb = blend.by_addr[layers_ptr]
        corner = None
        for i in range(totlayer):
            loff = lb["off"] + i * layer_sz
            raw = blend.data[loff + name_off : loff + name_off + 68]
            lname = raw.split(b"\x00", 1)[0].decode("ascii")
            if lname == ".corner_vert":
                corner = blend.read_ptr(loff + data_off)
                break
        if corner is None:
            raise RuntimeError("no .corner_vert")
        cb = blend.by_addr[corner]
        loops = struct.unpack_from(blend.endian + f"{totloop}i", blend.data, cb["off"])
        faces = [list(loops[offsets[i] : offsets[i + 1]]) for i in range(totpoly)]
        return totvert, faces
    raise FileNotFoundError(template)


def y_up(vert: list[float]) -> tuple[float, float, float]:
    x, y, z = vert
    return (x, z, -y)


def write_obj(path: Path, label: str, verts: list, faces: list[list[int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [HEADER.format(label=label)]
    for x, y, z in verts:
        xx, yy, zz = y_up([x, y, z])
        lines.append(f"v {xx:.5f} {yy:.5f} {zz:.5f}\n")
    for face in faces:
        idx = " ".join(str(i + 1) for i in face)
        lines.append(f"f {idx}\n")
    path.write_text("".join(lines))
    print(f"wrote {path} verts={len(verts)} faces={len(faces)}")


JOBS = [
    ("f_an01", "anime female F_AN01 shojo", "MBLab_anime_female", "f_an01_verts.json"),
    ("f_an02", "anime female F_AN02 shojo", "MBLab_anime_female", "f_an02_verts.json"),
    ("m_an01", "anime male M_AN01 shojo", "MBLab_anime_male", "m_an01_verts.json"),
]


def main() -> None:
    mblab = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/mblab/src")
    blend_path = mblab / "data" / "humanoid_library.blend"
    verts_dir = mblab / "data" / "vertices"
    blend = Blend(blend_path.read_bytes())
    face_cache: dict[str, tuple[int, list[list[int]]]] = {}
    for stem, label, template, verts_name in JOBS:
        if template not in face_cache:
            face_cache[template] = mesh_faces(blend, template)
        totvert, faces = face_cache[template]
        verts = json.loads((verts_dir / verts_name).read_text())
        if len(verts) != totvert:
            raise ValueError(f"{verts_name} {len(verts)} != template {totvert}")
        write_obj(OUT / f"{stem}.obj", label, verts, faces)


if __name__ == "__main__":
    main()
