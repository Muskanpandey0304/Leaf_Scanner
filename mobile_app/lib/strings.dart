import 'dart:convert';

import 'package:flutter/services.dart' show rootBundle;

/// UI text in English / Hindi / Marathi (assets/ui.json). Missing keys fall back to English.
class Strings {
  final Map<String, dynamic> _m;
  String lang;
  Strings(this._m, this.lang);

  static const languages = {'en': 'English', 'hi': 'हिन्दी', 'mr': 'मराठी'};

  static Future<Strings> load(String lang) async =>
      Strings(jsonDecode(await rootBundle.loadString('assets/ui.json')) as Map<String, dynamic>, lang);

  String t(String key, [Map<String, String> args = const {}]) {
    final e = _m[key] as Map<String, dynamic>?;
    var s = (e?[lang] ?? e?['en'] ?? key) as String;
    args.forEach((k, v) => s = s.replaceAll('{$k}', v));
    return s;
  }

  String band(String b) => t('band_$b');
}
