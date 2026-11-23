"""Build the training dataset (v2: ALL plants + real negatives for the unknown class).

Outputs data/processed2/images/<id>.jpg, manifest.csv (path,label,source,split) and tiers.json.
split: train / val / test_plantwild / test_plantdoc.   Run: .venv\\Scripts\\python.exe -I scripts\\build_dataset.py
"""
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from label_map import PLANTDOC, PLANTVILLAGE, ROOT, plantwild_label  # noqa: E402

OUT = ROOT / "processed2"
OUT = ROOT / "processed2"
IMG_OUT = OUT / "images"
MAXSIDE = 256
UNKNOWN = "unknown_plant"
MIN_IMAGES = 40  # a class needs at least this many (after dedupe) to be kept
random.seed(0)


def gather():
    items = []  # (src_path, canonical_or_None, source, orig_split)
    pd_root = ROOT / "plantdoc_clean"
    for split in ("train", "test"):
        for d in (pd_root / split).iterdir():
            if d.is_dir() and d.name in PLANTDOC and PLANTDOC[d.name]:
                for f in d.iterdir():
                    items.append((f, PLANTDOC[d.name], "plantdoc", split))
    pw_root = ROOT / "raw" / "plantwild" / "extracted" / "plantwild" / "images"
    for d in pw_root.iterdir():
        lab = plantwild_label(d.name)
        for f in d.iterdir():
            items.append((f, lab, "plantwild", "any"))
    pv_root = ROOT / "raw" / "plantvillage" / "extracted" / "raw" / "color"
    for d in pv_root.iterdir():
        if d.name in PLANTVILLAGE and PLANTVILLAGE[d.name]:
            for f in d.iterdir():
                items.append((f, PLANTVILLAGE[d.name], "plantvillage", "train"))
    neg = ROOT / "raw" / "negatives" / "img"
    if neg.exists():
        for f in neg.iterdir():
            items.append((f, UNKNOWN, "negative", "any"))
    return items


def dhash(img, n=8):
    g = img.convert("L").resize((n + 1, n), Image.BILINEAR)
    a = np.asarray(g, dtype=np.int16)
    bits = (a[:, 1:] > a[:, :-1]).flatten()
    return int(np.packbits(bits).view(">u8")[0])


def process(args):
    idx, src, source = args
    try:
        img = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        h = dhash(img)
        img.thumbnail((MAXSIDE, MAXSIDE), Image.BILINEAR)
        rel = f"{source}_{idx}.jpg"
        img.save(IMG_OUT / rel, quality=92)
        return idx, rel, h
    except Exception as e:  # corrupt image
        return idx, None, str(e)


class DSU:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def popcount64(x):
    x = x - ((x >> np.uint64(1)) & np.uint64(0x5555555555555555))
    x = (x & np.uint64(0x3333333333333333)) + ((x >> np.uint64(2)) & np.uint64(0x3333333333333333))
    x = (x + (x >> np.uint64(4))) & np.uint64(0x0F0F0F0F0F0F0F0F)
    return (x * np.uint64(0x0101010101010101)) >> np.uint64(56)


def main():
    IMG_OUT.mkdir(parents=True, exist_ok=True)
    items = gather()
    print("gathered", len(items), Counter(i[2] for i in items))
    with Pool() as p:
        res = p.map(process, [(i, s, src) for i, (s, _, src, _) in enumerate(items)], chunksize=64)
    ok = {}
    bad = 0
    for idx, rel, h in res:
        if rel is None:
            bad += 1
        else:
            ok[idx] = (rel, h)
    print("processed", len(ok), "corrupt", bad)

    # near-duplicate clusters among web-sourced images (plantwild + plantdoc)
    web = [i for i in ok if items[i][2] in ("plantwild", "plantdoc")]
    hs = np.array([ok[i][1] for i in web], dtype=np.uint64)
    dsu = DSU(len(web))
    for a in range(len(web)):
        d = popcount64(hs[a + 1:] ^ hs[a])
        for b in np.nonzero(d <= 3)[0]:
            dsu.union(a, a + 1 + int(b))
    comp = defaultdict(list)
    for k, i in enumerate(web):
        comp[dsu.find(k)].append(web[k])
    print("web images", len(web), "clusters", len(comp), "dup images removed", len(web) - len(comp))

    # one representative per cluster; clusters touching PlantDoc test go to test_plantdoc
    kept = []  # (idx, label, source, forced_split or None)
    comp_list = list(comp.values())
    random.shuffle(comp_list)
    for members in comp_list:
        pd_test = [m for m in members if items[m][2] == "plantdoc" and items[m][3] == "test"]
        if pd_test:
            kept.append((pd_test[0], items[pd_test[0]][1], "plantdoc", "test_plantdoc"))
        else:
            r = members[0]
            kept.append((r, items[r][1], items[r][2], "plantdoc_train" if items[r][2] == "plantdoc" else None))
    for i in ok:
        if items[i][2] in ("plantvillage", "negative"):
            kept.append((i, items[i][1], items[i][2], "train" if items[i][2] == "plantvillage" else None))

    # keep classes with enough images
    cnt = Counter(l for _, l, _, _ in kept)
    keep_classes = {c for c, n in cnt.items() if n >= MIN_IMAGES}
    dropped = sorted((c, n) for c, n in cnt.items() if c not in keep_classes)
    print("classes kept", len(keep_classes), "dropped (too few images)", dropped)

    rows = []
    for idx, lab, src, forced in kept:
        if lab not in keep_classes:
            continue
        path = ok[idx][0]
        if forced == "train" or forced == "plantdoc_train":
            split = "train"
        elif forced == "test_plantdoc":
            split = "test_plantdoc"
        else:  # plantwild or negative: 70/15/15
            r = random.random()
            split = "train" if r < 0.7 else ("val" if r < 0.85 else "test_plantwild")
        rows.append((path, lab, src, split))

    # tiers: A = seen in >= 2 independent datasets (so it can be tested on other photos); B = single source
    seen = defaultdict(set)
    for _, lab, src, _ in rows:
        if src != "negative":
            seen[lab].add(src)
    tiers = {c: ("A" if len(seen[c]) >= 2 else "B") for c in sorted(keep_classes) if c != UNKNOWN}
    json.dump(tiers, open(OUT / "tiers.json", "w"), indent=1)

    with open(OUT / "manifest.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["path", "label", "source", "split"])
        w.writerows(rows)

    print("total rows", len(rows), Counter(r[3] for r in rows))
    print("tier A", sum(v == "A" for v in tiers.values()), "tier B", sum(v == "B" for v in tiers.values()))
    tbl = defaultdict(Counter)
    for _, lab, _, sp in rows:
        tbl[lab][sp] += 1
    print(f"\n{'class':44s} tier train   val  t_pw  t_pd")
    for lab in sorted(tbl):
        c = tbl[lab]
        print(f"{lab:44s} {tiers.get(lab, '-'):>4s} {c['train']:5d} {c['val']:5d} {c['test_plantwild']:5d} {c['test_plantdoc']:5d}")


if __name__ == "__main__":
    main()
