def sub(s, a, b):
    assert a in s, a[:70]
    return s.replace(a, b, 1)


# ---------------- server ----------------
p = 'app/server.py'
s = open(p, encoding='utf-8').read()
s = sub(s, 'KB = json.loads((Path(__file__).resolve().parent / "knowledge_all.json").read_text(encoding="utf-8"))',
        'HERE = Path(__file__).resolve().parent\nKB = json.loads((HERE / "knowledge_all.json").read_text(encoding="utf-8"))\n'
        'KBL = {"en": KB}\nfor _l in ("hi", "mr"):\n    KBL[_l] = json.loads((HERE / f"knowledge_{_l}.json").read_text(encoding="utf-8"))\n'
        'UI_JSON = (HERE / "ui.json").read_text(encoding="utf-8")')
s = sub(s, 'async def predict(file: UploadFile = File(...), crop: str = Form("")):',
        'async def predict(file: UploadFile = File(...), crop: str = Form(""), lang: str = Form("en")):\n    L = KBL.get(lang, KB)')
# localized lookups inside predict
s = sub(s, '        k = KB.get(c, {})\n', '        k = L.get(c, {})\n')
s = sub(s, '"crop": k.get("crop", ""), "kind"', '"crop": k.get("crop_local", k.get("crop", "")), "kind"')
s = sub(s, '    detail = dict(KB.get(first["id"], {}))\n', '    detail = dict(L.get(first["id"], {}))\n')
s = sub(s, 'lookalikes = [{"id": l, "title": KB[l]["title"]} for l in detail.get("lookalikes", []) if l in KB]',
        'lookalikes = [{"id": l, "title": L[l]["title"]} for l in detail.get("lookalikes", []) if l in L]')
s = sub(s, '"all_candidates_detail": {c["id"]: KB.get(c["id"], {}) for c in cands}',
        '"all_candidates_detail": {c["id"]: L.get(c["id"], {}) for c in cands}')
s = sub(s, '''@app.get("/crops")
def list_crops():
    crops = sorted({v.get("crop") for v in KB.values() if isinstance(v, dict) and v.get("crop")})
    return crops
''', '''@app.get("/ui.json")
def ui_json():
    from fastapi.responses import Response
    return Response(UI_JSON, media_type="application/json")


@app.get("/crops")
def list_crops(lang: str = "en"):
    L = KBL.get(lang, KB)
    names = {}
    for v in L.values():
        if isinstance(v, dict) and v.get("crop"):
            names[v["crop"]] = v.get("crop_local", v["crop"])
    return [{"id": k, "name": n} for k, n in sorted(names.items())]
''')
s = sub(s, 'def list_classes():\n    return [{"id": c, "title": KB.get(c, {}).get("title", c)} for c in classes if c != "unknown_plant"]',
        'def list_classes(lang: str = "en"):\n    L = KBL.get(lang, KB)\n    return [{"id": c, "title": L.get(c, {}).get("title", c)} for c in classes if c != "unknown_plant"]')
open(p, 'w', encoding='utf-8').write(s)
print('server patched')
