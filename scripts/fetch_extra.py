"""Download the banana + coffee datasets (all CC BY 4.0 on Mendeley Data) into data/raw/. Resumable: skips finished files."""
import json
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

R = Path(__file__).resolve().parent.parent / "data" / "raw"
UA = {"User-Agent": "Mozilla/5.0"}


def api(ds):
    with urllib.request.urlopen(urllib.request.Request(f"https://data.mendeley.com/public-api/datasets/{ds}", headers=UA)) as r:
        return json.loads(r.read())


def fetch(url, out, size=None):
    out = Path(out)
    if out.exists() and (size is None or out.stat().st_size == size):
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r, open(out, "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            if size is None or out.stat().st_size == size:
                return
        except Exception as e:  # noqa: BLE001
            print("retry", out.name, e, file=sys.stderr)
    print("FAILED", out, file=sys.stderr)


def main():
    jobs = []
    # BananaLSD: only the 4 raw class folders (the 400-image folders are augmented copies)
    d = api("9tb7k297ff")
    raw = {"2f782abe-4cce-463b-80b1-e0ef359488ab": "sigatoka", "87d14638-ce4a-4b25-be8e-c6d993c09238": "pestalotiopsis",
           "74dcf511-d0dc-47a3-8b06-59734003843c": "cordana", "336f946e-178e-4d37-8051-c368486849d3": "healthy"}
    for f in d["files"]:
        cls = raw.get(f.get("folder_id"))
        if cls:
            cd = f["content_details"]
            jobs.append((cd["download_url"], R / "banana" / "bananalsd" / cls / f["filename"], cd["size"]))
    # Banana Disease Recognition Dataset (original images, 7 classes) + Banana and Banana Leaf (raw)
    for ds, names in (("79w2n6b4kf", ["Original Images.zip"]), ("5nfjzntwd8", ["Banana and banana leaf dataset Raw.zip"])):
        for f in api(ds)["files"]:
            if f["filename"] in names:
                cd = f["content_details"]
                jobs.append((cd["download_url"], R / "banana" / f"{ds}.zip", cd["size"]))
    # RoCoLe images + annotation tables
    d = api("c5yvn32dzg")
    for f in d["files"]:
        cd = f["content_details"]
        ext = f["filename"].rsplit(".", 1)[-1].lower()
        if ext in ("jpg", "csv", "xlsx", "json"):
            jobs.append((cd["download_url"], R / "coffee" / "rocole" / f["filename"], cd["size"]))
    print(len(jobs), "files to check", flush=True)
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(lambda j: fetch(*j), jobs))
    print("done")


main()
