#!/usr/bin/env python3
"""Reads the costume and class-perk rows of a Smartstone-style module's SQL and writes data/examples.json.
Only what the page shows is kept: the name, the display ID, the category and the icon.

    python3 parse_examples.py <folder with 3_smartstone_costumes.sql and 8_smartstone_perks.sql> <examples.json>

Output: [{"d": display id, "n": name, "g": category, "i": icon key}, ...]
"""
import json, os, re, sys

SQL, OUT = sys.argv[1:3]
STRING = r"'((?:[^'\\]|\\.|'')*)'"
ICON = r"\|TInterface[/\\]icons[/\\]([^:|]+)"


def icon_key(name):
    """icon file name -> the key used in icons.json and as a CSS class"""
    return "x" + re.sub(r"[^a-z0-9_]", "_", name.lower()) if name else ""


def read(name):
    return open(os.path.join(SQL, name), encoding="utf-8", errors="replace").read()


examples = []

# costumes: (@costumeID_start+N, DisplayId, Scale, @costumeCat_<x>, SubscriptionLevel, Duration, "Description", Enabled)
sql = read("3_smartstone_costumes.sql")
category_name = {"uncommon": "Uncommon costumes", "rare": "Rare costumes", "legendary": "Legendary costumes", "epic": "Epic costumes", "tiers": "Tier costumes"}
category_icon = {m[1]: m[2] for m in re.finditer(r"\(@costumeCat_(\w+),\s*\d+,\s*'" + ICON, sql, re.I)}
for m in re.finditer(r"\(@costumeID_start\s*\+\s*\d+,\s*(\d+),\s*[\d.]+,\s*@costumeCat_(\w+),\s*[^,]+,\s*[^,]+,\s*(?:\"([^\"]*)\"|" + STRING + r"),\s*\d\s*\)", sql):
    examples.append({"d": int(m[1]), "n": (m[3] or m[4]).replace("''", "'").strip(),
                     "g": category_name.get(m[2], m[2]), "i": icon_key(category_icon.get(m[2], ""))})
costumes = len(examples)

# class perks: (Id, 'Title', 'Description', ClassId, Category, Effect, Value = display id, Scale, SubscriptionLevel, Enabled)
sql = read("8_smartstone_perks.sql")
for m in re.finditer(r"\(\d+,\s*" + STRING + r",\s*" + STRING + r",\s*\d+,\s*\d+,\s*\d+,\s*(\d+),\s*[\d.]+,\s*\d+,\s*\d+\s*\)", sql):
    icon = re.search(ICON, m[1], re.I)
    title = re.sub(r"\|T[^|]*\|t", "", m[1]).replace("''", "'").replace("\\'", "'").strip()
    examples.append({"d": int(m[3]), "n": title,
                     "g": "Class perks: " + (title.split(":")[0].strip() if ":" in title else "other"),
                     "i": icon_key(icon[1] if icon else "")})

json.dump(examples, open(OUT, "w"))
print("wrote", OUT, "-", costumes, "costumes,", len(examples) - costumes, "class perks")
