p = "scripts/build_dataset3.py"
s = open(p, encoding="utf-8").read()
a = s.index("    # RoCoLe (labels from its annotation csv if present)")
b = s.index("    # wheat healthy")
new = '''    # RoCoLe: labels live in the Labelbox export (External ID = file name, Label = JSON with "classification")
    roc = RAW / "coffee" / "rocole"
    lc = roc / "meta" / "RoCoLE-csv.csv"
    if lc.exists():
        df = pd.read_csv(lc)
        for r in df.itertuples(index=False):
            row = dict(zip(df.columns, r))
            f = roc / "img" / str(row["External ID"])
            try:
                cls = json.loads(row["Label"])["classification"]
            except Exception:  # noqa: BLE001
                continue
            lab = None
            if cls == "healthy":
                lab = "coffee__healthy"
            elif cls in ("rust_level_2", "rust_level_3", "rust_level_4"):  # level 1 is too faint to be a clean label
                lab = "coffee__leaf_rust"
            if lab and f.exists():
                m = re.match(r"(C\d+P\d+)", str(row["External ID"]))
                add(("file", str(f)), lab, "rocole", m.group(1) if m else None)
'''
s = s[:a] + new + s[b:]
open(p, "w", encoding="utf-8").write(s)
print("patched")
