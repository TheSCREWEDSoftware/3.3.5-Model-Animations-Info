#!/usr/bin/env python3
"""Last step. Builds the single-file page from tools/template.html and the JSON files in data/.

    python3 make_page.py <data folder> <template.html> <out html>
"""
import json, os, sys

DATA, TEMPLATE, OUT = sys.argv[1:4]


def load(name, default=None):
    path = os.path.join(DATA, name)
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else default


payload = load("payload.json")
payload["examples"] = load("examples.json", [])
payload["formicons"] = load("formicons.json", {})
payload["creatures"] = load("creatures.json", [])

inline = lambda obj: json.dumps(obj, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
page = open(TEMPLATE, encoding="utf-8").read().replace("__PAYLOAD__", inline(payload)).replace("__ICONS__", inline(load("icons.json", {})))
open(OUT, "w", encoding="utf-8").write(page)
print("wrote", OUT, "-", len(page) // 1024, "KB")
