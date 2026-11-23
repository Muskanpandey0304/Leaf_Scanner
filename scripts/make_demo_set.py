"""Copy the verified-correct web test photos into demo_photos/ with readable names + a credits file."""
import csv, shutil
from pathlib import Path
import pandas as pd
R = Path(".")
res = pd.read_csv("scripts/web_test_models_run4.csv")
man = pd.read_csv("data/test_web/manifest.csv").set_index("file")
pick = {  # row number in the scored list -> demo file name
    21: "01_coffee_leaf_rust", 22: "02_banana_sigatoka", 20: "03_citrus_canker", 25: "04_soybean_rust",
    23: "05_peach_leaf_curl", 28: "06_basil_healthy", 31: "07_banana_healthy", 5: "08_potato_late_blight",
    18: "09_squash_powdery_mildew", 7: "10_NOT_A_LEAF_book_page",
}
out = R / "demo_photos"; out.mkdir(exist_ok=True)
rows = []
for n, name in pick.items():
    r = res.iloc[n]; m = man.loc[r.file]
    dst = out / f"{name}.jpg"; shutil.copy(R / "data/test_web" / r.file, dst)
    rows.append([dst.name, r.top, r.conf, r.band, m.title, m.license, m.page])
with open(out / "credits.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["file", "app_answer", "confidence", "band", "wikimedia_title", "license", "source_page"]); w.writerows(rows)
for r in rows: print(r[:4])
