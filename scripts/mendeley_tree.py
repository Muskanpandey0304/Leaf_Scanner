import json, sys, urllib.request
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})) as r:
        return json.loads(r.read())
def walk(ds, ver, folder="root", path=""):
    items = get(f"https://data.mendeley.com/public-api/datasets/{ds}/files?folder_id={folder}&version={ver}")
    for it in items:
        if "content_details" in it:
            yield path + "/" + it["filename"], it["content_details"]["download_url"], it["content_details"]["size"]
        else:
            yield from walk(ds, ver, it["id"], path + "/" + it.get("name", it["id"]))
if __name__ == "__main__":
    ds, ver, out = sys.argv[1], sys.argv[2], sys.argv[3]
    rows = list(walk(ds, ver))
    json.dump(rows, open(out, "w"))
    print(ds, len(rows), "files", round(sum(r[2] for r in rows) / 1e6), "MB")
    import collections
    print(collections.Counter("/".join(r[0].split("/")[:-1]) for r in rows).most_common(20))
