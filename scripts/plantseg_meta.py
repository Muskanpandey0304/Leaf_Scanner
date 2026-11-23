import io, sys
sys.path.insert(0, "scripts")
import zipfile, importlib.util
spec = importlib.util.spec_from_file_location("pl", "scripts/plantseg_list.py")
src = open("scripts/plantseg_list.py", encoding="utf-8").read().split("f = RangeFile(URL)")[0]
ns = {}
exec(src, ns)
f = ns["RangeFile"](ns["URL"])
z = zipfile.ZipFile(io.BufferedReader(f, buffer_size=1 << 20))
data = z.read("plantseg/Metadata.csv")
open("data/raw/plantseg_meta/Metadata.csv", "wb").write(data)
print(len(data), "bytes saved")
