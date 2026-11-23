import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:onnxruntime/onnxruntime.dart';

import 'models.dart';
import 'preprocess.dart';

class Classifier {
  final OrtSession _session;
  final List<String> classes;
  final double temperature;
  Classifier._(this._session, this.classes, this.temperature);

  static Future<Classifier> load() async {
    OrtEnv.instance.init();
    final opts = OrtSessionOptions()..setIntraOpNumThreads(2);
    final raw = await rootBundle.load('assets/model.onnx');
    final session = OrtSession.fromBuffer(raw.buffer.asUint8List(), opts);
    final classes = (jsonDecode(await rootBundle.loadString('assets/classes.json')) as List).cast<String>();
    final cfg = jsonDecode(await rootBundle.loadString('assets/config.json')) as Map<String, dynamic>;
    return Classifier._(session, classes, (cfg['temperature'] as num).toDouble());
  }

  /// Returns the top 3 candidates for the photo at [path].
  Future<List<Candidate>> classify(String path, {Set<String>? allowed}) async {
    final inputs = await compute(preprocessFile, path);
    final sum = List<double>.filled(classes.length, 0);
    for (final data in inputs) {
      final tensor = OrtValueTensor.createTensorWithDataList([data], [1, 3, kSize, kSize]);
      final runOptions = OrtRunOptions();
      final outputs = await _session.runAsync(runOptions, {'input': tensor});
      tensor.release();
      runOptions.release();
      if (outputs == null || outputs.isEmpty || outputs[0] == null) {
        throw Exception('The model returned no output.');
      }
      final row = ((outputs[0]!.value as List)[0] as List).map((e) => (e as num).toDouble()).toList();
      for (var i = 0; i < sum.length; i++) {
        sum[i] += row[i] / inputs.length;
      }
      for (final o in outputs) {
        o?.release();
      }
    }
    if (allowed != null) {
      // Restrict to the chosen plant (plus the 'unknown' class, so a leaf that
      // does not match the chosen plant still gets the 'not sure' result).
      for (var i = 0; i < sum.length; i++) {
        if (!allowed.contains(classes[i])) sum[i] = -1e9;
      }
    }
    return topK(calibratedSoftmax(sum, temperature), classes);
  }
}
