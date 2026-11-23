"""Compare run3 vs run4 on the PlantDoc test split (real field photos): which photos changed and why."""
import json, sys
from collections import Counter
from pathlib import Path
import pandas as pd, torch, torch.nn as nn, torch.nn.functional as F
from PIL import Image
from torchvision import models, transforms as T
R = Path(__file__).resolve().parent.parent
tf = T.Compose([T.Resize(256), T.CenterCrop(224), T.ToTensor(), T.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])])
dev = "cuda"
def load(d):
    cl = json.loads((R/d/"classes.json").read_text()); t = json.loads((R/d/"report.json").read_text())["temperature"]
    m = models.efficientnet_b0(); m.classifier[1] = nn.Linear(m.classifier[1].in_features, len(cl))
    m.load_state_dict(torch.load(R/d/"best.pt", map_location=dev)); return m.to(dev).eval(), cl, t
def pred(b, x):
    m, cl, t = b
    with torch.no_grad(): p = F.softmax(((m(x)+m(torch.flip(x,dims=[3])))/2)/t, 1)[0]
    c, i = p.max(0); return cl[int(i)], float(c)
a, b = load("models_run3"), load("models_run4")
df = pd.read_csv(R/"data/processed3/manifest.csv"); df = df[df.split == "test_plantdoc"]
rows = []
for r in df.itertuples():
    x = tf(Image.open(R/"data/processed3/images"/r.path).convert("RGB")).unsqueeze(0).to(dev)
    p3, c3 = pred(a, x); p4, c4 = pred(b, x); rows.append((r.label, p3, c3, p4, c4))
ok3 = sum(r[0]==r[1] for r in rows); ok4 = sum(r[0]==r[3] for r in rows)
print("run3", ok3, "run4", ok4, "of", len(rows))
lost = [r for r in rows if r[0]==r[1] and r[0]!=r[3]]; won = [r for r in rows if r[0]!=r[1] and r[0]==r[3]]
print("lost", len(lost), "won", len(won))
print("run4 wrong predictions that became:", Counter(r[3] for r in rows if r[0]!=r[3]).most_common(12))
print("LOST (true -> run4 pred):", Counter((r[0], r[3]) for r in lost).most_common(20))
print("WON:", Counter((r[0], r[1]) for r in won).most_common(10))
