"""Turn the downloaded general-image parquet files into small JPEGs used as the 'unknown_plant' class."""
import io
import random
from pathlib import Path

import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data/raw/negatives"
OUT = SRC / "img"
OUT.mkdir(exist_ok=True)
random.seed(1)
CAPS = {"caltech_train": 3500, "dtd_train": 2500, "dtd_test": 1000, "flowers_train": 1500}
for name, cap in CAPS.items():
    f = SRC / f"{name}.parquet"
    if not f.exists():
        print("missing", f); continue
    df = pd.read_parquet(f)
    col = next(c for c in df.columns if "image" in c.lower())
    idx = list(range(len(df))); random.shuffle(idx)
    n = 0
    for i in idx[:cap]:
        cell = df.iloc[i][col]
        raw = cell["bytes"] if isinstance(cell, dict) else cell
        try:
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            im.thumbnail((256, 256))
            im.save(OUT / f"{name}_{i}.jpg", quality=90)
            n += 1
        except Exception:
            pass
    print(name, len(df), "->", n)
