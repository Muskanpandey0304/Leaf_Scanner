import json, urllib.request, collections
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60))
for d in ("c5yvn32dzg", "9tb7k297ff", "yy2k5y8mxg"):
    m = get(f"https://data.mendeley.com/public-api/datasets/{d}")
    fs = m["files"]
    c = collections.Counter(f.get("folder_id") for f in fs)
    print(d, len(fs), "files;", len(c), "folders; size MB", round(sum(f["content_details"]["size"] for f in fs)/1e6))
    names = collections.Counter(f["filename"].rsplit(".",1)[-1].lower() for f in fs)
    print("  ext", dict(names))
    print("  sample", [f["filename"] for f in fs[:3]], list(c.items())[:3])
    for ep in (f"datasets/{d}/folders?version={m['version']}", f"datasets/{d}/folders/{list(c)[0]}"):
        try:
            print("  ", ep, json.dumps(get("https://data.mendeley.com/public-api/"+ep))[:300])
        except Exception as e:
            print("  ", ep, "ERR", e)
