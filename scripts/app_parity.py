"""Parity check between the Dart (phone) preprocessing and the Python/PIL pipeline.
  step 1: python scripts/app_parity.py make    -> writes mobile_app/test/fixtures/list.txt
  step 2: (cd mobile_app && flutter test test/preprocess_test.dart)   -> Dart writes out_<i>.bin
  step 3: python scripts/app_parity.py check   -> compares ONNX predictions on both tensors
"""
import glob
import json
import os
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "mobile_app" / "test" / "fixtures"


def make():
    random.seed(2)
    big = []
    for pat in ("data/plantdoc_clean/test/*/*.*", "data/raw/plantwild/extracted/plantwild/images/*/*.*"):
        fs = glob.glob(str(ROOT / pat))
        random.shuffle(fs)
        k = 0
        for f in fs:
            try:
                w, h = Image.open(f).size
            except Exception:
                continue
            if max(w, h) > 700:
                big.append(f.replace("\\", "/"))
                k += 1
            if k >= 20:
                break
    thumbs = [p for p in glob.glob(str(ROOT / "data/processed/images/plantdoc_*.jpg"))[:10]]
    paths = big + [t.replace("\\", "/") for t in thumbs]
    FIX.mkdir(parents=True, exist_ok=True)
    for f in FIX.glob("out_*.bin"):
        f.unlink()
    (FIX / "list.txt").write_text("\n".join(paths))
    print(len(paths), "images;", "sizes of first 5 big:", [Image.open(p).size for p in big[:5]])


def check():
    import onnxruntime as ort
    from torchvision import transforms as T
    temp = json.load(open(ROOT / "mobile_app/assets/config.json"))["temperature"]
    sess = ort.InferenceSession(str(ROOT / "mobile_app/assets/model.onnx"), providers=["CPUExecutionProvider"])
    tf = T.Compose([T.Resize(256), T.CenterCrop(224), T.ToTensor(),
                    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    paths = (FIX / "list.txt").read_text().split("\n")

    def probs(x):
        l = sess.run(None, {"input": x[None].astype(np.float32)})[0][0]
        e = np.exp((l - l.max()) / temp)
        return e / e.sum()
    s1 = s3 = 0
    maxp, mad = 0.0, []
    for i, p in enumerate(paths):
        ref = tf(Image.open(p).convert("RGB")).numpy()
        dart = np.fromfile(FIX / f"out_{i}.bin", dtype=np.float32).reshape(3, 224, 224)
        mad.append(np.abs(ref - dart).mean())
        a, b = probs(ref), probs(dart)
        s1 += a.argmax() == b.argmax()
        s3 += set(np.argsort(-a)[:3]) == set(np.argsort(-b)[:3])
        maxp = max(maxp, np.abs(a - b).max())
    n = len(paths)
    print(f"mean |tensor diff| {np.mean(mad):.4f} (max {np.max(mad):.4f})")
    print(f"same top-1: {s1}/{n}   same top-3 set: {s3}/{n}   max prob diff: {maxp:.3f}")


if __name__ == "__main__":
    {"make": make, "check": check}[sys.argv[1]]()
