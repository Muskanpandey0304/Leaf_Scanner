"""Label mapping for the extra datasets added in run 4 (PlantSeg, banana sets, coffee sets, wheat healthy).

Canonical class = '<crop>__<condition>', same scheme as label_map.py. None = deliberately excluded.
Fruit / ear / berry diseases are excluded on purpose: the app is for LEAVES, and fruit photos would teach the
model to expect fruit.
"""
import re

GENERIC = "diseased_unnamed"  # tiny classes are pooled into this one: 'looks diseased, cannot name it'

EXCLUDE = {  # (plant, disease) PlantSeg pairs that are fruit/ear/berry problems, not leaf problems
    ("Banana", "banana cigar end rot"),
    ("Bell pepper", "bell pepper blossom end rot"),
    ("Blueberry", "blueberry mummy berry"),
    ("Coffee", "coffee berry blotch"),
    ("Eggplant", "eggplant phomopsis fruit rot"),
    ("Peach", "peach brown rot"),
    ("Peach", "peach scab"),
    ("Plum", "plum brown rot"),
    ("Raspberry", "raspberry gray mold"),
    ("Wheat", "wheat head scab"),
    ("Wheat", "wheat loose smut"),
}

# PlantSeg (plant, disease) -> canonical label, where the automatic name would not match our existing ids
ALIAS = {
    ("Apple", "apple rust"): "apple__rust",
    ("Banana", "banana black leaf streak"): "banana__sigatoka",
    ("Cherry", "cherry leaf spot"): "cherry__leaf_spot",
    ("Citrus", "citrus canker"): "citrus__canker",
    ("Citrus", "citrus greening disease"): "citrus__greening",
    ("Corn", "corn rust"): "corn__common_rust",
    ("Corn", "corn smut"): "corn__smut",
    ("Coffee", "coffee brown eye spot"): "coffee__brown_eye_spot",
    ("Grape", "grape leaf spot"): "grape__leaf_blight",
    ("Tomato", "tomato bacterial leaf spot"): "tomato__bacterial_spot",
    ("Peach", "peach bacterial spot"): "peach__bacterial_spot",
    ("Wheat", "wheat bacterial leaf streak (black chaff)"): "wheat__bacterial_leaf_streak",
    ("Soybean", "soybean frog eye leaf spot"): "soybean__frogeye_leaf_spot",
    ("Soybean", "soybean mosaic"): "soybean__mosaic_virus",
    ("Grape", "grape grapevine leafroll disease"): "grape__leafroll_disease",
    ("Bell pepper", "bell pepper frogeye leaf spot"): "bell_pepper__frogeye_leaf_spot",
    ("Tobacco", "tobacco frogeye leaf spot"): "tobacco__frogeye_leaf_spot",
}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def plantseg_label(plant, disease):
    """-> canonical label, or None if excluded."""
    if (plant, disease) in EXCLUDE:
        return None
    if (plant, disease) in ALIAS:
        return ALIAS[(plant, disease)]
    p = slug(plant)
    d = slug(disease)
    if d.startswith(p + "_"):
        d = d[len(p) + 1:]
    return f"{p}__{d}"


# ---- banana sets -------------------------------------------------------------------------------
# Mendeley 79w2n6b4kf "Banana Disease Recognition Dataset" (original images, folder names)
BANANA_7 = {
    "Banana Black Sigatoka Disease": "banana__sigatoka",
    "Banana Yellow Sigatoka Disease": "banana__sigatoka",
    "Banana Healthy Leaf": "banana__healthy",
    "Banana Panama Disease": "banana__panama_disease",
    "Banana Bract Mosaic Virus Disease": "banana__bract_mosaic_virus",
    "Banana Moko Disease": "banana__moko_disease",
    "Banana Insect Pest Disease": None,  # not a pathogen; skip
}
# BananaLSD folders (peer layout <folder_id[:8]>__<count>)
BANANALSD = {
    "2f782abe": "banana__sigatoka",
    "87d14638": "banana__pestalotiopsis_leaf_spot",
    "74dcf511": "banana__cordana_leaf_spot",
    "336f946e": "banana__healthy",
}

# ---- coffee ------------------------------------------------------------------------------------
# BRACOL dataset.csv columns: id,predominant_stress,miner,rust,phoma,cercospora,severity
BRACOL_STRESS = {0: "coffee__healthy", 1: "coffee__leaf_miner", 2: "coffee__leaf_rust",
                 3: "coffee__phoma_leaf_spot", 4: "coffee__brown_eye_spot"}

# Wheat healthy leaves (Mendeley 5gc7hwydwg, Bangladesh field photos)
WHEAT_HEALTHY = "wheat__healthy"
