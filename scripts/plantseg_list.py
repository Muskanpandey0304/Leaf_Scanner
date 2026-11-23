"""List the file names inside the remote PlantSeg zip using HTTP range requests (no full download)."""
import io
import sys
import urllib.request
import zipfile
from collections import Counter, defaultdict

URL = "https://zenodo.org/api/records/17719108/files/plantseg.zip/content"


class RangeFile(io.RawIOBase):
    def __init__(self, url):
        self.url = url
        req = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
        with urllib.request.urlopen(req) as r:
            self.size = int(r.headers["Content-Range"].split("/")[1])
        self.pos = 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos

    def read(self, n=-1):
        if n < 0 or self.pos + n > self.size:
            n = self.size - self.pos
        if n <= 0:
            return b""
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{self.pos + n - 1}"})
        with urllib.request.urlopen(req) as r:
            data = r.read()
        self.pos += len(data)
        return data

    def readinto(self, b):
        d = self.read(len(b))
        b[: len(d)] = d
        return len(d)


f = RangeFile(URL)
print("zip size MB", round(f.size / 1e6), file=sys.stderr)
z = zipfile.ZipFile(io.BufferedReader(f, buffer_size=1 << 20))
names = [i.filename for i in z.infolist() if not i.is_dir()]
open("data/raw/plantseg_meta/names.txt", "w", encoding="utf-8").write("\n".join(names))
print(len(names), "files")
dirs = Counter("/".join(n.split("/")[:-1]) for n in names)
for d, c in sorted(dirs.items())[:60]:
    print(c, d)
print(len(dirs), "directories")
for n in names:
    if n.lower().endswith((".csv", ".txt", ".json", ".md")):
        print("META:", n, z.getinfo(n).file_size)
