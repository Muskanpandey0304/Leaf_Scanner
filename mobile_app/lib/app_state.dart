import 'dart:io';

import 'package:flutter/services.dart' show rootBundle;
import 'package:path_provider/path_provider.dart';

import 'classifier.dart';
import 'history_store.dart';
import 'models.dart';
import 'strings.dart';

/// Everything the screens share: the model, knowledge base, scan history and language.
class AppState {
  final Classifier classifier;
  final Map<String, Knowledge> _kbs;
  final HistoryStore history;
  final Strings ui;
  AppState(this.classifier, this._kbs, this.history, this.ui);

  /// Plant chosen with the plant picker; null means auto-detect.
  String? selectedCrop;

  String get lang => ui.lang;
  Knowledge get kb => _kbs[ui.lang] ?? _kbs['en']!;
  String t(String key, [Map<String, String> args = const {}]) => ui.t(key, args);

  Future<void> setLang(String l) async {
    ui.lang = l;
    try {
      final dir = await getApplicationDocumentsDirectory();
      await File('${dir.path}/lang.txt').writeAsString(l);
    } catch (_) {}
  }

  static Future<AppState> load() async {
    final kbs = <String, Knowledge>{
      'en': Knowledge.parse(await rootBundle.loadString('assets/knowledge.json')),
      'hi': Knowledge.parse(await rootBundle.loadString('assets/knowledge_hi.json')),
      'mr': Knowledge.parse(await rootBundle.loadString('assets/knowledge_mr.json')),
    };
    var lang = 'en';
    try {
      final dir = await getApplicationDocumentsDirectory();
      final f = File('${dir.path}/lang.txt');
      if (await f.exists()) {
        final v = (await f.readAsString()).trim();
        if (Strings.languages.containsKey(v)) lang = v;
      }
    } catch (_) {}
    final classifier = await Classifier.load();
    final history = await HistoryStore.open();
    return AppState(classifier, kbs, history, await Strings.load(lang));
  }
}
