"""Download the Mendeley coffee/banana datasets (resumable, parallel). Big photos are shrunk to <=800px.
Layout:
  data/raw/coffee/bracol/<zip>            (kept as zip, extracted later)
  data/raw/coffee/rocole/img/*.jpg + meta files
  data/raw/banana/bananalsd/<folder_id>__<count>/<n>.jpeg
"""
import io
import json
import sys
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0"}


def get(url, timeout=120):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()


def meta(d):
    return json.loads(get(f"https://data.mendeley.com/public-api/datasets/{d}"))


def fetch(url, dest, shrink=False, tries=5):
    if dest.exists() and dest.stat().st_size > 0:
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(tries):
        try:
            data = get(url)
            if shrink and dest.suffix.lower() in (".jpg", ".jpeg"):
                im = Image.open(io.BytesIO(data)).convert("RGB")
                im.thumbnail((800, 800))
                im.save(dest, quality=90)
            else:
                dest.write_bytes(data)
            return True
        except Exception as e:  # noqa: BLE001
            err = e
    print("FAILED", dest.name, err, file=sys.stderr)
    return False


def run(jobs, label):
    ok = 0
    with ThreadPoolExecutor(8) as ex:
        for i, r in enumerate(ex.map(lambda j: fetch(*j), jobs), 1):
            ok += bool(r)
            if i % 200 == 0:
                print(label, i, "/", len(jobs), flush=True)
    print(label, "done", ok, "/", len(jobs), flush=True)


# --- BRACOL: one zip
m = meta("yy2k5y8mxg")
f = m["files"][0]
dest = ROOT / "coffee" / "bracol" / "bracol.zip"
want = f["content_details"]["size"]
if not dest.exists() or dest.stat().st_size != want:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(get(f["content_details"]["download_url"], 600))
print("bracol", dest.stat().st_size, "of", want, flush=True)

# --- BananaLSD: raw folders only (the 400-image folders are augmented copies)
m = meta("9tb7k297ff")
cnt = Counter(f["folder_id"] for f in m["files"])
jobs = []
seen = Counter()
for f in m["files"]:
    n = cnt[f["folder_id"]]
    if n == 400:
        continue
    seen[f["folder_id"]] += 1
    dest = ROOT / "banana" / "bananalsd" / f"{f['folder_id'][:8]}__{n}" / f"{seen[f['folder_id']]}_{f['filename']}"
    jobs.append((f["content_details"]["download_url"], dest, False))
run(jobs, "bananalsd")

# --- RoCoLe: images (shrunk) + label files
m = meta("c5yvn32dzg")
jobs = []
for f in m["files"]:
    url = f["content_details"]["download_url"]
    if f["filename"].lower().endswith(".jpg"):
        jobs.append((url, ROOT / "coffee" / "rocole" / "img" / f["filename"], True))
    else:
        jobs.append((url, ROOT / "coffee" / "rocole" / "meta" / f["filename"], False))
run(jobs, "rocole")
