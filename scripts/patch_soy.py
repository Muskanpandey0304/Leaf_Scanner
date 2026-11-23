import json, re
p = "app/knowledge_run4.json"
kb = json.load(open(p, encoding="utf-8"))
kb["soybean__mosaic_virus"] = {"title": "Mosaic virus (soybean)", "crop": "Soybean", "kind": "disease",
  "cause": "Virus spread by aphids and infected seed. No cure.",
  "signs": ["Light and dark green mottling", "Puckered, curled leaves", "Stunted plants and poor pods"],
  "actions": ["Remove and bag infected plants.", "Control aphids.", "Do not save seed from infected plants."],
  "prevention": ["Certified virus-free seed", "Control aphids and weeds"], "lookalikes": ["soybean__downy_mildew"]}
json.dump(kb, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# crops
s = open("i18n/ui.py", encoding="utf-8").read()
if '"Wheat"' not in s:
    s = s.replace('"Zucchini":["ज़ुकीनी","झुकिनी"],', '"Zucchini":["ज़ुकीनी","झुकिनी"],\n"Wheat":["गेहूँ","गहू"],')
open("i18n/ui.py", "w", encoding="utf-8").write(s)
print("ok", '"Wheat"' in s)
