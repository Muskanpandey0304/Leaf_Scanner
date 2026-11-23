"""Fine-tune EfficientNet-B0 on the processed manifest, then evaluate on field test sets.

Run: .venv\\Scripts\\python.exe scripts\\train.py [--epochs 12] [--samples 30000]
Outputs in models/: best.pt, classes.json, report.json
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import models, transforms as T

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
import sys as _s
OUT = ROOT / "models"
MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]


class DS(Dataset):
    def __init__(self, df, cls2i, tf, root=None):
        self.root = Path(root) if root else PROC
        self.p = df["path"].tolist()
        self.y = [cls2i[l] for l in df["label"]]
        self.tf = tf

    def __len__(self):
        return len(self.p)

    def __getitem__(self, i):
        img = Image.open(self.root / "images" / self.p[i]).convert("RGB")
        return self.tf(img), self.y[i]


def make_tf(train):
    if train:
        return T.Compose([
            T.RandomResizedCrop(224, scale=(0.4, 1.0)),
            T.RandomHorizontalFlip(), T.RandomVerticalFlip(),
            T.RandomApply([T.RandomRotation(30)], p=0.5),
            T.ColorJitter(0.4, 0.4, 0.4, 0.05),
            T.RandomApply([T.GaussianBlur(5, (0.1, 2.0))], p=0.3),
            T.ToTensor(), T.Normalize(MEAN, STD),
            T.RandomErasing(p=0.25),
        ])
    return T.Compose([T.Resize(256), T.CenterCrop(224), T.ToTensor(), T.Normalize(MEAN, STD)])


@torch.no_grad()
def logits_of(model, loader, dev):
    model.eval()
    outs, ys = [], []
    for x, y in loader:
        with torch.autocast("cuda", enabled=dev == "cuda"):
            o = model(x.to(dev, non_blocking=True))
        outs.append(o.float().cpu())
        ys.append(y)
    return torch.cat(outs), torch.cat(ys)


def fit_temperature(logits, y):
    t = nn.Parameter(torch.ones(1))
    opt = torch.optim.LBFGS([t], lr=0.1, max_iter=100)

    def closure():
        opt.zero_grad()
        loss = F.cross_entropy(logits / t, y)
        loss.backward()
        return loss
    opt.step(closure)
    return float(t.detach())


def risk_coverage(probs, y, thresholds=(0.5, 0.7, 0.8, 0.9, 0.95)):
    conf, pred = probs.max(1)
    rows = []
    for th in thresholds:
        keep = conf >= th
        cov = keep.float().mean().item()
        acc = (pred[keep] == y[keep]).float().mean().item() if keep.any() else float("nan")
        rows.append({"threshold": th, "coverage": round(cov, 3), "accuracy_on_answered": round(acc, 4)})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--samples", type=int, default=30000, help="samples per epoch")
    ap.add_argument("--bs", type=int, default=48)
    ap.add_argument("--lr", type=float, default=6e-4)
    ap.add_argument("--field_weight", type=float, default=4.0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default="models")
    ap.add_argument("--data", default="data/processed")
    ap.add_argument("--balance", type=float, default=0.0, help="class-balance exponent (0.5 = 1/sqrt(count))")
    a = ap.parse_args()

    global OUT
    OUT = ROOT / a.out
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    print("device", dev, torch.cuda.get_device_name(0) if dev == "cuda" else "")
    data_root = ROOT / a.data
    df = pd.read_csv(data_root / "manifest.csv")
    classes = sorted(df["label"].unique())
    cls2i = {c: i for i, c in enumerate(classes)}
    OUT.mkdir(exist_ok=True)
    (OUT / "classes.json").write_text(json.dumps(classes, indent=1))

    tr = df[df.split == "train"].reset_index(drop=True)
    w = np.where(tr.source == "plantvillage", 1.0, a.field_weight)
    if a.balance > 0:
        cnt = tr["label"].map(tr["label"].value_counts()).values.astype(float)
        w = w / cnt ** a.balance
    sampler = WeightedRandomSampler(w, num_samples=a.samples, replacement=True)
    kw = dict(num_workers=a.workers, pin_memory=dev == "cuda", persistent_workers=a.workers > 0)
    tl = DataLoader(DS(tr, cls2i, make_tf(True), data_root), batch_size=a.bs, sampler=sampler, drop_last=True, **kw)
    mk = lambda s: DataLoader(DS(df[df.split == s].reset_index(drop=True), cls2i, make_tf(False), data_root),
                              batch_size=96, shuffle=False, **kw)
    vl, tpw, tpd = mk("val"), mk("test_plantwild"), mk("test_plantdoc")

    model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(classes))
    model.to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=1e-2)
    steps = a.epochs * len(tl)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=a.lr, total_steps=steps, pct_start=0.15)
    scaler = torch.amp.GradScaler(enabled=dev == "cuda")
    best = 0.0
    for ep in range(a.epochs):
        model.train()
        t0, tot, n = time.time(), 0.0, 0
        for x, y in tl:
            x, y = x.to(dev, non_blocking=True), y.to(dev, non_blocking=True)
            with torch.autocast("cuda", enabled=dev == "cuda"):
                loss = F.cross_entropy(model(x), y, label_smoothing=0.1)
            opt.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
            sched.step()
            tot += loss.item() * len(y)
            n += len(y)
        lg, yy = logits_of(model, vl, dev)
        vacc = (lg.argmax(1) == yy).float().mean().item()
        print(f"ep {ep + 1}/{a.epochs} loss {tot / n:.3f} val_acc {vacc:.4f} ({time.time() - t0:.0f}s)", flush=True)
        if vacc > best:
            best = vacc
            torch.save(model.state_dict(), OUT / "best.pt")

    model.load_state_dict(torch.load(OUT / "best.pt"))
    vlg, vy = logits_of(model, vl, dev)
    temp = fit_temperature(vlg, vy)
    report = {"best_val_acc": best, "temperature": temp, "classes": len(classes)}
    for name, ld in (("test_plantwild", tpw), ("test_plantdoc", tpd)):
        lg, yy = logits_of(model, ld, dev)
        pr = F.softmax(lg / temp, 1)
        acc = (pr.argmax(1) == yy).float().mean().item()
        per = {}
        for i, c in enumerate(classes):
            m = yy == i
            if m.any():
                per[c] = {"n": int(m.sum()), "acc": round((pr.argmax(1)[m] == i).float().mean().item(), 3)}
        report[name] = {"n": len(yy), "acc": round(acc, 4), "risk_coverage": risk_coverage(pr, yy), "per_class": per}
        print(name, "acc", round(acc, 4), "n", len(yy))
        for r in report[name]["risk_coverage"]:
            print("  ", r)
    (OUT / "report.json").write_text(json.dumps(report, indent=1))
    print("saved models/report.json")


if __name__ == "__main__":
    main()
