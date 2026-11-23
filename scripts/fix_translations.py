"""Corrections found in the Hindi/Marathi review. Edits i18n/{hi,mr}.txt and the split files in place."""
import re
from pathlib import Path

R = Path(__file__).resolve().parent.parent / "i18n"

HI = {
    187: "फलों पर कठोर भूरी सड़न",
    236: "तना काटने पर अंदर भूरा या लाल-भूरा रंग",
    238: "रोगी पौधे उखाड़कर नष्ट करें; उस जगह की मिट्टी या पुत्तियाँ (सकर) कहीं और न ले जाएँ।",
    362: "वायुरोधक पेड़ (विंडब्रेक)",
    443: "पर्णच्छद झुलसा / शीथ ब्लाइट (अदरक)",
    495: "पर्णच्छद झुलसा / शीथ ब्लाइट (धान)",
    589: "लाल मकड़ी / माइट (टमाटर)",
}
MR = {
    4: "सफरचंदावरील खपली रोग (स्कॅब)",
    13: "खपली रोगास प्रतिकारक वाण निवडा",
    41: "लहान गडद, पाण्याने भिजल्यासारखे ठिपके जे पिवळ्या कडेसह तपकिरी होतात",
    99: "बुरशी (Guignardia bidwellii), उबदार ओलसर हवामान; वाळलेल्या मण्यांवर हिवाळा काढते.",
    132: "मोठे, पाण्याने भिजल्यासारखे गडद डाग, अनेकदा फिकट हिरव्या कडेसह",
    216: "पिवळा पान-वळण (लीफ कर्ल) विषाणू (टोमॅटो)",
    260: "पिवळसर-हिरव्या कडेसह लहान, पाण्याने भिजल्यासारखे ठिपके",
    391: "शिरांनी मर्यादित, पाण्याने भिजल्यासारखे कोनदार ठिपके",
    443: "आवरण करपा / शीथ ब्लाइट (आले)",
    445: "पानांच्या आवरणावर (शीथ) पाण्याने भिजल्यासारखे डाग",
    495: "आवरण करपा / शीथ ब्लाइट (भात)",
    589: "लाल कोळी / माइट्स (टोमॅटो)",
}


def apply(lang, fixes):
    for f in [R / f"{lang}.txt"] + sorted(R.glob(f"{lang}_*.txt")):
        lines = f.read_text(encoding="utf-8").splitlines()
        out = []
        for ln in lines:
            n = int(ln.split("|", 1)[0])
            out.append(f"{n}|{fixes[n]}" if n in fixes else ln)
        f.write_text("\n".join(out) + "\n", encoding="utf-8")


apply("hi", HI)
apply("mr", MR)

# UI strings
p = R / "ui.py"
s = p.read_text(encoding="utf-8")
s = s.replace('"band_high": ["High", "ऊँचा", "जास्त"]', '"band_high": ["High", "अधिक", "जास्त"]')
# Marathi "{c} चे पान" breaks for names like "लिंबूवर्गीय फळे"; rephrase without joining a suffix to the plant name
s = s.replace('"हे निरोगी {c} चे पान दिसते."', '"हे पान निरोगी दिसते (वनस्पती: {c})."')
s = s.replace('"हे निरोगी {c} चे पान दिसते, पण हे अ‍ॅप {c} मधील रोग तपासू शकत नाही. रोग नसल्याची खात्री देता येत नाही."',
              '"हे पान निरोगी दिसते (वनस्पती: {c}), पण हे अ‍ॅप या वनस्पतीवरील रोग तपासू शकत नाही. रोग नसल्याची खात्री देता येत नाही."')
p.write_text(s, encoding="utf-8")
print("fixed", len(HI), "hi +", len(MR), "mr lines + UI strings")
