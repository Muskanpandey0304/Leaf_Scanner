"""How many of the photos scanned in the app (app/uploads) are (near-)duplicates of training/test images? (dHash hamming <= 6)"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
from PIL import Image, ImageOps
sys.path.insert(0, "scripts")
from build_dataset3 import dhash, popcount64
R = Path(".")
df = pd.read_csv(R / "data/processed3/manifest.csv")
def h(p):
    try: return dhash(ImageOps.exif_transpose(Image.open(p)).convert("RGB"))
    except Exception: return 0
if __name__ == "__main__":
    ups = sorted((R / "app/uploads").glob("*.jpg"))
    uh = np.array([h(p) for p in ups], dtype=np.uint64)
    mh = np.array([h(R / "data/processed3/images" / p) for p in df.path], dtype=np.uint64)
    seen = 0; rows = []
    for p, x in zip(ups, uh):
        d = popcount64(mh ^ x); j = int(d.argmin())
        if d[j] <= 6:
            seen += 1; rows.append((p.stem[-6:], int(d[j]), df.iloc[j].label, df.iloc[j].source, df.iloc[j].split))
    print(len(ups), "uploads;", seen, "have a near-duplicate in the dataset")
    for r in rows: print(r)
