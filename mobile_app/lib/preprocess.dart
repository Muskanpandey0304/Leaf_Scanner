import 'dart:io';
import 'dart:math' as math;
import 'dart:typed_data';

import 'package:image/image.dart' as img;

import 'models.dart';

const int kSize = 224;
const int kResize = 256;
const List<double> kMean = [0.485, 0.456, 0.406];
const List<double> kStd = [0.229, 0.224, 0.225];

/// Loads the photo and builds the model input exactly like training/eval did:
/// resize shorter side to 256, centre-crop 224, normalise. Returns [original, horizontally flipped].
/// Top-level so it can run in a background isolate via compute().
List<Float32List> preprocessFile(String path) {
  final bytes = File(path).readAsBytesSync();
  var image = img.decodeImage(bytes);
  if (image == null) throw Exception('Could not read this image.');
  image = img.bakeOrientation(image);
  return preprocessImage(image);
}

/// Python's round(): half to even (needed so crop offsets match torchvision).
int _pyRound(double v) {
  final f = v.floorToDouble();
  final diff = v - f;
  if (diff < 0.5) return f.toInt();
  if (diff > 0.5) return f.toInt() + 1;
  return (f.toInt() % 2 == 0) ? f.toInt() : f.toInt() + 1;
}

/// Pillow's bilinear resize (separable triangle filter, support scaled when shrinking = antialiased).
/// [src] is tightly packed RGB. Returns packed RGB of size outW x outH.
Uint8List _pilResize(Uint8List src, int inW, int inH, int outW, int outH) {
  Uint8List pass(Uint8List data, int w, int h, int outSize, bool horizontal) {
    final inSize = horizontal ? w : h;
    final scale = inSize / outSize;
    final filterScale = math.max(scale, 1.0);
    final support = filterScale; // bilinear support = 1.0 * filterScale
    final outW2 = horizontal ? outSize : w;
    final outH2 = horizontal ? h : outSize;
    final out = Uint8List(outW2 * outH2 * 3);
    // precompute coefficients per output index
    final starts = List<int>.filled(outSize, 0);
    final coeffs = List<Float64List>.filled(outSize, Float64List(0));
    for (var i = 0; i < outSize; i++) {
      final center = (i + 0.5) * scale;
      var xmin = (center - support + 0.5).toInt();
      if (xmin < 0) xmin = 0;
      var xmax = (center + support + 0.5).toInt();
      if (xmax > inSize) xmax = inSize;
      xmax -= xmin;
      final k = Float64List(xmax);
      var ww = 0.0;
      for (var x = 0; x < xmax; x++) {
        final d = ((x + xmin - center + 0.5) / filterScale).abs();
        final w0 = d < 1.0 ? 1.0 - d : 0.0;
        k[x] = w0;
        ww += w0;
      }
      if (ww != 0) {
        for (var x = 0; x < xmax; x++) {
          k[x] /= ww;
        }
      }
      starts[i] = xmin;
      coeffs[i] = k;
    }
    if (horizontal) {
      for (var y = 0; y < h; y++) {
        for (var ox = 0; ox < outSize; ox++) {
          final k = coeffs[ox];
          final x0 = starts[ox];
          for (var c = 0; c < 3; c++) {
            var acc = 0.0;
            for (var x = 0; x < k.length; x++) {
              acc += data[(y * w + x0 + x) * 3 + c] * k[x];
            }
            out[(y * outSize + ox) * 3 + c] = acc.round().clamp(0, 255);
          }
        }
      }
    } else {
      for (var oy = 0; oy < outSize; oy++) {
        final k = coeffs[oy];
        final y0 = starts[oy];
        for (var x = 0; x < w; x++) {
          for (var c = 0; c < 3; c++) {
            var acc = 0.0;
            for (var j = 0; j < k.length; j++) {
              acc += data[((y0 + j) * w + x) * 3 + c] * k[j];
            }
            out[(oy * w + x) * 3 + c] = acc.round().clamp(0, 255);
          }
        }
      }
    }
    return out;
  }

  var data = src;
  var w = inW, h = inH;
  if (outW != inW) {
    data = pass(data, w, h, outW, true);
    w = outW;
  }
  if (outH != inH) {
    data = pass(data, w, h, outH, false);
    h = outH;
  }
  return data;
}

List<Float32List> preprocessImage(img.Image source) {
  final rgbImage = source.convert(numChannels: 3);
  final w = rgbImage.width, h = rgbImage.height;
  final rgb = rgbImage.getBytes(order: img.ChannelOrder.rgb);
  // torchvision Resize(256): shorter side -> 256, longer side truncated.
  int nw, nh;
  if (w <= h) {
    nw = kResize;
    nh = (kResize * h / w).floor();
  } else {
    nh = kResize;
    nw = (kResize * w / h).floor();
  }
  final resized = (nw == w && nh == h) ? rgb : _pilResize(rgb, w, h, nw, nh);
  final left = _pyRound((nw - kSize) / 2.0);
  final top = _pyRound((nh - kSize) / 2.0);

  const plane = kSize * kSize;
  final normal = Float32List(3 * plane);
  final flipped = Float32List(3 * plane);
  for (var y = 0; y < kSize; y++) {
    for (var x = 0; x < kSize; x++) {
      final o = ((y + top) * nw + (x + left)) * 3;
      for (var c = 0; c < 3; c++) {
        final v = ((resized[o + c] / 255.0) - kMean[c]) / kStd[c];
        normal[c * plane + y * kSize + x] = v;
        flipped[c * plane + y * kSize + (kSize - 1 - x)] = v;
      }
    }
  }
  return [normal, flipped];
}

/// Softmax of logits / temperature.
List<double> calibratedSoftmax(List<double> logits, double temperature) {
  final scaled = logits.map((l) => l / temperature).toList();
  final m = scaled.reduce(math.max);
  final exps = scaled.map((l) => math.exp(l - m)).toList();
  final sum = exps.reduce((a, b) => a + b);
  return exps.map((e) => e / sum).toList();
}

List<Candidate> topK(List<double> probs, List<String> classes, {int k = 3}) {
  final idx = List<int>.generate(probs.length, (i) => i)..sort((a, b) => probs[b].compareTo(probs[a]));
  return idx.take(k).map((i) => Candidate(classes[i], probs[i])).toList();
}

