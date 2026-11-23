"""Append strings from app/knowledge_run4.json that are not in i18n/strings_en.json; write i18n/new_en.txt (idx|text)."""
import json
from pathlib import Path
R = Path(__file__).resolve().parent.parent
en = json.loads((R / "i18n/strings_en.json").read_text(encoding="utf-8"))
kb = json.loads((R / "app/knowledge_run4.json").read_text(encoding="utf-8"))
new = []
def add(x):
    if x and x not in en and x not in new:
        new.append(x)
for v in kb.values():
    for f in ("title", "cause", "summary"):
        add(v.get(f))
    for f in ("signs", "actions", "prevention"):
        for x in v.get(f, []):
            add(x)
start = len(en)
en2 = en + new
(R / "i18n/strings_en.json").write_text(json.dumps(en2, ensure_ascii=False, indent=0), encoding="utf-8")
(R / "i18n/new_en.txt").write_text("\n".join(f"{start + i}|{s}" for i, s in enumerate(new)), encoding="utf-8")
print("old", start, "new", len(new), "total", len(en2))
