"""Reliability tiers from MEASURED accuracy on held-out test photos (never seen in training).
  * upgrade to A (no warning in the app): n >= 15 test photos and the 95% Wilson lower bound of accuracy >= 0.70
  * downgrade to B (warning shown):       n >= 15 test photos and measured accuracy < 0.70, even if the class has lots of training photos
  * otherwise keep the structural tier (A: >=2 datasets, B: 1 dataset, C: studio photos only)
Usage: assign_tiers.py models_run4 data/processed3"""
import json, math, sys
from collections import Counter
from pathlib import Path
R = Path(__file__).resolve().parent.parent
model, data = R / sys.argv[1], R / sys.argv[2]
rep = json.load(open(model / "report.json"))
tiers = json.load(open(data / "tiers.json"))
N_MIN, LB_UP, ACC_DOWN = 15, 0.70, 0.70

def wilson_lb(k, n, z=1.96):
    p = k / n
    return (p + z * z / (2 * n) - z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)

n_tot, k_tot = {}, {}
for split in ("test_plantwild", "test_plantdoc"):
    for c, v in rep.get(split, {}).get("per_class", {}).items():
        n_tot[c] = n_tot.get(c, 0) + v["n"]
        k_tot[c] = k_tot.get(c, 0) + v["n"] * v["acc"]
final, detail = dict(tiers), {}
for c, t in tiers.items():
    n, k = n_tot.get(c, 0), k_tot.get(c, 0.0)
    acc = k / n if n else None
    lb = wilson_lb(k, n) if n else 0.0
    d = {"structural": t, "test_n": n, "test_acc": None if acc is None else round(acc, 3), "wilson_lb": round(lb, 3)}
    if n >= N_MIN and lb >= LB_UP:
        final[c] = "A"
        d["change"] = "up" if t != "A" else "same"
    elif n >= N_MIN and acc < ACC_DOWN and t == "A":
        final[c] = "B"
        d["change"] = "down"
    detail[c] = d
json.dump(final, open(data / "tiers_final.json", "w"), indent=1)
json.dump(detail, open(data / "tiers_detail.json", "w"), indent=1)
print("structural", dict(Counter(tiers.values())), "-> final", dict(Counter(final.values())))
print("UP  :", sorted(c for c, d in detail.items() if d.get("change") == "up"))
print("DOWN:", sorted(c for c, d in detail.items() if d.get("change") == "down"))
