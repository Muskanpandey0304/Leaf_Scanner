"""Shared label scheme: canonical class = '<crop>__<condition>'.

Anything mapped to None is deliberately excluded (not a typo). Run this file to check that every
folder in PlantDoc / PlantWild is covered and to see per-class dataset coverage.
Assumptions to verify by looking at images are marked  # CHECK.
"""
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "data"

PLANTDOC = {
    "Apple leaf": "apple__healthy",
    "Apple rust leaf": "apple__rust",
    "Apple Scab Leaf": "apple__scab",
    "Bell_pepper leaf": "bell_pepper__healthy",
    "Bell_pepper leaf spot": "bell_pepper__bacterial_spot",  # CHECK: PlantDoc says only 'leaf spot'
    "Blueberry leaf": "blueberry__healthy",
    "Cherry leaf": "cherry__healthy",
    "Corn Gray leaf spot": "corn__gray_leaf_spot",
    "Corn leaf blight": "corn__northern_leaf_blight",  # CHECK: could include southern blight
    "Corn rust leaf": "corn__common_rust",
    "grape leaf": "grape__healthy",
    "grape leaf black rot": "grape__black_rot",
    "Peach leaf": "peach__healthy",
    "Potato leaf early blight": "potato__early_blight",
    "Potato leaf late blight": "potato__late_blight",
    "Raspberry leaf": "raspberry__healthy",
    "Soyabean leaf": "soybean__healthy",
    "Squash Powdery mildew leaf": "squash__powdery_mildew",
    "Strawberry leaf": "strawberry__healthy",
    "Tomato Early blight leaf": "tomato__early_blight",
    "Tomato leaf": "tomato__healthy",
    "Tomato leaf bacterial spot": "tomato__bacterial_spot",
    "Tomato leaf late blight": "tomato__late_blight",
    "Tomato leaf mosaic virus": "tomato__mosaic_virus",
    "Tomato leaf yellow virus": "tomato__yellow_leaf_curl_virus",
    "Tomato mold leaf": "tomato__leaf_mold",
    "Tomato Septoria leaf spot": "tomato__septoria_leaf_spot",
    "Tomato two spotted spider mites leaf": "tomato__spider_mites",
}

# PlantWild: "<crop> leaf" folders are assumed to be healthy leaves.  # CHECK by viewing images
PLANTWILD = {
    "apple leaf": "apple__healthy", "apple scab": "apple__scab", "apple black rot": "apple__black_rot",
    "apple rust": "apple__rust", "apple mosaic virus": "apple__mosaic_virus",
    "bell pepper leaf": "bell_pepper__healthy", "bell pepper leaf spot": "bell_pepper__bacterial_spot",
    "blueberry leaf": "blueberry__healthy",
    "cherry leaf": "cherry__healthy", "cherry powdery mildew": "cherry__powdery_mildew",
    "cherry leaf spot": "cherry__leaf_spot",
    "corn leaf": "corn__healthy", "corn gray leaf spot": "corn__gray_leaf_spot",
    "corn northern leaf blight": "corn__northern_leaf_blight", "corn rust": "corn__common_rust",
    "corn smut": "corn__smut",
    "grape leaf": "grape__healthy", "grape black rot": "grape__black_rot",
    "grape downy mildew": "grape__downy_mildew", "grape leaf spot": "grape__leaf_blight",  # CHECK
    "grapevine leafroll disease": "grape__leafroll_disease",
    "peach leaf": "peach__healthy", "peach leaf curl": "peach__leaf_curl",
    "potato leaf": "potato__healthy", "potato early blight": "potato__early_blight",
    "potato late blight": "potato__late_blight",
    "raspberry leaf": "raspberry__healthy",
    "soybean leaf": "soybean__healthy",
    "squash leaf": "squash__healthy", "squash powdery mildew": "squash__powdery_mildew",
    "strawberry leaf": "strawberry__healthy", "strawberry leaf scorch": "strawberry__leaf_scorch",
    "strawberry anthracnose": "strawberry__anthracnose",
    "tomato leaf": "tomato__healthy", "tomato bacterial leaf spot": "tomato__bacterial_spot",
    "tomato early blight": "tomato__early_blight", "tomato late blight": "tomato__late_blight",
    "tomato leaf mold": "tomato__leaf_mold", "tomato septoria leaf spot": "tomato__septoria_leaf_spot",
    "tomato mosaic virus": "tomato__mosaic_virus", "citrus greening disease": "citrus__greening", "tomato yellow leaf curl virus": "tomato__yellow_leaf_curl_virus",
}

PW_CROPS = ["bell pepper", "apple", "banana", "basil", "bean", "blueberry", "broccoli", "cabbage", "carrot",
            "cauliflower", "celery", "cherry", "citrus", "coffee", "corn", "cucumber", "eggplant", "garlic",
            "ginger", "grapevine", "grape", "lettuce", "maple", "peach", "plum", "potato", "raspberry", "rice",
            "soybean", "squash", "strawberry", "tobacco", "tomato", "zucchini"]


def auto_plantwild(folder):
    """Canonical id for PlantWild folders not in the explicit map: '<crop> leaf' = healthy."""
    for crop in PW_CROPS:
        if folder == crop or folder.startswith(crop + " "):
            cond = folder[len(crop):].strip()
            cond = "healthy" if cond in ("", "leaf") else cond.replace(" ", "_")
            return crop.replace(" ", "_") + "__" + cond
    return folder.replace(" ", "_") + "__healthy"


def plantwild_label(folder):
    return PLANTWILD.get(folder) or auto_plantwild(folder)

PLANTVILLAGE = {
    "Apple___Apple_scab": "apple__scab", "Apple___Black_rot": "apple__black_rot",
    "Apple___Cedar_apple_rust": "apple__rust", "Apple___healthy": "apple__healthy",
    "Blueberry___healthy": "blueberry__healthy",
    "Cherry_(including_sour)___Powdery_mildew": "cherry__powdery_mildew",
    "Cherry_(including_sour)___healthy": "cherry__healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": "corn__gray_leaf_spot",
    "Corn_(maize)___Common_rust_": "corn__common_rust",
    "Corn_(maize)___Northern_Leaf_Blight": "corn__northern_leaf_blight",
    "Corn_(maize)___healthy": "corn__healthy",
    "Grape___Black_rot": "grape__black_rot", "Grape___Esca_(Black_Measles)": "grape__esca",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": "grape__leaf_blight", "Grape___healthy": "grape__healthy",
    "Orange___Haunglongbing_(Citrus_greening)": "citrus__greening",
    "Peach___Bacterial_spot": "peach__bacterial_spot", "Peach___healthy": "peach__healthy",
    "Pepper,_bell___Bacterial_spot": "bell_pepper__bacterial_spot",
    "Pepper,_bell___healthy": "bell_pepper__healthy",
    "Potato___Early_blight": "potato__early_blight", "Potato___Late_blight": "potato__late_blight",
    "Potato___healthy": "potato__healthy",
    "Raspberry___healthy": "raspberry__healthy", "Soybean___healthy": "soybean__healthy",
    "Squash___Powdery_mildew": "squash__powdery_mildew",
    "Strawberry___Leaf_scorch": "strawberry__leaf_scorch", "Strawberry___healthy": "strawberry__healthy",
    "Tomato___Bacterial_spot": "tomato__bacterial_spot", "Tomato___Early_blight": "tomato__early_blight",
    "Tomato___Late_blight": "tomato__late_blight", "Tomato___Leaf_Mold": "tomato__leaf_mold",
    "Tomato___Septoria_leaf_spot": "tomato__septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite": "tomato__spider_mites",
    "Tomato___Target_Spot": "tomato__target_spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "tomato__yellow_leaf_curl_virus",
    "Tomato___Tomato_mosaic_virus": "tomato__mosaic_virus", "Tomato___healthy": "tomato__healthy",
}


def check():
    cov = defaultdict(dict)
    for name, mp, base in [("plantdoc", PLANTDOC, ROOT / "plantdoc_clean" / "train"),
                           ("plantwild", PLANTWILD, ROOT / "raw" / "plantwild" / "extracted" / "plantwild" / "images")]:
        if not base.exists():
            print(f"[skip] {name}: {base} not found"); continue
        folders = {p.name: sum(1 for _ in p.iterdir()) for p in base.iterdir() if p.is_dir()}
        unknown = [f for f in folders if f not in mp]
        missing = [k for k in mp if k not in folders]
        if name == "plantdoc":
            unknown = []  # all PlantDoc folders must be in the map
            unknown = [f for f in folders if f not in mp]
        print(f"{name}: {len(folders)} folders, {len(unknown)} unmapped"
              + (" (other crops, expected for plantwild)" if name == "plantwild" else ""))
        if missing:
            print(f"  map keys with no folder (typo?): {missing}")
        if name == "plantdoc" and unknown:
            print(f"  UNMAPPED: {unknown}")
        for f, n in folders.items():
            if mp.get(f):
                cov[mp[f]][name] = n
    for k, v in PLANTVILLAGE.items():
        if v:
            cov[v]["plantvillage"] = "yes"
    print(f"\n{len(cov)} canonical classes. Classes seen in >=2 datasets:")
    both = {k: v for k, v in cov.items() if len(v) >= 2}
    for k in sorted(both):
        print(f"  {k:42s} {dict(both[k])}")
    single = sorted(k for k in cov if k not in both)
    print(f"\nSingle-dataset classes ({len(single)}): {single}")


if __name__ == "__main__":
    check()
