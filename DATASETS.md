# Datasets decision

| Role | Dataset | License | Why |
|---|---|---|---|
| Base (volume) | PlantVillage (38 classes, ~54.3k lab images). Source: https://huggingface.co/datasets/mohanty/PlantVillage (original release; includes leaf_grouping/leaf-map.json so we can split by physical leaf). NOT the Mendeley copy: that one is pre-augmented, which leaks across splits. | CC BY-SA 3.0 | Clean labels, many classes. Lab backgrounds only, so never trust alone. |
| Field #1 | PlantDoc, cropped classification version. https://github.com/pratikkayal/PlantDoc-Dataset | CC BY 4.0 | Real phone/field photos, 13 species. Small (~2.6k), so oversample and augment. |
| Field #2 (SKIPPED by user decision; no official download found, only Roboflow copies) | FieldPlant (5,170 field images, 27 classes). Paper: IEEE Access 2023, doi 10.1109/ACCESS.2023.3263042 | CC BY 4.0 | Photos taken on real plantations, pathologist-annotated. Use the authors' release, not Roboflow copies (class lists differ). |

| Field #3 (train only) | PlantWild, https://huggingface.co/datasets/Voxel51/PlantWild (~18.5k images, 89 classes) | CC BY-NC-ND 4.0 | Largest real-world set. Web-scraped, so labels are noisy: clean them, use for TRAINING ONLY, never for the test set. |

## PlantWild license handling (project is non-commercial portfolio)
- Only needed: a note at the end of the README linking the datasets and stating the project is non-commercial.
- If the project ever goes commercial, retrain without PlantWild.

## Split policy (decided)
- PlantVillage: TRAIN ONLY. Its leaf map covers only 41,111 of 54,305 images, so a clean leaf-level split is impossible for the rest. It never appears in validation or test.
- PlantWild: train + validation + a held-out test slice, after near-duplicate removal (perceptual hash) so web duplicates don't cross splits.
- PlantDoc: official train/test split. Its test split is the main honest test.

## Rules to limit wrong answers
1. Test set = field images only (PlantDoc/FieldPlant held-out). Never report PlantVillage accuracy.
2. Split by source photo/plant, not random, to avoid leakage.
3. Add "not a leaf / unknown" class (non-leaf images, other crops).
4. App abstains below a calibrated confidence threshold ("retake photo"), shows top-3.
5. Advice comes from a curated knowledge base keyed by class, never generated freely.
6. Restrict v1 to crops present in at least two datasets.

## Open TODOs
- Confirm PlantVillage license on Mendeley.
- Map class names across the three datasets to one label schema.
