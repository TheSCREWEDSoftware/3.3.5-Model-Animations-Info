#!/usr/bin/env python3
"""Reads a HeidiSQL dump of creature_template + creature_template_model -> creatures.json
   [[entry, name, subname, [displayIds...]], ...]"""
import sys, json, re
SQL, OUT = sys.argv[1], sys.argv[2]
t = open(SQL, encoding="utf-8", errors="replace").read()
def rows(table):
    for m in re.finditer(r"INSERT INTO `%s` \(([^)]*)\) VALUES" % table, t):
        cols = [c.strip(" `") for c in m[1].split(",")]
        i = m.end(); n = len(t)
        while i < n:
            while i < n and t[i] in " \r\n\t,": i += 1
            if i >= n or t[i] != "(": break
            i += 1; row = []; cur = []; instr = False; quoted = False
            while True:
                c = t[i]
                if instr:
                    if c == "\\": cur.append(t[i + 1]); i += 2; continue
                    if c == "'":
                        if t[i + 1] == "'": cur.append("'"); i += 2; continue
                        instr = False; i += 1; continue
                    cur.append(c); i += 1; continue
                if c == "'": instr = True; quoted = True; cur = []; i += 1; continue
                if c == "," or c == ")":
                    v = "".join(cur); row.append(v if quoted else v.strip()); cur = []; quoted = False; i += 1
                    if c == ")": break
                    continue
                if not quoted: cur.append(c)
                i += 1
            yield dict(zip(cols, row))
            if i < n and t[i] == ";": break
cr = {}
for r in rows("creature_template"):
    cr[int(r["entry"])] = [int(r["entry"]), r["name"], "" if r["subname"] in ("NULL", "") else r["subname"], []]
nm = 0
for r in rows("creature_template_model"):
    e = int(r["CreatureID"]); d = int(r["CreatureDisplayID"])
    if e in cr and d and d not in cr[e][3]: cr[e][3].append(d); nm += 1
out = [v for k, v in sorted(cr.items()) if v[3]]
json.dump(out, open(OUT, "w"), ensure_ascii=False, separators=(",", ":"))
print(len(cr), "creatures,", nm, "model links,", len(out), "creatures with a display")
