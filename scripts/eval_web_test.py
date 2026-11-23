"""Score the model on the independent web test set (data/test_web). Photos that are near-duplicates of any
training/validation/test image are removed first, so every scored photo is truly new.
Usage: eval_web_test.py models_run4 [models_run3]"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image, ImageOps
from torchvision import models, transforms as T

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_dataset3 import dhash, popcount64  # noqa: E402

R = Path(__file__).resolve().parent.parent
CACHE = R / "data" / "processed3" / "hashes.npy"
tf = T.Compose([T.Resize(256), T.CenterCrop(224), T.ToTensor(), T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])


def h(p):
    try:
        return dhash(ImageOps.exif_transpose(Image.open(p)).convert("RGB"))
    except Exception:  # noqa: BLE001
        return 0


def dataset_hashes():
    if CACHE.exists():
        return np.load(CACHE)
    df = pd.read_csv(R / "data/processed3/manifest.csv")
    with Pool(8) as pool:
        hs = pool.map(h, [R / "data/processed3/images" / p for p in df.path], chunksize=512)
    arr = np.array(hs, dtype=np.uint64)
    np.save(CACHE, arr)
    return arr


def load(d):
    classes = json.loads((R / d / "classes.json").read_text())
    temp = json.loads((R / d / "report.json").read_text())["temperature"]
    m = models.efficientnet_b0()
    m.classifier[1] = nn.Linear(m.classifier[1].in_features, len(classes))
    m.load_state_dict(torch.load(R / d / "best.pt", map_location="cpu"))
    return m.eval().to("cuda"), classes, temp


def predict(b, path):
    m, classes, temp = b
    x = tf(Image.open(path).convert("RGB")).unsqueeze(0).to("cuda")
    with torch.no_grad():
        p = F.softmax(((m(x) + m(torch.flip(x, dims=[3]))) / 2) / temp, 1)[0].cpu()
    c, i = p.max(0)
    return classes[int(i)], float(c)


def band(p):
    return "high" if p >= 0.8 else ("medium" if p >= 0.5 else "low")


def main():
    man = pd.read_csv(R / "data/test_web/manifest.csv")
    mh = dataset_hashes()
    keep = []
    for r in man.itertuples():
        x = np.uint64(h(R / "data/test_web" / r.file))
        near = (popcount64(mh ^ x) <= 6).any()
        keep.append(not near)
    print(len(man), "photos downloaded;", int((~np.array(keep)).sum()), "removed as near-copies of training/test images")
    man = man[keep].reset_index(drop=True)
    for d in sys.argv[1:]:
        b = load(d)
        rows = []
        for r in man.itertuples():
            top, c = predict(b, R / "data/test_web" / r.file)
            sup = not r.label.startswith("unsupported:")
            ok = (top == r.label) if sup else (top == "unknown_plant")
            plant_ok = (top.split("__")[0] == r.label.split("__")[0]) if sup else (top == "unknown_plant")
            rows.append((r.file, r.label, top, round(c, 2), band(c), ok, plant_ok, sup))
        df = pd.DataFrame(rows, columns=["file", "label", "top", "conf", "band", "ok", "plant_ok", "supported"])
        df.to_csv(R / f"scripts/web_test_{Path(d).name}.csv", index=False)
        s = df[df.supported]
        print(f"\n== {d}: {len(df)} photos")
        print(f"supported plants ({len(s)}): exact answer right {s.ok.mean():.0%}  | plant right {s.plant_ok.mean():.0%}")
        for bnd in ("high", "medium", "low"):
            t = s[s.band == bnd]
            if len(t):
                print(f"   {bnd:6s} confidence: {len(t):3d} photos, exact right {t.ok.mean():.0%}")
        u = df[~df.supported]
        if len(u):
            print(f"unsupported plants ({len(u)}): correctly said 'not sure' {u.ok.mean():.0%}")


if __name__ == "__main__":
    main()
