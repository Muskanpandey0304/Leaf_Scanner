import json, urllib.request
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60))
for d in ("c5yvn32dzg", "9tb7k297ff"):
    m = get(f"https://data.mendeley.com/public-api/datasets/{d}")
    print(d, "keys", list(m.keys()))
    print("  files:", json.dumps(m.get("files"))[:600])
    print("  folders:", json.dumps(m.get("folders"))[:300], "| version", m.get("version"))
    for v in (1, 2, 3):
        try:
            r = get(f"https://data.mendeley.com/public-api/datasets/{d}/files?folder_id=root&version={v}")
            print("  v", v, len(r), [x.get("filename") for x in r][:5])
        except Exception as e:
            print("  v", v, "ERR", e)
