"""Download a small independent test set from Wikimedia Commons (free-licensed photos), for a sanity check only.
Labels come from the search query and are verified by eye afterwards. Files go to data/test_web/ (git-ignored)."""
import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "test_web"
UA = {"User-Agent": "LeafScannerStudentProject/1.0 (portfolio test; non-commercial)"}
API = "https://commons.wikimedia.org/w/api.php"

# (our label or 'unsupported:<name>', search text, how many)
QUERIES = [
    ("tomato__late_blight", "tomato late blight leaf", 3), ("tomato__early_blight", "tomato early blight leaf", 2),
    ("tomato__septoria_leaf_spot", "tomato septoria leaf spot", 2), ("tomato__healthy", "tomato plant leaf healthy", 2),
    ("potato__late_blight", "potato late blight leaf", 3), ("potato__early_blight", "potato early blight leaf", 2),
    ("apple__scab", "apple scab leaf", 3), ("apple__rust", "cedar apple rust leaf", 2), ("apple__healthy", "apple leaf", 2),
    ("grape__downy_mildew", "grape downy mildew leaf", 2), ("grape__black_rot", "grape black rot leaf", 2),
    ("corn__common_rust", "corn common rust leaf", 2), ("corn__northern_leaf_blight", "northern corn leaf blight", 2),
    ("wheat__stripe_rust", "wheat stripe rust leaf", 2), ("wheat__leaf_rust", "wheat leaf rust", 2),
    ("cucumber__powdery_mildew", "cucumber powdery mildew leaf", 2), ("squash__powdery_mildew", "squash powdery mildew leaf", 2),
    ("rice__blast", "rice blast leaf", 2), ("citrus__canker", "citrus canker leaf", 2),
    ("coffee__leaf_rust", "coffee leaf rust", 2), ("banana__sigatoka", "black sigatoka banana leaf", 2),
    ("peach__leaf_curl", "peach leaf curl", 2), ("cherry__powdery_mildew", "cherry powdery mildew leaf", 1),
    ("soybean__rust", "soybean rust leaf", 2), ("bean__rust", "bean rust leaf", 1), ("cabbage__black_rot", "cabbage black rot", 2),
    ("strawberry__leaf_scorch", "strawberry leaf scorch", 1), ("basil__healthy", "basil leaves", 2), ("banana__healthy", "banana leaf", 2),
    ("unsupported:mango", "mango leaf", 2), ("unsupported:pothos", "pothos money plant leaf", 2),
    ("unsupported:rose_black_spot", "rose black spot leaf", 2), ("unsupported:neem", "neem leaf azadirachta", 1),
]


def open_url(req):
    for wait in (0, 20, 45, 90, 150):
        time.sleep(wait)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            time.sleep(1.5)
            return data
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
    raise RuntimeError("rate limited")


def get(params):
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    return json.loads(open_url(urllib.request.Request(url, headers=UA)))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, seen = [], set()
    for label, q, n in QUERIES:
        try:
            res = get({"action": "query", "generator": "search", "gsrsearch": q + " filetype:bitmap", "gsrnamespace": 6,
                       "gsrlimit": 12, "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 700})
            pages = sorted(res.get("query", {}).get("pages", {}).values(), key=lambda x: x.get("index", 0))
            got = 0
            for page in pages:
                t = page["title"]
                ii = (page.get("imageinfo") or [{}])[0]
                if got >= n or t in seen or not t.lower().endswith((".jpg", ".jpeg")):
                    continue
                if not ii.get("thumburl") or ii.get("width", 0) < 400:
                    continue
                lic = ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "?")
                f = OUT / label.replace(":", "_") / f"{len(rows):03d}.jpg"
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_bytes(open_url(urllib.request.Request(ii["thumburl"], headers=UA)))
                rows.append([str(f.relative_to(OUT)), label, q, t, lic, ii.get("descriptionurl", "")])
                seen.add(t)
                got += 1
            print(label, got, flush=True)
        except Exception as e:  # noqa: BLE001
            print("ERR", label, e, flush=True)
        with open(OUT / "manifest.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["file", "label", "query", "title", "license", "page"])
            w.writerows(rows)
    print(len(rows), "images downloaded")


main()
