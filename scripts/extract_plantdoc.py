"""Extract PlantDoc from the cloned git repo, sanitizing filenames Windows rejects ('?', newlines...)."""
import re
import subprocess
import sys
from pathlib import Path

repo = Path(sys.argv[1])
out = Path(sys.argv[2])
raw = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "-z", "HEAD"],
                     capture_output=True, check=True).stdout
bad = re.compile(r'[<>:"|?*\x00-\x1f]')
n = skipped = 0
for entry in raw.split(b"\0"):
    if not entry:
        continue
    meta, path = entry.split(b"\t", 1)
    sha = meta.split()[2].decode()
    path = path.decode("utf-8", "replace")
    parts = [re.sub(r"\s+", " ", bad.sub("_", p)).strip() for p in path.split("/")]
    parts = [p[:100] if i == len(parts) - 1 else p for i, p in enumerate(parts)]
    # keep a valid image extension after truncation / sanitization
    dest = out.joinpath(*parts)
    if not path.lower().endswith((".jpg", ".jpeg", ".png")) or not path.startswith(("train/", "test/")):
        skipped += 1
        continue
    if dest.suffix.lower() not in (".jpg", ".jpeg", ".png"):
        dest = dest.with_name(dest.name + ".jpg")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest = dest.with_name(f"{dest.stem}_{sha[:6]}{dest.suffix}")
    dest.write_bytes(subprocess.run(["git", "-C", str(repo), "cat-file", "blob", sha],
                                    capture_output=True, check=True).stdout)
    n += 1
print(f"extracted {n} images, skipped {skipped} non-image/other files")
