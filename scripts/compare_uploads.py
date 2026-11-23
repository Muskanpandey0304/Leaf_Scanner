"""Run two models on the photos scanned through the web app (app/uploads/*.jpg) and print the top-1 of each.
These photos were never used in training. Usage: compare_uploads.py models_run3 models_run4 [out.csv]"""
import csv
import json
import sys
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import models, transforms as T

R = Path(__file__).resolve().parent.parent
tf = T.Compose([T.Resize(256), T.CenterCrop(224), T.ToTensor(), T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])


def load(d):
    classes = json.loads((R / d / "classes.json").read_text())
    temp = json.loads((R / d / "report.json").read_text())["temperature"]
    m = models.efficientnet_b0()
    m.classifier[1] = nn.Linear(m.classifier[1].in_features, len(classes))
    m.load_state_dict(torch.load(R / d / "best.pt", map_location="cpu"))
    return m.eval(), classes, temp


def top1(bundle, x):
    m, classes, temp = bundle
    with torch.no_grad():
        p = F.softmax(((m(x) + m(torch.flip(x, dims=[3]))) / 2) / temp, 1)[0]
    c, i = p.max(0)
    return classes[int(i)], float(c)


def main():
    a, b = load(sys.argv[1]), load(sys.argv[2])
    rows = []
    for f in sorted((R / "app" / "uploads").glob("*.jpg")):
        x = tf(Image.open(f).convert("RGB")).unsqueeze(0)
        (c1, p1), (c2, p2) = top1(a, x), top1(b, x)
        rows.append([f.stem, c1, round(p1, 2), c2, round(p2, 2)])
    out = sys.argv[3] if len(sys.argv) > 3 else None
    if out:
        with open(out, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["scan", sys.argv[1], "conf", sys.argv[2], "conf"])
            w.writerows(rows)
    changed = [r for r in rows if r[1] != r[3]]
    print(len(rows), "photos;", len(changed), "answers changed")
    for r in changed:
        print(f"{r[0]}: {r[1]} ({r[2]})  ->  {r[3]} ({r[4]})")


if __name__ == "__main__":
    main()
