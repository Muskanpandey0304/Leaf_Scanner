import 'dart:convert';

/// One possible diagnosis from the model.
class Candidate {
  final String id;
  final double confidence;
  const Candidate(this.id, this.confidence);

  String get band => confidence >= 0.8 ? 'high' : (confidence >= 0.5 ? 'medium' : 'low');

  Map<String, dynamic> toJson() => {'id': id, 'c': confidence};
  factory Candidate.fromJson(Map<String, dynamic> j) => Candidate(j['id'] as String, (j['c'] as num).toDouble());
}

/// Knowledge-base entry (assets/knowledge.json).
class Info {
  final String id;
  final Map<String, dynamic> raw;
  Info(this.id, this.raw);

  String get title => (raw['title'] as String?) ?? id;
  String get crop => (raw['crop'] as String?) ?? '';
  /// Plant name in the app language (falls back to English).
  String get cropName => (raw['crop_local'] as String?) ?? crop;
  String get kind => (raw['kind'] as String?) ?? 'disease'; // disease | healthy | unknown
  String get tier => (raw['tier'] as String?) ?? 'A'; // A tested, B single-source, C lab-only
  String get cause => (raw['cause'] as String?) ?? '';
  String get summary => (raw['summary'] as String?) ?? '';
  List<String> _list(String k) => ((raw[k] as List?) ?? const []).cast<String>();
  List<String> get signs => _list('signs');
  List<String> get actions => _list('actions');
  List<String> get prevention => _list('prevention');
  List<String> get lookalikes => _list('lookalikes');
}

class Knowledge {
  final Map<String, Info> _m = {};
  Knowledge(Map<String, dynamic> json) {
    json.forEach((k, v) {
      if (k.startsWith('_')) return;
      _m[k] = Info(k, v as Map<String, dynamic>);
    });
  }
  factory Knowledge.parse(String s) => Knowledge(jsonDecode(s) as Map<String, dynamic>);

  Info of(String id) => _m[id] ?? Info(id, {'title': id, 'kind': 'disease'});
  /// Plant names (e.g. 'Tomato'), sorted.
  List<String> get crops => (supported.map((i) => i.crop).where((c) => c.isNotEmpty).toSet().toList()..sort());

  /// Plant name in the app language for an English plant key.
  String cropLabel(String crop) {
    for (final i in _m.values) {
      if (i.crop == crop) return i.cropName;
    }
    return crop;
  }

  /// Class ids for one plant, plus the 'unknown' class.
  Set<String> idsForCrop(String crop) =>
      _m.values.where((i) => i.crop == crop || i.kind == 'unknown').map((i) => i.id).toSet();

  /// False for plants whose only class is 'healthy' (the app cannot detect disease on them).
  bool cropHasDisease(String crop) => _m.values.any((i) => i.crop == crop && i.kind == 'disease');

  Iterable<Info> get supported => _m.values.where((i) => i.kind != 'unknown' && i.kind != 'unnamed_disease');
}

/// A saved scan.
class ScanRecord {
  final String id;
  final String imagePath;
  final DateTime time;
  final List<Candidate> top;
  String? feedback; // 'yes' | 'no'
  String? trueLabel;

  ScanRecord({required this.id, required this.imagePath, required this.time, required this.top, this.feedback, this.trueLabel});

  Map<String, dynamic> toJson() => {
        'id': id,
        'img': imagePath,
        't': time.toIso8601String(),
        'top': top.map((c) => c.toJson()).toList(),
        'fb': feedback,
        'tl': trueLabel,
      };

  factory ScanRecord.fromJson(Map<String, dynamic> j) => ScanRecord(
        id: j['id'] as String,
        imagePath: j['img'] as String,
        time: DateTime.parse(j['t'] as String),
        top: (j['top'] as List).map((e) => Candidate.fromJson(e as Map<String, dynamic>)).toList(),
        feedback: j['fb'] as String?,
        trueLabel: j['tl'] as String?,
      );
}
