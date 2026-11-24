"""Build the README analysis charts from saved project files (no retraining needed).

Inputs : data/processed3/manifest.csv, data/processed3/tiers_detail.json, tiers_final.json,
         models_run1..4/report.json, scripts/train_run4.log
Output : docs/charts/<name>_light.png and <name>_dark.png

    python scripts/make_charts.py
"""
import json
import math
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed3"
OUT = ROOT / "docs" / "charts"
OUT.mkdir(parents=True, exist_ok=True)

# Validated palette (categorical slots 1-3 pass all-pairs CVD checks in both modes).
THEMES = {
    "light": dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", muted="#898781",
                  grid="#e1e0d9", axis="#c3c2b7", s1="#2a78d6", s2="#eb6834", s3="#1baf7a",
                  neutral="#b5b3ab"),
    "dark": dict(surface="#1a1a19", ink="#f0efec", ink2="#c3c2b7", muted="#898781",
                 grid="#2c2c2a", axis="#383835", s1="#3987e5", s2="#d95926", s3="#199e70",
                 neutral="#5f5e59"),
}

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"],
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.titlepad": 26,
    "savefig.dpi": 150,
})


def style(fig, axes, t, ygrid=True, xgrid=False):
    fig.patch.set_facecolor(t["surface"])
    for ax in axes:
        ax.set_facecolor(t["surface"])
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(t["axis"])
            ax.spines[side].set_linewidth(0.8)
        ax.tick_params(colors=t["muted"], labelcolor=t["ink2"], length=0)
        ax.title.set_color(t["ink"])
        ax.xaxis.label.set_color(t["ink2"])
        ax.yaxis.label.set_color(t["ink2"])
        ax.set_axisbelow(True)
        if ygrid:
            ax.yaxis.grid(True, color=t["grid"], linewidth=0.8)
        if xgrid:
            ax.xaxis.grid(True, color=t["grid"], linewidth=0.8)


def subtitle(ax, text, t):
    ax.text(0, 1.02, text, transform=ax.transAxes, color=t["ink2"], fontsize=10.5, va="bottom")


def legend(ax, t, **kw):
    lg = ax.legend(frameon=False, labelcolor=t["ink2"], **kw)
    return lg


def save(fig, name, mode):
    fig.savefig(OUT / f"{name}_{mode}.png", facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


def pct(ax, axis="y"):
    fmt = matplotlib.ticker.PercentFormatter(1.0, decimals=0)
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


# ---------------------------------------------------------------- load data
manifest = pd.read_csv(DATA / "manifest.csv")
tiers_detail = json.load(open(DATA / "tiers_detail.json"))
tiers_final = json.load(open(DATA / "tiers_final.json"))
reports = {f"run{i}": json.load(open(ROOT / f"models_run{i}" / "report.json")) for i in range(1, 5)}
r4 = reports["run4"]

log = (ROOT / "scripts" / "train_run4.log").read_text()
epochs = [(int(e), float(l), float(v)) for e, l, v in
          re.findall(r"ep (\d+)/\d+ loss ([\d.]+) val_acc ([\d.]+)", log)]

SOURCE_NAMES = {
    "plantvillage": "PlantVillage", "plantwild": "PlantWild", "plantdoc": "PlantDoc",
    "plantseg": "PlantSeg", "bracol": "BRACOL (coffee)", "rocole": "RoCoLe (coffee)",
    "banana_a": "Banana Disease Recognition", "banana_b": "Banana and Banana Leaf",
    "bananalsd": "BananaLSD", "wheat_bd": "Wheat", "negative": "Unknown-class images",
}
SOURCE_GROUP = {
    "plantvillage": "Studio photos (plain background)",
    "plantwild": "Web and field photos", "plantdoc": "Web and field photos", "plantseg": "Web and field photos",
    "bracol": "Crop-specific field datasets", "rocole": "Crop-specific field datasets",
    "banana_a": "Crop-specific field datasets", "banana_b": "Crop-specific field datasets",
    "bananalsd": "Crop-specific field datasets", "wheat_bd": "Crop-specific field datasets",
    "negative": "Non-leaf images (for the unknown class)",
}


def wilson(acc, n, z=1.96):
    k = acc * n
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


# ---------------------------------------------------------------- charts
def chart_composition(t, mode):
    counts = manifest["source"].value_counts()
    total = counts.sum()
    studio_share = counts.get("plantvillage", 0) / total
    group_color = {
        "Studio photos (plain background)": t["s1"],
        "Web and field photos": t["s2"],
        "Crop-specific field datasets": t["s3"],
        "Non-leaf images (for the unknown class)": t["neutral"],
    }
    order = counts.sort_values()
    fig, ax = plt.subplots(figsize=(10, 5.6))
    style(fig, [ax], t, ygrid=False, xgrid=True)
    colors = [group_color[SOURCE_GROUP[s]] for s in order.index]
    ax.barh([SOURCE_NAMES[s] for s in order.index], order.values, color=colors, height=0.7)
    for i, v in enumerate(order.values):
        ax.text(v + total * 0.006, i, f"{v:,}  ({v / total:.1%})", va="center", color=t["ink2"], fontsize=9.5)
    ax.set_xlim(0, order.max() * 1.25)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x / 1000:.0f}k"))
    ax.set_xlabel("Images")
    ax.set_title(f"{studio_share:.0%} of the {total:,} images are studio photos")
    subtitle(ax, "Images per source dataset. Studio photos are easy for the model; real field photos are scarce.", t)
    handles = [matplotlib.patches.Patch(color=c, label=g) for g, c in group_color.items()]
    legend(ax, t, handles=handles, loc="lower right")
    save(fig, "01_dataset_composition", mode)


def chart_imbalance(t, mode):
    train = manifest[(manifest["split"] == "train") & (manifest["source"] != "negative")]
    per_class = train["label"].value_counts().sort_values(ascending=False)
    n_small = int((per_class < 50).sum())
    fig, ax = plt.subplots(figsize=(11, 4.8))
    style(fig, [ax], t)
    x = range(len(per_class))
    ax.bar(x, per_class.values, color=t["s1"], width=0.75)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.tick_params(which="minor", length=0)
    ax.axhline(50, color=t["ink2"], linewidth=1)
    ax.text(len(per_class) - 1, 56, "50 images", ha="right", va="bottom", color=t["ink2"], fontsize=9.5)
    ax.set_xticks([])
    ax.set_xlim(-1, len(per_class))
    ax.set_xlabel(f"{len(per_class)} conditions, sorted by number of training images")
    ax.set_ylabel("Training images (log scale)")
    top, bottom = per_class.index[0], per_class.index[-1]
    ax.set_title(f"{n_small} of {len(per_class)} conditions have fewer than 50 training images")
    subtitle(ax, f"Long-tailed class distribution: from {per_class.iloc[0]:,} images "
                 f"({top.replace('__', ' / ').replace('_', ' ')}) down to {per_class.iloc[-1]} "
                 f"({bottom.replace('__', ' / ').replace('_', ' ')}).", t)
    save(fig, "02_class_imbalance", mode)


def chart_training(t, mode):
    ep = [e for e, _, _ in epochs]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    style(fig, [a1, a2], t)
    a1.plot(ep, [l for _, l, _ in epochs], color=t["s1"], linewidth=2, marker="o", markersize=5)
    a1.set_title("Training loss", pad=10)
    a1.set_xlabel("Epoch")
    a2.plot(ep, [v for _, _, v in epochs], color=t["s1"], linewidth=2, marker="o", markersize=5)
    a2.set_title("Validation accuracy", pad=10)
    a2.set_xlabel("Epoch")
    pct(a2)
    a2.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.05))
    last = epochs[-1]
    best = max(epochs, key=lambda r: r[2])
    a2.annotate(f"best {best[2]:.1%}", (best[0], best[2]), xytext=(-10, -28), textcoords="offset points",
                ha="right", color=t["ink"], fontsize=10,
                arrowprops=dict(arrowstyle="-", color=t["muted"], linewidth=0.8))
    a1.annotate(f"{last[1]:.2f}", (last[0], last[1]), xytext=(0, 10), textcoords="offset points",
                ha="center", color=t["ink"], fontsize=10)
    for a in (a1, a2):
        a.set_xticks(range(2, len(ep) + 1, 2))
    fig.suptitle("Model training (EfficientNet-B0, 18 epochs, GTX 1650, about 3 hours)",
                 x=0.06, ha="left", y=1.04, fontsize=14, fontweight="bold", color=t["ink"])
    save(fig, "03_training_curves", mode)


def chart_evolution(t, mode):
    runs = list(reports)
    labels = [f"Run {i + 1}" for i in range(len(runs))]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={"width_ratios": [1, 1.4]})
    style(fig, [a1, a2], t)
    classes = [reports[r]["classes"] for r in runs]
    a1.bar(labels, classes, color=t["s1"], width=0.55)
    for i, c in enumerate(classes):
        a1.text(i, c + 2, str(c), ha="center", va="bottom", color=t["ink"], fontsize=10)
    a1.set_ylim(0, max(classes) * 1.18)
    a1.set_title("Classes the model knows", pad=10)

    pw = [reports[r]["test_plantwild"]["acc"] for r in runs]
    pd_ = [reports[r]["test_plantdoc"]["acc"] for r in runs]
    a2.plot(labels, pw, color=t["s1"], linewidth=2, marker="o", markersize=6, label="PlantWild (web photos)")
    a2.plot(labels, pd_, color=t["s2"], linewidth=2, marker="o", markersize=6, label="PlantDoc (field photos)")
    for series, name in ((pw, "PlantWild"), (pd_, "PlantDoc")):
        a2.text(len(runs) - 1 + 0.08, series[-1], f"{name} {series[-1]:.1%}", va="center",
                color=t["ink"], fontsize=10)
    a2.set_xlim(-0.3, len(runs) - 1 + 0.9)
    a2.set_ylim(0.5, 0.9)
    pct(a2)
    a2.set_title("Held-out test accuracy", pad=10)
    legend(a2, t, loc="upper left", ncol=2)
    fig.suptitle("Classes grew from 34 to 127, with test accuracy in the same range",
                 x=0.06, ha="left", y=1.08, fontsize=14, fontweight="bold", color=t["ink"])
    pw_n = [reports[r]["test_plantwild"]["n"] for r in runs]
    pd_n = reports[runs[-1]]["test_plantdoc"]["n"]
    fig.text(0.06, 1.0, f"The PlantWild test set grew with the classes ({pw_n[0]:,} to {pw_n[-1]:,} photos), so runs are "
                        f"not strictly comparable. PlantDoc has only {pd_n} photos, so ±3 points is noise.",
             ha="left", color=t["ink2"], fontsize=10.5)
    save(fig, "04_model_evolution", mode)


def chart_risk_coverage(t, mode):
    fig, ax = plt.subplots(figsize=(10, 5.2))
    style(fig, [ax], t, xgrid=True)
    for key, name, c in (("test_plantwild", "PlantWild (web photos)", t["s1"]),
                         ("test_plantdoc", "PlantDoc (field photos)", t["s2"])):
        rep = r4[key]
        pts = [(1.0, rep["acc"], 0.0)] + [(p["coverage"], p["accuracy_on_answered"], p["threshold"])
                                         for p in rep["risk_coverage"]]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=c, linewidth=2, marker="o", markersize=6,
                label=f"{name}, n = {rep['n']:,}")
        for cov, acc, th in pts:
            if th == 0.8:
                ax.annotate(f"{acc:.0%} accurate on\nthe {cov:.0%} shown as High",
                            (cov, acc), xytext=(14, -34), textcoords="offset points",
                            color=t["ink"], fontsize=9.5,
                            arrowprops=dict(arrowstyle="-", color=t["muted"], linewidth=0.8))
            if th == 0.0:
                ax.annotate(f"all photos: {acc:.1%}", (cov, acc), xytext=(10, -4), textcoords="offset points",
                            ha="left", va="top", color=t["ink2"], fontsize=9.5)
    ax.invert_xaxis()
    pct(ax, "x")
    pct(ax, "y")
    ax.set_ylim(0.55, 1.0)
    ax.set_xlabel("Share of photos the model answers (confidence threshold rises to the right: 0, 50, 70, 80, 90, 95%)")
    ax.set_ylabel("Accuracy on answered photos")
    ax.set_title("When the model is confident, it is usually right")
    subtitle(ax, "Calibrated confidence lets the app answer the clear photos and ask for a retake on the rest.", t)
    legend(ax, t, loc="lower right")
    save(fig, "05_confidence_vs_accuracy", mode)


def chart_per_class(t, mode):
    rows = []
    for cls, d in tiers_detail.items():
        n, acc = d.get("test_n") or 0, d.get("test_acc")
        if n >= 5 and acc is not None:
            lo, hi = wilson(acc, n)
            rows.append((cls, acc, lo, hi, n, tiers_final.get(cls, d.get("structural"))))
    rows.sort(key=lambda r: r[1])
    skipped = len(tiers_detail) - len(rows)
    tier_color = {"A": t["s1"], "B": t["s2"], "C": t["s3"]}
    tier_name = {"A": "Tier A: reliable", "B": "Tier B: lower reliability (app shows a warning)",
                 "C": "Tier C: studio photos only"}
    fig, ax = plt.subplots(figsize=(12, 5.4))
    style(fig, [ax], t)
    for i, (cls, acc, lo, hi, n, tier) in enumerate(rows):
        c = tier_color[tier]
        ax.vlines(i, lo, hi, color=c, linewidth=1.4, alpha=0.55)
        ax.plot(i, acc, "o", color=c, markersize=4.5, markeredgecolor=t["surface"], markeredgewidth=0.8)
    ax.axhline(0.7, color=t["ink2"], linewidth=1, zorder=0)
    ax.set_xticks([])
    ax.set_xlim(-1.5, len(rows) + 0.5)
    ax.set_ylim(-0.02, 1.04)
    pct(ax)
    ax.set_xlabel(f"{len(rows)} conditions with 5+ test photos, sorted by accuracy "
                  f"({skipped} with fewer are not shown)")
    ax.set_ylabel("Test accuracy")
    counts = {k: sum(1 for r in rows if r[5] == k) for k in tier_color}
    handles = [matplotlib.lines.Line2D([], [], color=tier_color[k], marker="o", linewidth=1.4,
                                       label=f"{tier_name[k]} ({counts[k]})")
               for k in tier_color if counts[k]]
    legend(ax, t, handles=handles, loc="lower right")
    ax.set_title("Per-condition accuracy, with 95% confidence intervals")
    subtitle(ax, "Dots are measured accuracy; bars show the uncertainty (few test photos = long bar). "
                 "The line marks 70%, the level the reliability tiers are judged against.", t)
    save(fig, "06_per_class_accuracy", mode)


def chart_lab_vs_field(t, mode):
    items = [("Validation set\n(mixed, incl. studio)", r4["best_val_acc"]),
             ("PlantWild test\n(web photos)", r4["test_plantwild"]["acc"]),
             ("PlantDoc test\n(real field photos)", r4["test_plantdoc"]["acc"])]
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    style(fig, [ax], t)
    colors = [t["neutral"], t["neutral"], t["s2"]]
    ax.bar([i[0] for i in items], [i[1] for i in items], color=colors, width=0.55)
    for i, (_, v) in enumerate(items):
        ax.text(i, v + 0.015, f"{v:.1%}", ha="center", va="bottom", color=t["ink"], fontsize=12, fontweight="bold")
    ax.set_ylim(0, 1)
    pct(ax)
    gap = items[0][1] - items[2][1]
    ax.set_title(f"Accuracy drops {gap * 100:.0f} points on real field photos")
    subtitle(ax, "Same model, three test sets. Messy backgrounds and lighting are harder than curated images.", t)
    save(fig, "07_lab_vs_field", mode)


CHARTS = [chart_composition, chart_imbalance, chart_training, chart_evolution,
          chart_risk_coverage, chart_per_class, chart_lab_vs_field]

if __name__ == "__main__":
    for mode, theme in THEMES.items():
        plt.rcParams["axes.titlecolor"] = theme["ink"]
        for fn in CHARTS:
            fn(theme, mode)
    print("wrote", len(list(OUT.glob("*.png"))), "files to", OUT)
