def sub(s, a, b):
    assert a in s, a[:70]
    return s.replace(a, b, 1)


p = "README.md"
s = open(p, encoding="utf-8").read()

s = sub(s, "The app covers **33 plants and 93 conditions** (diseases and healthy leaves).",
        "The app covers **34 plants and 126 conditions** (95 diseases and 31 healthy-leaf classes).")
s = sub(s, "  - Leaves from plants the app does not know get *\"Not sure what type of leaf this is\"* instead of a made-up answer.\n  - For plants where the app only knows the healthy leaf (for example soybean), it says *\"Looks healthy (disease not checked)\"*.",
        "  - Leaves from plants the app does not know get *\"Not sure what type of leaf this is\"* instead of a made-up answer.\n  - A leaf that clearly looks diseased but matches no disease the app can name gets *\"Looks diseased, disease not identified\"* with advice to show it to an agriculture officer.\n  - For plants where the app only knows the healthy leaf (for example raspberry), it says *\"Looks healthy (disease not checked)\"*.")
s = sub(s, "  - Each condition has a reliability tier (see [Reliability tiers](#reliability-tiers)). Weaker conditions show a warning.",
        "  - Each condition has a reliability tier set from its measured test accuracy (see [Reliability tiers](#reliability-tiers)). Conditions that tested weak show a warning.")

a = s.index("| Test set | Photos | Accuracy |")
b = s.index("### Reliability tiers")
s = s[:a] + """| Test set | Photos | Accuracy |
|---|---|---|
| PlantDoc test split (real field photos) | 234 | **61.5%** (63.2% with the flip-averaging the app uses) |
| PlantWild held-out slice (web photos, noisy labels) | 4,957 | **78.6%** |

The previous version (33 plants) scored 65.0% on PlantDoc and 76.7% on PlantWild. On the 234 field photos the difference is 3 photos, which is within noise, while the model now covers about 30 more conditions.

Accuracy is much higher when the model is confident:

| Shown confidence | Share of PlantDoc photos | Accuracy on those | Share of PlantWild photos | Accuracy on those |
|---|---|---|---|---|
| ≥ 80% (High) | 48% | 84% | 68% | 93% |
| ≥ 90% | 34% | 88% | 58% | 96% |

That is why the app always shows the confidence level and asks for a retake when it is low.

Some web photos in the training data also appear in public image collections, so a photo you find online may be one the model has already seen. Test on your own photos of real leaves to see honest results.

""" + s[b:]

a = s.index("| Tier | Meaning | Conditions |")
b = s.index("The full list of plants and conditions")
s = s[:a] + """Each condition is rated from how it did on held-out test photos:

| Tier | Meaning | Conditions |
|---|---|---|
| A | Tested accurately (at least 15 test photos and a 95% lower bound of 70% or more), or trained on real photos from two datasets and not measured weak | 36 |
| B | Weak or unproven in tests: few test photos, or accuracy under 70%. The app shows a "lower reliability" note | 87 |
| C | Studio photos only, never checked on field photos | 3 |

Several common conditions, such as tomato, apple, corn and potato diseases, are in tier B because they look alike and scored under 70% in tests, even though they have plenty of training photos.

""" + s[b:]

s = sub(s, "- Some diseases are missing from the training data, for example carrot leaf blight, black rot on cabbage and cauliflower, and soybean diseases. A leaf with one of these may come out as the closest condition the model knows, sometimes \"healthy\".",
        "- Many diseases are still missing, for example raspberry diseases, carrot Cercospora leaf blight, cauliflower black rot and most diseases of tomato lookalikes. Many new classes have under 50 photos and only a handful of test photos, so their accuracy is uncertain. A leaf with a disease the model does not know may come out as the closest condition it knows, as \"diseased, not identified\", or sometimes as \"healthy\".\n- Fruit and ear diseases are not covered; the app is for leaves.")
s = sub(s, "- **Unknown-class images** come from",
        """- **PlantSeg**, Wei et al., 2025. [zenodo.org/records/17719108](https://zenodo.org/records/17719108), [github.com/tqwei05/PlantSeg](https://github.com/tqwei05/PlantSeg). CC BY-NC 4.0.
- **Banana:** [BananaLSD](https://data.mendeley.com/datasets/9tb7k297ff), [Banana Disease Recognition Dataset](https://data.mendeley.com/datasets/79w2n6b4kf), [Banana and Banana Leaf Dataset](https://data.mendeley.com/datasets/5nfjzntwd8). Mendeley Data, CC BY 4.0.
- **Coffee:** [BRACOL](https://data.mendeley.com/datasets/yy2k5y8mxg) (Brazilian Arabica coffee leaves) and [RoCoLe](https://data.mendeley.com/datasets/c5yvn32dzg) (Robusta coffee leaves, Parraga-Alava et al.). Mendeley Data, CC BY 4.0.
- **Wheat (healthy leaves):** [Disease Dataset of Wheat](https://data.mendeley.com/datasets/5gc7hwydwg). Mendeley Data, CC BY 4.0.
- **Unknown-class images** come from""")
s = sub(s, "because one of the training datasets (PlantWild) has a non-commercial license.",
        "because some of the training datasets (PlantWild, PlantSeg) have non-commercial licenses.")
s = sub(s, "The trained model weights (`models_run3/`, `mobile_app/assets/model.onnx`) were trained on data that includes PlantWild (CC BY-NC-ND 4.0), so the model is for non-commercial use only.",
        "The trained model weights (`models_run4/`, `mobile_app/assets/model.onnx`) were trained on data that includes PlantWild (CC BY-NC-ND 4.0) and PlantSeg (CC BY-NC 4.0), so the model is for non-commercial use only.")
s = s.replace("models_run3/         Final model weights, classes and test report", "models_run4/         Final model weights, classes and test report")
s = s.replace("python scripts/build_dataset.py                       # builds data/processed2 from the raw datasets", "python scripts/build_dataset.py                       # builds data/processed2 from the first datasets\npython scripts/build_dataset3.py                      # adds PlantSeg, banana, coffee and wheat data -> data/processed3")
s = s.replace("python scripts/train.py --data data/processed2 --out models_run3 --epochs 16 --samples 40000 --field_weight 8 --balance 0.5", "python scripts/train.py --data data/processed3 --out models_run4 --epochs 18 --samples 40000 --field_weight 8 --balance 0.5\npython scripts/assign_tiers.py models_run4 data/processed3   # reliability tiers from measured accuracy")
s = s.replace("python scripts/export_onnx.py models_run3 data/processed2", "python scripts/export_onnx.py models_run4 data/processed3\npython scripts/merge_kb.py")
s = s.replace("On a GTX 1650, training takes about 2.5–3 hours.", "On a GTX 1650, training takes about 3 hours.")
open(p, "w", encoding="utf-8").write(s)
print("README patched")
