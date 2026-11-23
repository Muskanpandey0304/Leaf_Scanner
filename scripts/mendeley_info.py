import json, sys, urllib.request
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})) as r:
        return json.loads(r.read())
for id_, ver in [("9tb7k297ff", 1), ("yy2k5y8mxg", 1), ("c5yvn32dzg", 2), ("wzshm7ky49", 1), ("sjmgzhwrxv", 1)]:
    try:
        d = get(f"https://data.mendeley.com/public-api/datasets/{id_}/versions/{ver}")
    except Exception as e:
        try:
            d = get(f"https://data.mendeley.com/public-api/datasets/{id_}")
        except Exception as e2:
            print(id_, "ERR", e, e2); continue
    lic = d.get("data_licence") or d.get("license") or {}
    print("==", id_, d.get("name"), "| licence:", lic.get("full_name") or lic.get("short_name") or lic, "| v", d.get("version"))
    for f in d.get("files", []):
        cd = f.get("content_details", {})
        print("  ", f.get("filename"), round(f.get("size", 0) / 1e6, 1), "MB", cd.get("download_url"))
