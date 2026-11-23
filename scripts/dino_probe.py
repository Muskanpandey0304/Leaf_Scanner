"""Frozen DINOv2 features + linear head. Fast test of whether a stronger backbone fixes field accuracy.
Run: .venv\\Scripts\\python.exe -W ignore scripts\\dino_probe.py [vits14|vitb14]
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train import DS, PROC, ROOT, make_tf  # noqa: E402

NAME = sys.argv[1] if len(sys.argv) > 1 else "vits14"
TIMM = {"vits14": "vit_small_patch14_dinov2.lvd142m", "vitb14": "vit_base_patch14_dinov2.lvd142m"}
FEAT = ROOT / f"features_{NAME}.npz"


def extract(df, classes):
    dev = "cuda"
    import timm
    m = timm.create_model(TIMM[NAME], pretrained=True, num_classes=0, img_size=224).to(dev).half().eval()
    ld = DataLoader(DS(df, {c: i for i, c in enumerate(classes)}, make_tf(False)),
                    batch_size=64, num_workers=4)
    out = []
    t0 = time.time()
    with torch.no_grad():
        for k, (x, _) in enumerate(ld):
            f = m(x.to(dev).half())
            out.append(F.normalize(f.float(), dim=1).cpu())
            if k % 100 == 0:
                print(f"  {k * 64}/{len(df)} {time.time() - t0:.0f}s", flush=True)
    return torch.cat(out).numpy()


def analyse(name, probs, y, classes, unk):
    conf, pred = probs.max(1)
    tr = y != unk
    n = tr.sum().item()
    print(f"\n== {name}: top1 acc {(pred == y).float().mean():.3f}")
    for th in (0.0, 0.5, 0.7, 0.8, 0.9):
        ans = (pred != unk) & (conf >= th) & tr
        cor = (ans & (pred == y)).sum().item()
        wr = (ans & (pred != y)).sum().item()
        print(f" th={th:.1f}: correct {cor / n:5.1%} | declined {(n - cor - wr) / n:5.1%} | WRONG {wr / n:5.1%} | precision {cor / max(cor + wr, 1):5.1%}")


def main():
    df = pd.read_csv(PROC / "manifest.csv")
    classes = sorted(df["label"].unique())
    c2i = {c: i for i, c in enumerate(classes)}
    unk = c2i["unknown_plant"]
    if FEAT.exists():
        X = np.load(FEAT)["X"]
    else:
        X = extract(df, classes)
        np.savez(FEAT, X=X)
    y = torch.tensor([c2i[l] for l in df.label])
    X = torch.tensor(X)
    dev = "cuda"
    trm = (df.split == "train").values
    Xtr, ytr = X[trm].to(dev), y[trm].to(dev)
    src = df.source[trm].values
    # class-balanced weights x field-domain upweight
    cnt = torch.bincount(ytr, minlength=len(classes)).float()
    w = (1.0 / cnt[ytr]) * torch.tensor(np.where(src == "plantvillage", 1.0, 6.0), device=dev).float()
    w = w / w.mean()
    head = torch.nn.Linear(X.shape[1], len(classes)).to(dev)
    opt = torch.optim.AdamW(head.parameters(), lr=2e-3, weight_decay=1e-3)
    vm = (df.split == "val").values
    Xv, yv = X[vm].to(dev), y[vm].to(dev)
    best, state = 0, None
    for ep in range(60):
        perm = torch.randperm(len(Xtr), device=dev)
        for i in range(0, len(perm), 512):
            idx = perm[i:i + 512]
            loss = (F.cross_entropy(head(Xtr[idx] * 8), ytr[idx], reduction="none", label_smoothing=0.05) * w[idx]).mean()
            opt.zero_grad(); loss.backward(); opt.step()
        with torch.no_grad():
            acc = (head(Xv * 8).argmax(1) == yv).float().mean().item()
        if acc > best:
            best, state = acc, {k: v.clone() for k, v in head.state_dict().items()}
    head.load_state_dict(state)
    print("best val acc", round(best, 4))
    with torch.no_grad():
        for sp in ("test_plantwild", "test_plantdoc"):
            m = (df.split == sp).values
            p = F.softmax(head(X[m].to(dev) * 8), 1).cpu()
            analyse(sp, p, y[m], classes, unk)


if __name__ == "__main__":
    main()
