"""Read a stored/deflated zip by walking local file headers (for archives with a broken central directory)."""
import struct, zlib

def iter_zip(path):
    with open(path, "rb") as f:
        while True:
            h = f.read(30)
            if len(h) < 30 or h[:4] != b"PK\x03\x04":
                return
            _, flags, method, _, _, _, csize, usize, nlen, elen = struct.unpack("<HHHHHIIIHH", h[4:30])
            name = f.read(nlen).decode("utf-8", "replace")
            f.read(elen)
            data = f.read(csize)
            if method == 8:
                data = zlib.decompress(data, -15)
            if not name.endswith("/"):
                yield name, data
