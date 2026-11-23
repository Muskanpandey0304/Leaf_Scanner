"""Local plant-leaf scanner. Phone opens http://<PC-IP>:8000 on the same Wi-Fi.
Run: .venv\\Scripts\\python.exe app\\server.py
"""
import csv
import io
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image, ImageOps
from torchvision import models, transforms as T

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "models_run4"
UPLOADS = Path(__file__).resolve().parent / "uploads"
UPLOADS.mkdir(exist_ok=True)
LOG = UPLOADS / "scans.csv"

classes = json.loads((MODEL_DIR / "classes.json").read_text())
HERE = Path(__file__).resolve().parent
KB = json.loads((HERE / "knowledge_all.json").read_text(encoding="utf-8"))
KBL = {"en": KB}
for _l in ("hi", "mr"):
    KBL[_l] = json.loads((HERE / f"knowledge_{_l}.json").read_text(encoding="utf-8"))
UI_JSON = (HERE / "ui.json").read_text(encoding="utf-8")
TEMP = json.loads((MODEL_DIR / "report.json").read_text())["temperature"]
dev = "cuda" if torch.cuda.is_available() else "cpu"

model = models.efficientnet_b0()
model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(classes))
model.load_state_dict(torch.load(MODEL_DIR / "best.pt", map_location=dev))
model.to(dev).eval()
tf = T.Compose([T.Resize(256), T.CenterCrop(224), T.ToTensor(),
                T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

app = FastAPI()


def band(p):
    return "high" if p >= 0.8 else ("medium" if p >= 0.5 else "low")


@app.get("/")
def index():
    return FileResponse(Path(__file__).resolve().parent / "index.html")


@app.post("/predict")
async def predict(file: UploadFile = File(...), crop: str = Form(""), lang: str = Form("en"), log: str = Form("1")):
    L = KBL.get(lang, KB)
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(await file.read()))).convert("RGB")
    x = tf(img).unsqueeze(0).to(dev)
    with torch.no_grad():
        # average of original + horizontal flip for a little stability
        logits = (model(x) + model(torch.flip(x, dims=[3]))) / 2
        if crop:
            # restrict to the chosen plant (+ the unknown class, so a mismatching leaf gets 'not sure')
            keep = torch.tensor([KB.get(c, {}).get("crop") == crop or c == "unknown_plant" for c in classes], device=logits.device)
            if keep.sum() > 1:
                logits = logits.masked_fill(~keep, -1e9)
        probs = F.softmax(logits / TEMP, 1)[0].cpu()
    top = probs.topk(3)
    cands = []
    for p, i in zip(top.values.tolist(), top.indices.tolist()):
        c = classes[i]
        k = L.get(c, {})
        cands.append({"id": c, "title": k.get("title", c), "crop": k.get("crop_local", k.get("crop", "")), "kind": k.get("kind", "disease"), "tier": k.get("tier", "A"),
                      "confidence": round(p, 3), "band": band(p)})
    first = cands[0]
    if first["kind"] == "unknown":
        status = "unrecognised"
    elif first["kind"] == "unnamed_disease":
        status = "unnamed"
    elif first["kind"] == "healthy":
        status = "healthy"
    else:
        status = "disease"
    detail = dict(L.get(first["id"], {}))
    if detail.get("kind") == "healthy":
        detail["nodisease"] = not any(isinstance(v, dict) and v.get("crop") == detail.get("crop") and v.get("kind") == "disease" for v in KB.values())
    lookalikes = [{"id": l, "title": L[l]["title"]} for l in detail.get("lookalikes", []) if l in L]
    scan_id = f"{int(time.time() * 1000)}"
    if log != "0":  # a language switch re-runs the same photo; do not log it twice
        img.thumbnail((640, 640))
        img.save(UPLOADS / f"{scan_id}.jpg", quality=88)
        with open(LOG, "a", newline="") as f:
            csv.writer(f).writerow([scan_id, first["id"], first["confidence"], cands[1]["id"], cands[2]["id"], "", ""])
    return JSONResponse({"scan_id": scan_id, "status": status, "top": cands, "detail": detail, "lookalikes": lookalikes,
                         "all_candidates_detail": {c["id"]: L.get(c["id"], {}) for c in cands}})


@app.post("/feedback")
async def feedback(scan_id: str = Form(...), correct: str = Form(...), true_label: str = Form("")):
    with open(UPLOADS / "feedback.csv", "a", newline="") as f:
        csv.writer(f).writerow([scan_id, correct, true_label])
    return {"ok": True}


@app.get("/ui.json")
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


@app.get("/classes")
def list_classes(lang: str = "en"):
    L = KBL.get(lang, KB)
    return [{"id": c, "title": L.get(c, {}).get("title", c)} for c in classes if c not in ("unknown_plant", "diseased_unnamed")]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
