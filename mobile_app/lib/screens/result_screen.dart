import 'dart:io';

import 'package:flutter/material.dart';

import '../app_state.dart';
import '../models.dart';

enum _Mode { unknown, healthy, disease, unnamed }

class ResultScreen extends StatefulWidget {
  final AppState state;
  final ScanRecord record;
  const ResultScreen({super.key, required this.state, required this.record});

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  Knowledge get kb => widget.state.kb;
  ScanRecord get rec => widget.record;

  Future<void> _setFeedback(String v) async {
    setState(() {
      rec.feedback = v;
      if (v == 'yes') rec.trueLabel = null;
    });
    await widget.state.history.update(rec);
  }

  Future<void> _saveTrueLabel(String? v) async {
    setState(() => rec.trueLabel = v);
    await widget.state.history.update(rec);
  }

  String _bandLabel(String band) => widget.state.ui.band(band);
  String _t(String k, [Map<String, String> a = const {}]) => widget.state.t(k, a);

  Widget _card({required IconData icon, required String title, required Widget child, Color? accent}) {
    final cs = Theme.of(context).colorScheme;
    return Card(
      elevation: 0,
      margin: const EdgeInsets.only(bottom: 12),
      color: cs.surfaceContainerLow,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Icon(icon, size: 20, color: accent ?? cs.primary),
            const SizedBox(width: 8),
            Text(title, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700)),
          ]),
          const SizedBox(height: 10),
          child,
        ]),
      ),
    );
  }

  Widget _bullets(List<String> items) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: items
            .map((s) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    const Padding(padding: EdgeInsets.only(top: 7, right: 10), child: Icon(Icons.circle, size: 6)),
                    Expanded(child: Text(s, style: const TextStyle(height: 1.35))),
                  ]),
                ))
            .toList(),
      );

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final c = rec.top.first;
    final info = kb.of(c.id);
    final mode = info.kind == 'unknown'
        ? _Mode.unknown
        : (info.kind == 'healthy' ? _Mode.healthy : (info.kind == 'unnamed_disease' ? _Mode.unnamed : _Mode.disease));
    final sure = c.band == 'high';

    late final Color base;
    late final IconData icon;
    late final String headline;
    late final String sub;
    switch (mode) {
      case _Mode.unknown:
        base = Colors.blueGrey;
        icon = Icons.help_outline_rounded;
        headline = _t('not_sure_head');
        sub = _t('not_sure_sub');
        break;
      case _Mode.healthy:
        base = Colors.green;
        icon = Icons.check_circle_rounded;
        headline = kb.cropHasDisease(info.crop) ? _t('healthy_head') : _t('healthy_nocheck_head');
        final cn = info.cropName.toLowerCase();
        sub = !kb.cropHasDisease(info.crop)
            ? _t('healthy_nocheck_sub', {'c': cn})
            : (sure ? _t('healthy_sub_sure', {'c': cn}) : _t('healthy_unsure'));
        break;
      case _Mode.unnamed:
        base = Colors.deepOrange;
        icon = Icons.report_problem_outlined;
        headline = info.title;
        sub = info.summary;
        break;
      case _Mode.disease:
        base = sure ? Colors.deepOrange : Colors.orange;
        icon = Icons.warning_amber_rounded;
        headline = _t(sure ? 'likely' : (c.band == 'medium' ? 'possibly' : 'uncertain'), {'t': info.title});
        sub = info.crop.isEmpty ? '' : _t('plant_n', {'p': info.cropName});
        break;
    }
    final dark = Theme.of(context).brightness == Brightness.dark;
    final bannerBg = base.withAlpha(dark ? 55 : 35);
    final lookalikes = info.lookalikes.map((id) => kb.of(id).title).toList();
    final choices = kb.supported.toList()..sort((a, b) => a.title.compareTo(b.title));

    return Scaffold(
      appBar: AppBar(title: Text(_t('result')), centerTitle: true),
      body: SafeArea(
        child: ListView(padding: const EdgeInsets.fromLTRB(16, 4, 16, 24), children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(22),
            child: Image.file(File(rec.imagePath), height: 250, width: double.infinity, fit: BoxFit.cover),
          ),
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(color: bannerBg, borderRadius: BorderRadius.circular(22), border: Border.all(color: base.withAlpha(120))),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Icon(icon, color: base, size: 34),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(headline,
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800, height: 1.2)),
                ),
              ]),
              if (sub.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(sub, style: Theme.of(context).textTheme.bodyMedium),
              ],
              if (mode != _Mode.unknown) ...[
                const SizedBox(height: 14),
                Row(children: [
                  Text(_t('conf', {'b': _bandLabel(c.band), 'p': '${(c.confidence * 100).round()}'}),
                      style: const TextStyle(fontWeight: FontWeight.w600)),
                ]),
                const SizedBox(height: 6),
                ClipRRect(
                  borderRadius: BorderRadius.circular(6),
                  child: LinearProgressIndicator(value: c.confidence, minHeight: 9, color: base, backgroundColor: base.withAlpha(40)),
                ),
              ],
            ]),
          ),
          if (mode != _Mode.unknown && !sure)
            Padding(
              padding: const EdgeInsets.only(top: 10),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Icon(Icons.info_outline, size: 18, color: Colors.orange.shade800),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(_t('not_fully_sure'),
                      style: TextStyle(color: Colors.orange.shade800)),
                ),
              ]),
            ),
          if (mode != _Mode.unknown && info.tier != 'A')
            Padding(
              padding: const EdgeInsets.only(top: 10),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Icon(Icons.science_outlined, size: 18, color: Colors.orange.shade800),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                      info.tier == 'C' ? _t('tier_c') : _t('tier_b'),
                      style: TextStyle(color: Colors.orange.shade800)),
                ),
              ]),
            ),
          const SizedBox(height: 16),
          if (mode == _Mode.disease) ...[
            if (info.signs.isNotEmpty) _card(icon: Icons.visibility_outlined, title: _t('looks_like'), child: _bullets(info.signs)),
            if (info.actions.isNotEmpty) _card(icon: Icons.healing_outlined, title: _t('what_to_do'), accent: Colors.green.shade700, child: _bullets(info.actions)),
            if (info.prevention.isNotEmpty) _card(icon: Icons.shield_outlined, title: _t('prevention'), child: _bullets(info.prevention)),
            if (info.cause.isNotEmpty) _card(icon: Icons.biotech_outlined, title: _t('cause'), child: Text(info.cause, style: const TextStyle(height: 1.35))),
            if (lookalikes.isNotEmpty)
              _card(icon: Icons.compare_arrows_rounded, title: _t('confused'), child: Text(lookalikes.join(', '))),
            Padding(
              padding: const EdgeInsets.only(bottom: 12, left: 4, right: 4),
              child: Text(_t('guidance'),
                  style: TextStyle(color: cs.outline, fontSize: 12)),
            ),
          ] else if (mode == _Mode.unnamed) ...[
            _card(icon: Icons.healing_outlined, title: _t('what_to_do'), accent: Colors.green.shade700, child: _bullets(info.actions)),
          ] else if (mode == _Mode.healthy) ...[
            _card(icon: Icons.spa_outlined, title: _t('keep_healthy'), accent: Colors.green.shade700, child: _bullets(info.actions)),
          ] else ...[
            _card(icon: Icons.photo_camera_outlined, title: _t('better_scan'), child: _bullets(info.actions)),
          ],
          _card(
            icon: Icons.rate_review_outlined,
            title: _t('was_right'),
            child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              Row(children: [
                Expanded(
                  child: FilledButton.tonalIcon(
                    onPressed: () => _setFeedback('yes'),
                    icon: Icon(rec.feedback == 'yes' ? Icons.check_circle : Icons.thumb_up_alt_outlined),
                    label: Text(_t('yes')),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: FilledButton.tonalIcon(
                    onPressed: () => _setFeedback('no'),
                    icon: Icon(rec.feedback == 'no' ? Icons.cancel : Icons.thumb_down_alt_outlined),
                    label: Text(_t('no')),
                  ),
                ),
              ]),
              if (rec.feedback == 'no') ...[
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: rec.trueLabel,
                  isExpanded: true,
                  decoration: InputDecoration(labelText: _t('really_what'), border: OutlineInputBorder(borderRadius: BorderRadius.circular(14))),
                  items: [
                    DropdownMenuItem(value: 'other', child: Text(_t('other'))),
                    for (final i in choices) DropdownMenuItem(value: i.id, child: Text(i.title, overflow: TextOverflow.ellipsis)),
                  ],
                  onChanged: _saveTrueLabel,
                ),
              ],
              if (rec.feedback != null)
                Padding(padding: const EdgeInsets.only(top: 8), child: Text(_t('saved'), style: TextStyle(color: cs.outline))),
            ]),
          ),
        ]),
      ),
    );
  }
}
