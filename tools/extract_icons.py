#!/usr/bin/env python3
"""Pulls the in-game icons the page shows (the examples' icons and the stock shapeshift forms) out of the client.

    python3 extract_icons.py <client Data folder> <StormLib library> <data folder>

Reads <data>/examples.json; writes <data>/icons.json {icon key: PNG data URI} and <data>/formicons.json {display id: icon key}.
Needs Pillow (it can read BLP textures).
"""
import base64, io, json, sys
from PIL import Image
from mpq import Client

DATA, LIB, OUT = sys.argv[1:4]
SIZE = 36
# stock shapeshift display IDs -> icon file
FORM_ICONS = {892: "ability_druid_catform", 2281: "ability_racial_bearform", 918: "ability_druid_travelform", 2428: "ability_druid_aquaticform",
              15374: "spell_nature_forceofnature", 15375: "spell_nature_forceofnature", 864: "ability_druid_treeoflife",
              20857: "ability_druid_flightform", 21243: "ability_druid_flightform", 4613: "spell_nature_spiritwolf", 25277: "spell_shadow_demonform"}

client = Client(DATA, LIB)
wanted = {e["i"][1:] for e in json.load(open(OUT + "/examples.json")) if e["i"]} | set(FORM_ICONS.values())   # key "x<name>" -> file name
icons = {}
for name in sorted(wanted):
    raw = client.read("Interface\\Icons\\%s.blp" % name)
    if not raw:
        print("not in the client:", name)
        continue
    png = io.BytesIO()
    Image.open(io.BytesIO(raw)).convert("RGBA").resize((SIZE, SIZE), Image.LANCZOS).save(png, "PNG", optimize=True)
    icons["x" + name] = "data:image/png;base64," + base64.b64encode(png.getvalue()).decode()

json.dump(icons, open(OUT + "/icons.json", "w"))
json.dump({d: "x" + n for d, n in FORM_ICONS.items() if "x" + n in icons}, open(OUT + "/formicons.json", "w"))
print("wrote", len(icons), "of", len(wanted), "icons")
