import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:leaf_scanner/preprocess.dart';

void main() {
  test('softmax is a probability distribution and respects temperature', () {
    final p = calibratedSoftmax([2.0, 1.0, 0.1], 1.0);
    expect(p.reduce((a, b) => a + b), closeTo(1.0, 1e-9));
    expect(p[0], greaterThan(p[1]));
    final sharper = calibratedSoftmax([2.0, 1.0, 0.1], 0.5);
    expect(sharper[0], greaterThan(p[0]));
  });

  test('topK returns the 3 highest in order', () {
    final r = topK([0.1, 0.5, 0.05, 0.3, 0.05], ['a', 'b', 'c', 'd', 'e']);
    expect(r.map((c) => c.id).toList(), ['b', 'd', 'a']);
  });

  // Writes the model input for each listed image so Python can feed it to the ONNX model.
  test('preprocess fixtures (parity with Python pipeline)', () {
    final list = File('test/fixtures/list.txt');
    if (!list.existsSync()) {
      markTestSkipped('no fixtures');
      return;
    }
    final paths = list.readAsLinesSync().where((l) => l.trim().isNotEmpty).toList();
    for (var i = 0; i < paths.length; i++) {
      final out = preprocessFile(paths[i]);
      expect(out.length, 2);
      expect(out[0].length, 3 * kSize * kSize);
      final bytes = Uint8List.view(out[0].buffer);
      File('test/fixtures/out_$i.bin').writeAsBytesSync(bytes);
    }
  });
}
