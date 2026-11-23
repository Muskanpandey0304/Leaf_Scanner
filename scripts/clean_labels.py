"""Flag likely mislabeled / off-topic web images using out-of-fold predictions on DINOv2 features.
Field images (plantwild + plantdoc) are split into 5 folds; for each fold a linear head is trained on
PlantVillage + the other 4 folds and predicts the held-out fold. Writes data/processed/flags.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent.parent
df = pd.read_csv(ROOT / "data/processed/manifest.csv")
X = torch.tensor(np.load(ROOT / "features_vits14.npz")["X"]).cuda()
classes = sorted(df.label.unique())
c2i = {c: i for i, c in enumerate(classes)}
y = torch.tensor([c2i[l] for l in df.label]).cuda()
field = (df.source != "plantvillage").values
pv_idx = np.nonzero(~field)[0]
f_idx = np.nonzero(field)[0]
rng = np.random.RandomState(0)
fold = rng.randint(0, 5, len(f_idx))
oof = torch.zeros(len(df), len(classes))


def fit(idx):
    cnt = torch.bincount(y[idx], minlength=len(classes)).float()
    w = 1.0 / cnt[y[idx]]
    w = w / w.mean()
    head = torch.nn.Linear(X.shape[1], len(classes)).cuda()
    opt = torch.optim.AdamW(head.parameters(), lr=2e-3, weight_decay=1e-3)
    idx_t = torch.tensor(idx).cuda()
    for ep in range(25):
        perm = torch.randperm(len(idx_t), device="cuda")
        for i in range(0, len(perm), 512):
            b = perm[i:i + 512]
            loss = (F.cross_entropy(head(X[idx_t[b]] * 8), y[idx_t[b]], reduction="none") * w[b]).mean()
            opt.zero_grad(); loss.backward(); opt.step()
    return head


for k in range(5):
    tr = np.concatenate([pv_idx, f_idx[fold != k]])
    te = f_idx[fold == k]
    head = fit(tr)
    with torch.no_grad():
        oof[te] = F.softmax(head(X[te] * 8), 1).cpu()
    print("fold", k, "done", flush=True)

p = oof[f_idx]
conf, pred = p.max(1)
lab = y[f_idx].cpu()
p_label = p[torch.arange(len(f_idx)), lab]
out = df.iloc[f_idx][["path", "label", "source", "split"]].copy()
out["oof_pred"] = [classes[i] for i in pred.tolist()]
out["oof_conf"] = conf.numpy()
out["p_label"] = p_label.numpy()
out["suspect"] = ((pred != lab) & (conf > 0.8) & (p_label < 0.1)).numpy()
out.to_csv(ROOT / "data/processed/flags.csv", index=False)
print(out.groupby("source").suspect.agg(["sum", "count", "mean"]))
print(out[out.suspect].groupby("label").size().sort_values(ascending=False).head(12))
