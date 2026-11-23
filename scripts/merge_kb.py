"""Merge knowledge.json + knowledge_extra.json + knowledge_run4.json and tag each class with its reliability tier -> app/knowledge_all.json
Tiers come from data/processed3/tiers.json, refined by measured accuracy (data/processed3/tiers_final.json, written by assign_tiers.py) if present."""
import json
from pathlib import Path
R = Path(__file__).resolve().parent.parent
load = lambda p: json.load(open(R / p, encoding="utf-8"))
kb = {**load("app/knowledge.json"), **load("app/knowledge_extra.json"), **load("app/knowledge_run4.json")}
tp = R / "data/processed3/tiers_final.json"
if not tp.exists():
    tp = R / "data/processed3/tiers.json"
tiers = json.load(open(tp))
print("tiers from", tp.name)
for k, v in kb.items():
    if not k.startswith("_") and v.get("kind") not in ("unknown", "unnamed_disease"):
        v["tier"] = tiers.get(k, "B")
json.dump(kb, open(R / "app/knowledge_all.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(kb) - 1, "entries written")
