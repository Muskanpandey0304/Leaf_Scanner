import json, pandas as pd, collections
m = pd.read_csv("data/raw/plantseg_meta/Metadata.csv", encoding="utf-8-sig")
print(len(m), "rows;", m.Plant.nunique(), "plants;", m.Disease.nunique(), "diseases")
print(m.License.value_counts().to_dict())
kb = json.load(open("app/knowledge_all.json", encoding="utf-8"))
ours = collections.defaultdict(list)
for k, v in kb.items():
    if isinstance(v, dict) and v.get("crop"):
        ours[v["crop"].lower()].append(v["title"] if v["kind"] == "disease" else "(healthy)")
g = m.groupby(["Plant", "Disease"]).size().reset_index(name="n")
for plant, d in g.groupby("Plant"):
    mine = ours.get(plant.lower().split(" /")[0], None)
    tag = "NEW PLANT" if mine is None else "ours: " + "; ".join(sorted(x for x in mine if x != "(healthy)")) 
    print(f"\n## {plant} ({d.n.sum()} imgs) [{tag}]")
    print("   " + "; ".join(f"{r.Disease.replace(plant.lower()+' ','')} ({r.n})" for r in d.itertuples()))
