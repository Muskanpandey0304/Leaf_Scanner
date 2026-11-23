import json
from pathlib import Path
R = Path(__file__).resolve().parent.parent
kb = json.loads((R / "app/knowledge_all.json").read_text(encoding="utf-8"))
by = {}
for k, v in kb.items():
    if not isinstance(v, dict) or v.get("kind") in ("unknown", "unnamed_disease"): continue
    by.setdefault(v.get("crop", "?"), []).append(v)
lines = ["Plants and conditions Leaf Scanner can recognise", "Tier A = tested accurately on held-out photos; B = weak or unproven in tests (double-check); C = studio photos only (weakly tested)", ""]
for crop in sorted(by):
    lines.append(crop)
    for v in sorted(by[crop], key=lambda x: x["title"]):
        lines.append(f"  - {v['title']} [{v.get('tier','?')}]")
    lines.append("")
(R / "list.txt").write_text("\n".join(lines), encoding="utf-8")
print(len(by), "plants,", sum(len(x) for x in by.values()), "entries")
