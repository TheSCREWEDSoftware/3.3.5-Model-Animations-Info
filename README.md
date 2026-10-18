# Model Animation Checker

Which animations does a creature model really have in the 3.3.5a client, and what will a morphed player look like when some are missing?

Once morphed, the player's own race, gender and class make no difference: only the creature model counts.

Open **`Model Animation Checker.html`** in any browser. It works offline.

## Using the page

1. **Add models.** Type one of these in a row:
   - a display ID, e.g. `15374`
   - a creature name, e.g. `Hogger`
   - a creature entry, e.g. `npc 448`
   - part of a model file name, e.g. `owlbear`

   Press **+** for another row and **−** to remove one. The shapeshift buttons and the Examples list add models for you.
2. **Share or export.** "Copy my code" gives a share code holding your list; someone else pastes it and presses "Load code". "Download Excel" and "Download HTML page" export the whole list.

## Verdict

| Symbol | Meaning |
|---|---|
| ✓ | Works: has move, jump, fall, swim, strafe, attack, cast, death, sit and mounted animations |
| ⚠ | Works partly: some of those are missing (the Missing column says which) |
| ✗ | Does not work: no walk, run or swim animation, so it slides everywhere |

- "Has / missing" is read straight from each model file and is exact.
- "Plays instead" follows the fallback column of `AnimationData.dbc` and is a prediction of what the client shows.

## Files

| File | What it is |
|---|---|
| `Model Animation Checker.html` | The page (everything is embedded in this one file) |
| `reports/Examples.xlsx`, `reports/Examples.html` | The 174 example models, exported with the page's own buttons |
| `server/ModelAnimData.lua` | The same data as a Lua table for server scripts |
| `exported creature info.sql` | Your dump of `creature_template` + `creature_template_model` |
| `data/` | What the page is built from |
| `tools/` | The scripts that build it |

### `data/`

| File | Contents |
|---|---|
| `model_anims.json` | Every model's animation IDs, read from the client |
| `payload.json` | The compact version the page embeds |
| `examples.json` | Example models: name, display ID, category, icon |
| `creatures.json` | Creature entry, name, subname, display IDs |
| `icons.json`, `formicons.json` | The in-game icons shown next to examples and shapeshift forms |

### `tools/` (in the order they run)

| Script | Reads | Writes |
|---|---|---|
| `mpq.py` | Client archives (needs StormLib) | Used by the two extract scripts |
| `extract.py` | Client archives | `data/model_anims.json` |
| `build_payload.py` | `data/model_anims.json` | `data/payload.json`, `server/ModelAnimData.lua` |
| `parse_examples.py` | Costume / class-perk SQL | `data/examples.json` |
| `extract_icons.py` | Client archives (needs Pillow) | `data/icons.json`, `data/formicons.json` |
| `parse_creatures.py` | Creature SQL dump | `data/creatures.json` |
| `make_page.py` | `data/` + `tools/template.html` | `Model Animation Checker.html` |

`template.html` is the page's layout and code, without the data.

## Lua table

```lua
local MA = require("ModelAnimData")
MA.Has(displayId, MA.JUMP)   -- true when that model has a complete jump
MA.Works(displayId)          -- true when nothing a player needs is missing
```

## Rebuilding

After changing `template.html`, or any file in `data/`:

```
python tools/make_page.py data tools/template.html "Model Animation Checker.html"
```

After a new creature export (then run `make_page.py`):

```
python tools/parse_creatures.py "exported creature info.sql" data/creatures.json
```

After adding custom models to the client, run `extract.py` and `build_payload.py` again, then `make_page.py`. Each script explains its arguments at the top.

## Notes

- The custom client patches present when this was built (`patch-W`, `patch-Z`, `patch-enGB-M/N/y`) do not replace any creature model or the DBCs used, so the results match a stock 3.3.5a client.
- A ✓ only says the animations exist. Some models are invisible in game, for example the "invisible stalker" used by many trigger creatures.
