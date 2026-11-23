def sub(s, a, b):
    assert a in s, a[:80]
    return s.replace(a, b, 1)

# ---- Flutter models: supported excludes unnamed ----
p = 'mobile_app/lib/models.dart'
s = open(p, encoding='utf-8').read()
s = sub(s, "Iterable<Info> get supported => _m.values.where((i) => i.kind != 'unknown');",
        "Iterable<Info> get supported => _m.values.where((i) => i.kind != 'unknown' && i.kind != 'unnamed_disease');")
open(p, 'w', encoding='utf-8').write(s)

# ---- Flutter result screen ----
p = 'mobile_app/lib/screens/result_screen.dart'
s = open(p, encoding='utf-8').read()
s = sub(s, "enum _Mode { unknown, healthy, disease }", "enum _Mode { unknown, healthy, disease, unnamed }")
s = sub(s, "final mode = info.kind == 'unknown' ? _Mode.unknown : (info.kind == 'healthy' ? _Mode.healthy : _Mode.disease);",
        "final mode = info.kind == 'unknown'\n        ? _Mode.unknown\n        : (info.kind == 'healthy' ? _Mode.healthy : (info.kind == 'unnamed_disease' ? _Mode.unnamed : _Mode.disease));")
s = sub(s, "      case _Mode.disease:\n        base = sure",
        "      case _Mode.unnamed:\n        base = Colors.deepOrange;\n        icon = Icons.report_problem_outlined;\n        headline = info.title;\n        sub = info.summary;\n        break;\n      case _Mode.disease:\n        base = sure")
s = sub(s, "          ] else if (mode == _Mode.healthy) ...[",
        "          ] else if (mode == _Mode.unnamed) ...[\n            _card(icon: Icons.healing_outlined, title: _t('what_to_do'), accent: Colors.green.shade700, child: _bullets(info.actions)),\n          ] else if (mode == _Mode.healthy) ...[")
open(p, 'w', encoding='utf-8').write(s)

# ---- web page ----
p = 'app/index.html'
s = open(p, encoding='utf-8').read()
s = sub(s, "  if(kind==='unknown'){col='#607d8b';icon='❓';head=T('not_sure_head');sub=T('not_sure_sub')}",
        "  if(kind==='unknown'){col='#607d8b';icon='❓';head=T('not_sure_head');sub=T('not_sure_sub')}\n  else if(kind==='unnamed_disease'){col='#e65100';icon='🔍';head=t.title;sub=d.summary||''}")
s = sub(s, "  }else if(kind==='healthy')h+=card('🌱'", "  }else if(kind==='unnamed_disease')h+=card('🩹',esc(T('what_to_do')),list(d.actions));\n  else if(kind==='healthy')h+=card('🌱'")
open(p, 'w', encoding='utf-8').write(s)

# ---- server ----
p = 'app/server.py'
s = open(p, encoding='utf-8').read()
s = sub(s, '    if first["kind"] == "unknown":\n        status = "unrecognised"', '    if first["kind"] == "unknown":\n        status = "unrecognised"\n    elif first["kind"] == "unnamed_disease":\n        status = "unnamed"')
s = sub(s, 'if c != "unknown_plant"]', 'if c not in ("unknown_plant", "diseased_unnamed")]')
open(p, 'w', encoding='utf-8').write(s)
print("patched")
