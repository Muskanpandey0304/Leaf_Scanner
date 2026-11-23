import re


def sub(s, a, b):
    assert a in s, a[:70]
    return s.replace(a, b, 1)


# ---------- home ----------
p = 'mobile_app/lib/screens/home_screen.dart'
s = open(p, encoding='utf-8').read()
s = sub(s, "SnackBar(content: Text('Something went wrong: $e'))", "SnackBar(content: Text(widget.state.t('went_wrong', {'e': '$e'})))")
s = sub(s, """const Padding(
            padding: EdgeInsets.fromLTRB(20, 0, 20, 8),
            child: Text('Which plant is this leaf from?', style:""", """Padding(
            padding: const EdgeInsets.fromLTRB(20, 0, 20, 8),
            child: Text(widget.state.t('which_plant'), style:""")
s = sub(s, """            title: const Text('Auto-detect'),
            subtitle: const Text('Let the app work out the plant'),""", """            title: Text(widget.state.t('auto_detect')),
            subtitle: Text(widget.state.t('auto_sub')),""")
s = sub(s, "title: Text(c),\n              selected", "title: Text(widget.state.kb.cropLabel(c)),\n              selected")
s = sub(s, """                  label: Text(widget.state.selectedCrop == null
                      ? 'Choose plant (optional)'
                      : 'Plant: ${widget.state.selectedCrop}'),""", """                  label: Text(widget.state.selectedCrop == null
                      ? widget.state.t('choose_plant')
                      : widget.state.t('plant_n', {'p': widget.state.kb.cropLabel(widget.state.selectedCrop!)})),""")
s = sub(s, "tooltip: 'Back to auto-detect',", "tooltip: widget.state.t('back_auto'),")
s = sub(s, "final crops = widget.state.kb.supported.map((i) => i.crop).where((c) => c.isNotEmpty).toSet().toList()..sort();", "final crops = widget.state.kb.crops.map((c) => widget.state.kb.cropLabel(c)).toList();")
s = sub(s, "title: const Text('About Leaf Scanner'),", "title: Text(widget.state.t('about_title')),")
s = sub(s, "const Text('Supported plants', style: TextStyle(fontWeight: FontWeight.bold)),", "Text(widget.state.t('supported_plants'), style: const TextStyle(fontWeight: FontWeight.bold)),")
s, n = re.subn(r"const Text\(\n\s*'This app suggests.*?\),\n            const SizedBox\(height: 12\),\n            const Text\('Everything runs on your phone. Photos are never uploaded.'\),",
               "Text(widget.state.t('about_body')),\n            const SizedBox(height: 12),\n            Text(widget.state.t('local_only')),\n            const SizedBox(height: 12),\n            Text(widget.state.t('mt_note'), style: const TextStyle(fontSize: 12)),", s, flags=re.S)
assert n == 1
s = sub(s, "child: const Text('Close'))", "child: Text(widget.state.t('close')))")
s = sub(s, "Text('Check a leaf for disease and get simple advice.',", "Text(widget.state.t('tagline'),")
s = sub(s, "label: const Text('Take a photo', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),", "label: Text(widget.state.t('take_photo'), style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),")
s = sub(s, "label: const Text('Choose from gallery', style: TextStyle(fontSize: 16)),", "label: Text(widget.state.t('gallery'), style: const TextStyle(fontSize: 16)),")
s = sub(s, "const Text('Analysing the leaf...'),", "Text(widget.state.t('analysing')),")
s = sub(s, "Text('For the best result', style:", "Text(widget.state.t('tips_title'), style:")
s = sub(s, "_tip(Icons.crop_free_rounded, 'One leaf, filling the frame'),", "_tip(Icons.crop_free_rounded, widget.state.t('tip1')),")
s = sub(s, "_tip(Icons.wb_sunny_outlined, 'Daylight, sharp and in focus'),", "_tip(Icons.wb_sunny_outlined, widget.state.t('tip2')),")
s = sub(s, "_tip(Icons.block_rounded, 'Not fruit, stems or the whole plant'),", "_tip(Icons.block_rounded, widget.state.t('tip3')),")
s = sub(s, "Text('${widget.state.history.items.length} scans saved on this phone',", "Text(widget.state.t('scans_saved', {'n': '${widget.state.history.items.length}'}),")
s = sub(s, "tooltip: 'History',", "tooltip: widget.state.t('history'),")
s = sub(s, "IconButton(tooltip: 'About',", "IconButton(tooltip: widget.state.t('about'),")
s = sub(s, """            Row(mainAxisAlignment: MainAxisAlignment.end, children: [
""", """            Row(mainAxisAlignment: MainAxisAlignment.end, children: [
              PopupMenuButton<String>(
                tooltip: widget.state.t('language'),
                icon: const Icon(Icons.translate_rounded),
                initialValue: widget.state.lang,
                onSelected: (l) async {
                  await widget.state.setLang(l);
                  if (mounted) setState(() {});
                },
                itemBuilder: (_) => [
                  for (final e in Strings.languages.entries) PopupMenuItem(value: e.key, child: Text(e.value)),
                ],
              ),
""")
s = sub(s, "import '../app_state.dart';", "import '../app_state.dart';\nimport '../strings.dart';")
open(p, 'w', encoding='utf-8').write(s)

# ---------- history ----------
p = 'mobile_app/lib/screens/history_screen.dart'
s = open(p, encoding='utf-8').read()
s = sub(s, "AppBar(title: const Text('Scan history'))", "AppBar(title: Text(state.t('scan_history')))")
s = sub(s, "const Center(child: Text('No scans yet.'))", "Center(child: Text(state.t('no_scans')))")
s = sub(s, "'Not sure what leaf this is'", "state.t('not_sure_short')")
s = sub(s, "${kb.of(top.id).crop}  -", "${kb.of(top.id).cropName}  -")
open(p, 'w', encoding='utf-8').write(s)

# ---------- result ----------
p = 'mobile_app/lib/screens/result_screen.dart'
s = open(p, encoding='utf-8').read()
s = sub(s, "String _bandLabel(String band) => band == 'high' ? 'High' : (band == 'medium' ? 'Medium' : 'Low');", "String _bandLabel(String band) => widget.state.ui.band(band);\n  String _t(String k, [Map<String, String> a = const {}]) => widget.state.t(k, a);")
s = sub(s, "headline = 'Not sure what type of leaf this is';", "headline = _t('not_sure_head');")
s = sub(s, "sub = 'It may be a plant this app does not know, or the photo is unclear.';", "sub = _t('not_sure_sub');")
s, n = re.subn(r"sub = !kb\.cropHasDisease\(info\.crop\)\n.*?'Looks healthy, but the app is not certain.'\);",
               """final cn = info.cropName.toLowerCase();
        sub = !kb.cropHasDisease(info.crop)
            ? _t('healthy_nocheck_sub', {'c': cn})
            : (sure ? _t('healthy_sub_sure', {'c': cn}) : _t('healthy_unsure'));""", s, flags=re.S)
assert n == 1
s = sub(s, "headline = kb.cropHasDisease(info.crop) ? 'No disease detected' : 'Looks healthy (disease not checked)';", "headline = kb.cropHasDisease(info.crop) ? _t('healthy_head') : _t('healthy_nocheck_head');")
s = sub(s, "headline = '${sure ? 'Likely' : (c.band == 'medium' ? 'Possibly' : 'Uncertain, maybe')}: ${info.title}';", "headline = _t(sure ? 'likely' : (c.band == 'medium' ? 'possibly' : 'uncertain'), {'t': info.title});")
s = sub(s, "sub = info.crop.isEmpty ? '' : 'Plant: ${info.crop}';", "sub = info.crop.isEmpty ? '' : _t('plant_n', {'p': info.cropName});")
s = sub(s, "AppBar(title: const Text('Result'),", "AppBar(title: Text(_t('result')),")
s = sub(s, "Text('Confidence: ${_bandLabel(c.band)} (${(c.confidence * 100).round()}%)',", "Text(_t('conf', {'b': _bandLabel(c.band), 'p': '${(c.confidence * 100).round()}'}),")
s = sub(s, "child: Text('Not fully sure. Retake a closer, sharper photo in daylight to confirm.',", "child: Text(_t('not_fully_sure'),")
s, n = re.subn(r"info\.tier == 'C'\n\s*\? 'Weakly tested:.*?'\n\s*: 'Lower reliability:.*?',", "info.tier == 'C' ? _t('tier_c') : _t('tier_b'),", s, flags=re.S)
assert n == 1
s = sub(s, "title: 'What it looks like'", "title: _t('looks_like')")
s = sub(s, "title: 'What to do'", "title: _t('what_to_do')")
s = sub(s, "title: 'Prevention'", "title: _t('prevention')")
s = sub(s, "title: 'Cause'", "title: _t('cause')")
s = sub(s, "title: 'Easily confused with'", "title: _t('confused')")
s = sub(s, "Text('General guidance only. Check local agricultural advice and product labels.',", "Text(_t('guidance'),")
s = sub(s, "title: 'Keeping it healthy'", "title: _t('keep_healthy')")
s = sub(s, "title: 'For a better scan'", "title: _t('better_scan')")
s = sub(s, "title: 'Was this right?'", "title: _t('was_right')")
s = sub(s, "label: const Text('Yes'),", "label: Text(_t('yes')),")
s = sub(s, "label: const Text('No'),", "label: Text(_t('no')),")
s = sub(s, "labelText: 'What is it really? (optional)'", "labelText: _t('really_what')")
s = sub(s, "const DropdownMenuItem(value: 'other', child: Text('Other / not in list')),", "DropdownMenuItem(value: 'other', child: Text(_t('other'))),")
s = sub(s, "Text('Saved on this phone.',", "Text(_t('saved'),")
open(p, 'w', encoding='utf-8').write(s)
print("patched")
