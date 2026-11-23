"""Build localized knowledge files + UI strings for the app and web server."""
import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "i18n"))
from ui import UI, CROPS  # noqa: E402

en = json.loads((R / "i18n/strings_en.json").read_text(encoding="utf-8"))
kb = json.loads((R / "app/knowledge_all.json").read_text(encoding="utf-8"))
ASSETS = R / "mobile_app/assets"
missing = 0
for li, lang in ((0, "hi"), (1, "mr")):
    tr = {}
    for ln in (R / f"i18n/{lang}.txt").read_text(encoding="utf-8").splitlines():
        n, t = ln.split("|", 1)
        tr[int(n)] = t.strip()
    assert len(tr) == len(en), (len(tr), len(en))
    m = {e: tr[i] for i, e in enumerate(en)}
    out = {}
    for k, v in kb.items():
        if not isinstance(v, dict):
            out[k] = v
            continue
        d = dict(v)
        for f in ("title", "cause", "summary"):
            if v.get(f):
                d[f] = m[v[f]]
        for f in ("signs", "actions", "prevention"):
            if f in v:
                d[f] = [m[x] for x in v[f]]
        if v.get("crop"):
            if v["crop"] not in CROPS:
                missing += 1
                print("no crop name", v["crop"])
            d["crop_local"] = CROPS.get(v["crop"], [v["crop"]] * 2)[li]
        out[k] = d
    s = json.dumps(out, ensure_ascii=False)
    (R / f"app/knowledge_{lang}.json").write_text(s, encoding="utf-8")
    (ASSETS / f"knowledge_{lang}.json").write_text(s, encoding="utf-8")
ui = {k: {"en": v[0], "hi": v[1], "mr": v[2]} for k, v in UI.items()}
ui["_crops"] = {c: {"hi": h, "mr": mm} for c, (h, mm) in CROPS.items()}
s = json.dumps(ui, ensure_ascii=False)
(R / "app/ui.json").write_text(s, encoding="utf-8")
(ASSETS / "ui.json").write_text(s, encoding="utf-8")
(ASSETS / "knowledge.json").write_text((R / "app/knowledge_all.json").read_text(encoding="utf-8"), encoding="utf-8")
print("ok; missing crops:", missing)
