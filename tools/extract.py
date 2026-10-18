#!/usr/bin/env python3
"""Step 1. Reads the client archives and writes data/model_anims.json:
every creature/player model's animation list, plus the DBC tables needed to look models up.

    python3 extract.py <client Data folder> <StormLib library> <out json>

Only the animation table inside each model file (M2) is read; nothing is extracted to disk.
"""
import json, os, struct, sys
from mpq import Client

DATA, LIB, OUT = sys.argv[1:4]
client = Client(DATA, LIB)


def dbc(name):
    """-> (rows as tuples of uint32, function turning a string offset into text)"""
    raw = client.read("DBFilesClient\\" + name)
    assert raw[:4] == b"WDBC", name
    rows, fields, row_size, _ = struct.unpack_from("<4I", raw, 4)
    strings = raw[20 + rows * row_size:]
    text = lambda o: strings[o:strings.find(b"\0", o)].decode("latin-1")
    return [struct.unpack_from("<%dI" % fields, raw, 20 + i * row_size) for i in range(rows)], text


def as_float(u):
    return struct.unpack("<f", struct.pack("<I", u))[0]


out = {"anims": {}, "modeldata": {}, "displays": {}, "races": {}, "forms": {}, "models": {}}

rows, s = dbc("AnimationData.dbc")           # ID, Name, WeaponFlags, BodyFlags, Flags, Fallback, ...
for r in rows:
    out["anims"][r[0]] = {"name": s(r[1]), "fallback": r[5]}
rows, s = dbc("CreatureModelData.dbc")       # ID, Flags, ModelPath, ...
for r in rows:
    out["modeldata"][r[0]] = s(r[2])
rows, s = dbc("CreatureDisplayInfo.dbc")     # ID, ModelID, SoundID, ExtraDisplayInfoID, Scale, ...
for r in rows:
    out["displays"][r[0]] = {"model": r[1], "scale": as_float(r[4])}
rows, s = dbc("ChrRaces.dbc")                # ID, ..., MaleDisplayID (4), FemaleDisplayID (5), ..., Name (14)
for r in rows:
    out["races"][r[0]] = {"male": r[4], "female": r[5], "name": s(r[14])}
rows, s = dbc("SpellShapeshiftForm.dbc")     # ID, ..., Name (2), ..., 4 display IDs, 8 spells
for r in rows:
    out["forms"][r[0]] = {"name": s(r[2]), "displays": [x for x in r[-12:-8] if x]}


def m2_path(p):
    base, ext = os.path.splitext(p)
    return base + ".m2" if ext.lower() in (".mdx", ".mdl", ".m2") else p


paths = sorted({m2_path(p) for p in out["modeldata"].values() if p}, key=str.lower)
for n, path in enumerate(paths):
    source, archive = client.find(path)
    rec = {"src": source}
    if archive is None:
        rec["error"] = "file not found in any archive"
    else:
        head = archive.read(path, 0, 0x24)
        if head[:4] != b"MD20":
            rec["error"] = "not an M2 file"
        else:
            # M2 header: magic, version, name (count, offset), flags, global sequences (count, offset), sequences (count, offset at 0x1C)
            version = struct.unpack_from("<I", head, 4)[0]
            count, offset = struct.unpack_from("<2I", head, 0x1C)
            size = 64 if version >= 264 else 68                    # one sequence record; it starts with the animation id (uint16)
            block = archive.read(path, offset, count * size) if count else b""
            rec["version"] = version
            rec["anims"] = sorted({struct.unpack_from("<H", block, k * size)[0] for k in range(len(block) // size)})
    out["models"][path.lower()] = rec
    if n % 250 == 0:
        print(n, "/", len(paths), path, flush=True)

json.dump(out, open(OUT, "w"))
print("wrote", OUT, "-", len(out["models"]), "models,", sum(1 for m in out["models"].values() if "error" in m), "not readable")
