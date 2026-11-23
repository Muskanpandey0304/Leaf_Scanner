p = "scripts/fetch_web_test.py"
s = open(p, encoding="utf-8").read()
a = s.index("def main():")
new_main = '''def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, seen = [], set()
    for label, q, n in QUERIES:
        try:
            res = get({"action": "query", "generator": "search", "gsrsearch": q + " filetype:bitmap", "gsrnamespace": 6,
                       "gsrlimit": 12, "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 700})
            pages = sorted(res.get("query", {}).get("pages", {}).values(), key=lambda x: x.get("index", 0))
            got = 0
            for page in pages:
                t = page["title"]
                ii = (page.get("imageinfo") or [{}])[0]
                if got >= n or t in seen or not t.lower().endswith((".jpg", ".jpeg")):
                    continue
                if not ii.get("thumburl") or ii.get("width", 0) < 400:
                    continue
                lic = ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "?")
                f = OUT / label.replace(":", "_") / f"{len(rows):03d}.jpg"
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_bytes(open_url(urllib.request.Request(ii["thumburl"], headers=UA)))
                rows.append([str(f.relative_to(OUT)), label, q, t, lic, ii.get("descriptionurl", "")])
                seen.add(t)
                got += 1
            print(label, got, flush=True)
        except Exception as e:  # noqa: BLE001
            print("ERR", label, e, flush=True)
        with open(OUT / "manifest.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["file", "label", "query", "title", "license", "page"])
            w.writerows(rows)
    print(len(rows), "images downloaded")


main()
'''
open(p, "w", encoding="utf-8").write(s[:a] + new_main)
print("ok")
