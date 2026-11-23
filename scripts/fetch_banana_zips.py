"""Two small CC BY 4.0 banana datasets as zips (original/raw images only)."""
import json, urllib.request
from pathlib import Path
R = Path(__file__).resolve().parent.parent / "data" / "raw" / "banana"
UA = {"User-Agent": "Mozilla/5.0"}
def get(u, t=600):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
for ds, name in (("79w2n6b4kf", "Original Images.zip"), ("5nfjzntwd8", "Banana and banana leaf dataset Raw.zip")):
    m = json.loads(get(f"https://data.mendeley.com/public-api/datasets/{ds}"))
    for f in m["files"]:
        if f["filename"] == name:
            out = R / f"{ds}.zip"; want = f["content_details"]["size"]
            if not out.exists() or out.stat().st_size != want:
                out.write_bytes(get(f["content_details"]["download_url"]))
            print(ds, out.stat().st_size, "of", want, flush=True)
