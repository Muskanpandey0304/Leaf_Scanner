"""Top confusions + low-confidence-wrong examples for a trained run. Usage: confusion.py <models_dir>"""
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import models

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train import DS, PROC, ROOT, make_tf  # noqa: E402

def main():
    d = ROOT / sys.argv[1]
    classes = json.load(open(d / "classes.json"))
    c2i = {c: i for i, c in enumerate(classes)}
    m = models.efficientnet_b0()
    m.classifier[1] = nn.Linear(m.classifier[1].in_features, len(classes))
    m.load_state_dict(torch.load(d / "best.pt"))
    m.cuda().eval()
    df = pd.read_csv(PROC / "manifest.csv")
    rows = []
    for split in ("test_plantwild", "test_plantdoc"):
        sub = df[df.split == split].reset_index(drop=True)
        ld = DataLoader(DS(sub, c2i, make_tf(False)), batch_size=64, num_workers=2)
        preds, confs = [], []
        with torch.no_grad():
            for x, _ in ld:
                p = torch.softmax(m(x.cuda()), 1)
                c, i = p.max(1)
                preds += i.cpu().tolist(); confs += c.cpu().tolist()
        sub["pred"] = [classes[i] for i in preds]
        sub["conf"] = confs
        sub["split_name"] = split
        rows.append(sub)
        wrong = sub[sub.pred != sub.label]
        print(f"\n== {split}: {len(wrong)}/{len(sub)} wrong. Top confusions (true -> predicted):")
        for (t, p), n in Counter(zip(wrong.label, wrong.pred)).most_common(12):
            print(f"  {n:3d}  {t} -> {p}")
    pd.concat(rows).to_csv(d / "test_predictions.csv", index=False)


if __name__ == "__main__":
    main()
