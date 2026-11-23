"""Dataset v3 for run 4: processed2 + PlantSeg + banana sets + coffee sets + wheat healthy.

Outputs data/processed3/{images,manifest.csv,tiers.json,new_classes.json}. Existing images are hard-linked from
processed2 (no re-processing). New images: EXIF-fixed, <=256px, near-duplicates removed (also against the existing web
images), and split by CLUSTER (near-duplicate groups / same-plant groups) so the test split never holds a copy of a
training photo.  Run: .venv\\Scripts\\python.exe scripts\\build_dataset3.py
"""
import csv
import io
import json
import os
import random
import re
import shutil
import sys
import zipfile
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from label_map3 import (BANANA_7, BANANALSD, BRACOL_STRESS, GENERIC, WHEAT_HEALTHY, plantseg_label)  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent / "data"
OLD = ROOT / "processed2"
OUT = ROOT / os.environ.get("OUT_NAME", "processed3")
RAW = ROOT / "raw"
MAXSIDE = 256
MIN_NEW_CLASS = 30  # a NEW PlantSeg class needs this many images (after dedupe) or it is pooled into GENERIC
random.seed(0)

BANANA_RAW = {"Black and Yellow Sigatoka": "banana__sigatoka", "Healthy Banana  leaf": "banana__healthy",
              "Panama Wilt Disease": "banana__panama_disease"}  # fruit / insect folders deliberately skipped
_ZIPS = {}


def zf(path):
    if path not in _ZIPS:
        _ZIPS[path] = zipfile.ZipFile(path)
    return _ZIPS[path]


def gather():
    items = []  # dict(spec, label, source, group)

    def add(spec, label, source, group=None):
        if label:
            items.append({"spec": spec, "label": label, "source": source, "group": group})

    ps = RAW / "plantseg" / "plantseg.zip"
    if ps.exists() and not os.environ.get("SKIP_PLANTSEG"):
        z = zf(str(ps))
        meta = pd.read_csv(io.BytesIO(z.read("plantseg/Metadata.csv")), encoding="utf-8-sig")
        members = {Path(n).name: n for n in z.namelist() if "/images/" in n and n.lower().endswith((".jpg", ".jpeg", ".png"))}
        miss = 0
        for r in meta.itertuples():
            n = members.get(r.Name)
            if n is None:
                miss += 1
                continue
            add(("zip", str(ps), n), plantseg_label(r.Plant, r.Disease), "plantseg")
        print("plantseg rows", len(meta), "missing in zip", miss)
    else:
        print("!! plantseg.zip missing")

    # banana A: 79w2n6b4kf
    p = RAW / "banana" / "79w2n6b4kf.zip"
    if p.exists():
        for n in zf(str(p)).namelist():
            if n.endswith("/") or not n.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            add(("zip", str(p), n), BANANA_7.get(n.split("/")[-2]), "banana_a")
    # banana B: 5nfjzntwd8 (raw)
    p = RAW / "banana" / "5nfjzntwd8.zip"
    if p.exists():
        for n in zf(str(p)).namelist():
            if n.endswith("/") or not n.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            add(("zip", str(p), n), BANANA_RAW.get(n.split("/")[-2]), "banana_b")
    # BananaLSD folders
    d = RAW / "banana" / "bananalsd"
    if d.exists():
        for sub in d.iterdir():
            lab = BANANALSD.get(sub.name.split("__")[0])
            if lab and sub.is_dir():
                for f in sub.iterdir():
                    add(("file", str(f)), lab, "bananalsd")
    # BRACOL
    base = RAW / "coffee" / "bracol" / "ex" / "coffee-datasets" / "coffee-datasets" / "leaf"
    if (base / "dataset.csv").exists():
        df = pd.read_csv(base / "dataset.csv")
        for r in df.itertuples():
            f = base / "images" / f"{r.id}.jpg"
            if f.exists() and int(r.predominant_stress) in BRACOL_STRESS:
                add(("file", str(f)), BRACOL_STRESS[int(r.predominant_stress)], "bracol")
    # RoCoLe: labels live in the Labelbox export (External ID = file name, Label = JSON with "classification")
    roc = RAW / "coffee" / "rocole"
    lc = roc / "meta" / "RoCoLE-csv.csv"
    if lc.exists():
        df = pd.read_csv(lc)
        for r in df.itertuples(index=False):
            row = dict(zip(df.columns, r))
            f = roc / "img" / str(row["External ID"])
            try:
                cls = json.loads(row["Label"])["classification"]
            except Exception:  # noqa: BLE001
                continue
            lab = None
            if cls == "healthy":
                lab = "coffee__healthy"
            elif cls in ("rust_level_2", "rust_level_3", "rust_level_4"):  # level 1 is too faint to be a clean label
                lab = "coffee__leaf_rust"
            if lab and f.exists():
                m = re.match(r"(C\d+P\d+)", str(row["External ID"]))
                add(("file", str(f)), lab, "rocole", m.group(1) if m else None)
    # wheat healthy
    d = RAW / "wheat" / "healthy"
    if d.exists():
        for f in d.iterdir():
            add(("file", str(f)), WHEAT_HEALTHY, "wheat_bd")
    return items


def dhash(img, n=8):
    g = img.convert("L").resize((n + 1, n), Image.BILINEAR)
    a = np.asarray(g, dtype=np.int16)
    return int(np.packbits((a[:, 1:] > a[:, :-1]).flatten()).view(">u8")[0])


def process(args):
    idx, spec, tag = args
    try:
        data = zf(spec[1]).read(spec[2]) if spec[0] == "zip" else Path(spec[1]).read_bytes()
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
        h = dhash(img)
        img.thumbnail((MAXSIDE, MAXSIDE), Image.BILINEAR)
        name = f"{tag}_{idx}.jpg"
        img.save(OUT / "images" / name, quality=92)
        return idx, name, h
    except Exception as e:  # noqa: BLE001
        return idx, None, str(e)


def old_hash(path):
    try:
        return dhash(Image.open(OLD / "images" / path))
    except Exception:  # noqa: BLE001
        return None


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
    (OUT / "images").mkdir(parents=True, exist_ok=True)
    old = pd.read_csv(OLD / "manifest.csv")
    old_classes = set(old.label)

    # 1. hard-link existing images
    linked = 0
    for p in old.path:
        dst = OUT / "images" / p
        if not dst.exists():
            try:
                os.link(OLD / "images" / p, dst)
            except OSError:
                shutil.copy2(OLD / "images" / p, dst)
        linked += 1
    print("existing images linked", linked)

    items = gather()
    print("new items", len(items), Counter(i["source"] for i in items))
    with Pool() as pool:
        res = pool.map(process, [(i, it["spec"], it["source"]) for i, it in enumerate(items)], chunksize=32)
        web_old = old[old.source.isin(["plantwild", "plantdoc"])].path.tolist()
        oh = pool.map(old_hash, web_old, chunksize=256)
    ok = {i: (n, h) for i, n, h in res if n is not None}
    print("processed", len(ok), "failed", len(items) - len(ok))
    oh = np.array([h for h in oh if h is not None], dtype=np.uint64)

    # 2. drop new images that duplicate an existing web image (their split is already fixed), then cluster the rest
    idxs = sorted(ok)
    hs = np.array([ok[i][1] for i in idxs], dtype=np.uint64)
    keep = np.ones(len(idxs), bool)
    for k in range(len(idxs)):
        if len(oh) and (popcount64(oh ^ hs[k]) <= 3).any():
            keep[k] = False
    print("dropped as duplicates of existing web images:", int((~keep).sum()))
    idxs2 = [i for k, i in enumerate(idxs) if keep[k]]
    hs2 = np.array([ok[i][1] for i in idxs2], dtype=np.uint64)
    dsu = DSU(len(idxs2))
    first_of_group = {}
    for a in range(len(idxs2)):
        d = popcount64(hs2[a + 1:] ^ hs2[a])
        for b in np.nonzero(d <= 3)[0]:
            dsu.union(a, a + 1 + int(b))
        g = items[idxs2[a]]["group"]
        if g:
            key = (items[idxs2[a]]["source"], g)
            if key in first_of_group:
                dsu.union(a, first_of_group[key])
            else:
                first_of_group[key] = a
    comp = defaultdict(list)
    for a in range(len(idxs2)):
        comp[dsu.find(a)].append(idxs2[a])
    clusters = list(comp.values())
    random.shuffle(clusters)
    print("clusters", len(clusters))

    # 3. one image per exact-duplicate cluster for web sets is overkill for same-plant groups, so: keep ALL members of
    #    a cluster but give them the same split; drop only members whose hash is identical to an earlier member.
    rows_new = []
    for members in clusters:
        r = random.random()
        split = "train" if r < 0.7 else ("val" if r < 0.85 else "test_plantwild")
        seen_h = set()
        for m in members:
            n, h = ok[m]
            if h in seen_h:
                continue
            seen_h.add(h)
            rows_new.append([n, items[m]["label"], items[m]["source"], split])

    # 4. pool tiny NEW classes into the generic 'diseased_unnamed' class
    cnt = Counter(r[1] for r in rows_new)
    pooled = {}
    for r in rows_new:
        lab = r[1]
        if lab not in old_classes and cnt[lab] < MIN_NEW_CLASS and r[2] == "plantseg":
            pooled[lab] = cnt[lab]
            r[1] = GENERIC
    print("pooled into", GENERIC, pooled)

    allrows = [list(x) for x in old[["path", "label", "source", "split"]].itertuples(index=False)] + rows_new
    # a class with nothing in train would crash training: drop such classes entirely
    split_cnt = defaultdict(Counter)
    for p, l, s, sp in allrows:
        split_cnt[l][sp] += 1
    bad = {l for l, c in split_cnt.items() if c["train"] < 10}
    if bad:
        print("dropping classes with <10 train images:", sorted(bad))
        allrows = [r for r in allrows if r[1] not in bad]

    # 5. tiers (structural): A = >=2 independent datasets, C = PlantVillage only, else B.  Measured accuracy refines
    #    them after training (scripts/assign_tiers.py).
    seen = defaultdict(set)
    for _, l, s, _ in allrows:
        if s != "negative":
            seen[l].add(s)
    tiers = {}
    for l in sorted(seen):
        if l in ("unknown_plant", GENERIC):
            continue
        tiers[l] = "A" if len(seen[l]) >= 2 else ("C" if seen[l] == {"plantvillage"} else "B")
    json.dump(tiers, open(OUT / "tiers.json", "w"), indent=1)
    json.dump({"new_classes": sorted(set(tiers) - old_classes), "pooled": pooled}, open(OUT / "new_classes.json", "w"), indent=1)

    with open(OUT / "manifest.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["path", "label", "source", "split"])
        w.writerows(allrows)
    print("total rows", len(allrows), Counter(r[3] for r in allrows))
    print("classes", len({r[1] for r in allrows}), "tiers", Counter(tiers.values()))
    tbl = defaultdict(Counter)
    for _, l, s, sp in allrows:
        tbl[l][sp] += 1
    print(f"\n{'class':44s} tier train   val  t_pw  t_pd")
    for l in sorted(tbl):
        if l in old_classes and l not in ("unknown_plant",):
            continue
        c = tbl[l]
        print(f"{l:44s} {tiers.get(l, '-'):>4s} {c['train']:5d} {c['val']:5d} {c['test_plantwild']:5d} {c['test_plantdoc']:5d}")


if __name__ == "__main__":
    main()
