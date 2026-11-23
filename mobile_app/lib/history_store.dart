import 'dart:convert';
import 'dart:io';

import 'package:path_provider/path_provider.dart';

import 'models.dart';

/// Persists scans (photo copies + a JSON index) in the app's private documents folder.
class HistoryStore {
  late final Directory _dir;
  late final File _index;
  final List<ScanRecord> items = [];

  static Future<HistoryStore> open() async {
    final s = HistoryStore();
    final docs = await getApplicationDocumentsDirectory();
    s._dir = Directory('${docs.path}/scans');
    await s._dir.create(recursive: true);
    s._index = File('${s._dir.path}/history.json');
    if (await s._index.exists()) {
      try {
        final list = jsonDecode(await s._index.readAsString()) as List;
        s.items.addAll(list.map((e) => ScanRecord.fromJson(e as Map<String, dynamic>)));
      } catch (_) {
        // corrupt index: start fresh rather than crash
      }
    }
    return s;
  }

  Future<ScanRecord> add(String sourcePath, List<Candidate> top) async {
    final id = DateTime.now().millisecondsSinceEpoch.toString();
    final dest = '${_dir.path}/$id.jpg';
    await File(sourcePath).copy(dest);
    final rec = ScanRecord(id: id, imagePath: dest, time: DateTime.now(), top: top);
    items.insert(0, rec);
    await _save();
    return rec;
  }

  Future<void> update(ScanRecord r) => _save();

  Future<void> delete(ScanRecord r) async {
    items.removeWhere((e) => e.id == r.id);
    try {
      await File(r.imagePath).delete();
    } catch (_) {}
    await _save();
  }

  Future<void> _save() => _index.writeAsString(jsonEncode(items.map((e) => e.toJson()).toList()));
}
