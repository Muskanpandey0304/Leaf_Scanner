"""List/extract selected entries of a remote zip via HTTP range requests: zip_remote_list.py URL [pattern outdir]"""
import io, sys, urllib.request, zipfile, re
class RangeFile(io.RawIOBase):
    def __init__(self, url):
        self.url = url
        req = urllib.request.Request(url, headers={"Range": "bytes=0-0", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as r:
            self.size = int(r.headers["Content-Range"].split("/")[1])
        self.pos = 0
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos
    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos
    def read(self, n=-1):
        if n < 0 or self.pos + n > self.size: n = self.size - self.pos
        if n <= 0: return b""
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{self.pos+n-1}", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r: data = r.read()
        self.pos += len(data); return data
    def readinto(self, b):
        d = self.read(len(b)); b[:len(d)] = d; return len(d)
if __name__ == "__main__":
    z = zipfile.ZipFile(io.BufferedReader(RangeFile(sys.argv[1]), buffer_size=1 << 20))
    names = [i for i in z.infolist() if not i.is_dir()]
    if len(sys.argv) == 2:
        import collections
        c = collections.Counter("/".join(i.filename.split("/")[:3]) for i in names)
        for k, v in sorted(c.items()): print(v, k)
    else:
        pat, out = re.compile(sys.argv[2]), sys.argv[3]
        import os
        from pathlib import Path
        sel = [i for i in names if pat.search(i.filename)]
        print(len(sel), "selected", round(sum(i.file_size for i in sel)/1e6), "MB")
        for k, i in enumerate(sel):
            dst = Path(out) / (f"{k}_" + os.path.basename(i.filename))
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(z.read(i))
