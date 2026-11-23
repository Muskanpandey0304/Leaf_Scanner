"""Export models_run2 to ONNX (batch 1, 224x224) and verify parity with PyTorch on real test images."""
import json
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort
import pandas as pd
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms as T

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "models_run2")
DATA = ROOT / (sys.argv[2] if len(sys.argv) > 2 else "data/processed")
DST = ROOT / "mobile_app" / "assets"
DST.mkdir(parents=True, exist_ok=True)

classes = json.loads((SRC / "classes.json").read_text())
m = models.efficientnet_b0()
m.classifier[1] = nn.Linear(m.classifier[1].in_features, len(classes))
m.load_state_dict(torch.load(SRC / "best.pt", map_location="cpu"))
m.eval()
dummy = torch.randn(1, 3, 224, 224)
out = DST / "model.onnx"
torch.onnx.export(m, dummy, str(out), input_names=["input"], output_names=["logits"], opset_version=17,
                  dynamo=False)
print("onnx size MB", round(out.stat().st_size / 1e6, 1))

sess = ort.InferenceSession(str(out), providers=["CPUExecutionProvider"])
tf = T.Compose([T.Resize(256), T.CenterCrop(224), T.ToTensor(),
                T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
df = pd.read_csv(DATA / "manifest.csv")
sub = df[df.split == "test_plantdoc"].sample(40, random_state=0)
maxdiff, agree = 0.0, 0
for p in sub.path:
    x = tf(Image.open(DATA / "images" / p).convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        a = m(x).numpy()
    b = sess.run(None, {"input": x.numpy()})[0]
    maxdiff = max(maxdiff, float(np.abs(a - b).max()))
    agree += int(a.argmax() == b.argmax())
print(f"max |logit diff| {maxdiff:.2e}; same top-1 on {agree}/{len(sub)}")
if maxdiff > 1e-3 or agree != len(sub):
    sys.exit("PARITY FAILED")
print("PARITY OK")
